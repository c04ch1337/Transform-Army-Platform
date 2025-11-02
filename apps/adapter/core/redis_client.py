"""
Redis client with connection pooling, pub/sub, and async operations.

This module provides a robust Redis client with:
- Connection pooling for efficient resource usage
- Async operations using redis-py
- Pub/sub support for real-time events
- Health checks and monitoring
- Error handling and reconnection logic
- JSON serialization for complex data types
"""

import json
import asyncio
from typing import Any, Optional, Dict, List, Callable, AsyncGenerator
from datetime import timedelta
import pickle

import redis.asyncio as aioredis
from redis.asyncio import Redis, ConnectionPool
from redis.exceptions import (
    RedisError,
    ConnectionError,
    TimeoutError as RedisTimeoutError,
    ResponseError
)

from .config import settings
from .logging import get_logger
from .exceptions import AdapterException


logger = get_logger(__name__)


class RedisConnectionError(AdapterException):
    """Raised when Redis connection fails."""
    pass


class RedisOperationError(AdapterException):
    """Raised when Redis operation fails."""
    pass


class RedisClient:
    """
    Async Redis client with connection pooling and comprehensive operations.
    
    Features:
    - Connection pooling for efficient resource management
    - Async operations for non-blocking I/O
    - Pub/sub support for real-time messaging
    - Health checks for monitoring
    - Automatic reconnection on failures
    - JSON and pickle serialization support
    
    Example:
        ```python
        redis_client = RedisClient()
        await redis_client.connect()
        
        # Basic operations
        await redis_client.set("key", {"data": "value"}, ttl=3600)
        value = await redis_client.get("key")
        
        # Pub/sub
        await redis_client.publish("channel", {"event": "data"})
        
        async for message in redis_client.subscribe("channel"):
            print(message)
        ```
    """
    
    def __init__(
        self,
        redis_url: Optional[str] = None,
        password: Optional[str] = None,
        max_connections: int = 50,
        socket_timeout: float = 5.0,
        socket_connect_timeout: float = 5.0,
        retry_on_timeout: bool = True,
        decode_responses: bool = False  # Keep as bytes for pickle support
    ):
        """
        Initialize Redis client.
        
        Args:
            redis_url: Redis connection URL (default from settings)
            password: Redis password (default from settings)
            max_connections: Maximum connections in pool
            socket_timeout: Socket timeout in seconds
            socket_connect_timeout: Socket connect timeout in seconds
            retry_on_timeout: Retry operations on timeout
            decode_responses: Decode responses to strings (disable for pickle)
        """
        self.redis_url = redis_url or settings.REDIS_URL
        self.password = password or settings.REDIS_PASSWORD
        self.max_connections = max_connections
        self.socket_timeout = socket_timeout
        self.socket_connect_timeout = socket_connect_timeout
        self.retry_on_timeout = retry_on_timeout
        self.decode_responses = decode_responses
        
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[Redis] = None
        self._pubsub_client: Optional[Redis] = None
        self._is_connected = False
        
        logger.info(
            "Initialized RedisClient",
            extra={
                "redis_url": self.redis_url.split("@")[-1],  # Hide password
                "max_connections": max_connections
            }
        )
    
    async def connect(self) -> None:
        """
        Establish connection to Redis with connection pooling.
        
        Raises:
            RedisConnectionError: If connection fails
        """
        if self._is_connected:
            logger.debug("Redis already connected")
            return
        
        try:
            # Create connection pool
            self._pool = ConnectionPool.from_url(
                self.redis_url,
                password=self.password,
                max_connections=self.max_connections,
                socket_timeout=self.socket_timeout,
                socket_connect_timeout=self.socket_connect_timeout,
                retry_on_timeout=self.retry_on_timeout,
                decode_responses=self.decode_responses
            )
            
            # Create Redis client
            self._client = Redis(connection_pool=self._pool)
            
            # Create separate client for pub/sub (recommended by redis-py)
            self._pubsub_client = Redis(
                connection_pool=ConnectionPool.from_url(
                    self.redis_url,
                    password=self.password,
                    max_connections=10,  # Fewer connections for pub/sub
                    decode_responses=True  # Decode for pub/sub messages
                )
            )
            
            # Test connection
            await self._client.ping()
            
            self._is_connected = True
            logger.info("Successfully connected to Redis")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}", exc_info=True)
            raise RedisConnectionError(
                message="Failed to connect to Redis",
                details={"error": str(e)}
            )
    
    async def disconnect(self) -> None:
        """Close Redis connections and cleanup resources."""
        if not self._is_connected:
            return
        
        try:
            if self._client:
                await self._client.close()
            
            if self._pubsub_client:
                await self._pubsub_client.close()
            
            if self._pool:
                await self._pool.disconnect()
            
            self._is_connected = False
            logger.info("Disconnected from Redis")
            
        except Exception as e:
            logger.error(f"Error disconnecting from Redis: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Redis connection.
        
        Returns:
            Health status dictionary with metrics
        """
        if not self._is_connected or not self._client:
            return {
                "status": "unhealthy",
                "connected": False,
                "error": "Not connected"
            }
        
        try:
            # Test connection with ping
            start_time = asyncio.get_event_loop().time()
            await self._client.ping()
            latency_ms = (asyncio.get_event_loop().time() - start_time) * 1000
            
            # Get server info
            info = await self._client.info()
            
            return {
                "status": "healthy",
                "connected": True,
                "latency_ms": round(latency_ms, 2),
                "version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "uptime_seconds": info.get("uptime_in_seconds")
            }
            
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e)
            }
    
    def _ensure_connected(self) -> None:
        """Ensure Redis is connected before operations."""
        if not self._is_connected or not self._client:
            raise RedisConnectionError(
                message="Redis not connected. Call connect() first."
            )
    
    def _serialize(self, value: Any, use_pickle: bool = False) -> bytes:
        """
        Serialize value for Redis storage.
        
        Args:
            value: Value to serialize
            use_pickle: Use pickle for complex objects (default: JSON)
            
        Returns:
            Serialized bytes
        """
        if isinstance(value, (str, bytes)):
            return value.encode() if isinstance(value, str) else value
        
        if use_pickle:
            return pickle.dumps(value)
        else:
            return json.dumps(value).encode()
    
    def _deserialize(self, value: Optional[bytes], use_pickle: bool = False) -> Any:
        """
        Deserialize value from Redis.
        
        Args:
            value: Bytes to deserialize
            use_pickle: Value was pickled (default: JSON)
            
        Returns:
            Deserialized value
        """
        if value is None:
            return None
        
        if use_pickle:
            return pickle.loads(value)
        else:
            try:
                return json.loads(value.decode())
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Return as string if not JSON
                return value.decode()
    
    async def get(self, key: str, use_pickle: bool = False) -> Any:
        """
        Get value from Redis.
        
        Args:
            key: Redis key
            use_pickle: Value was pickled (default: JSON)
            
        Returns:
            Deserialized value or None if not found
        """
        self._ensure_connected()
        
        try:
            value = await self._client.get(key)
            return self._deserialize(value, use_pickle=use_pickle)
            
        except Exception as e:
            logger.error(f"Failed to get key {key}: {e}")
            raise RedisOperationError(
                message=f"Failed to get key: {key}",
                details={"error": str(e)}
            )
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        use_pickle: bool = False
    ) -> bool:
        """
        Set value in Redis.
        
        Args:
            key: Redis key
            value: Value to store (will be serialized)
            ttl: Time to live in seconds (optional)
            use_pickle: Use pickle for complex objects
            
        Returns:
            True if successful
        """
        self._ensure_connected()
        
        try:
            serialized = self._serialize(value, use_pickle=use_pickle)
            
            if ttl:
                await self._client.setex(key, ttl, serialized)
            else:
                await self._client.set(key, serialized)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to set key {key}: {e}")
            raise RedisOperationError(
                message=f"Failed to set key: {key}",
                details={"error": str(e)}
            )
    
    async def delete(self, *keys: str) -> int:
        """
        Delete one or more keys from Redis.
        
        Args:
            keys: Keys to delete
            
        Returns:
            Number of keys deleted
        """
        self._ensure_connected()
        
        try:
            return await self._client.delete(*keys)
            
        except Exception as e:
            logger.error(f"Failed to delete keys {keys}: {e}")
            raise RedisOperationError(
                message=f"Failed to delete keys: {keys}",
                details={"error": str(e)}
            )
    
    async def exists(self, *keys: str) -> int:
        """
        Check if keys exist in Redis.
        
        Args:
            keys: Keys to check
            
        Returns:
            Number of existing keys
        """
        self._ensure_connected()
        
        try:
            return await self._client.exists(*keys)
            
        except Exception as e:
            logger.error(f"Failed to check existence of keys {keys}: {e}")
            raise RedisOperationError(
                message=f"Failed to check existence: {keys}",
                details={"error": str(e)}
            )
    
    async def ttl(self, key: str) -> int:
        """
        Get time to live for a key.
        
        Args:
            key: Redis key
            
        Returns:
            TTL in seconds (-1 if no expiry, -2 if key doesn't exist)
        """
        self._ensure_connected()
        
        try:
            return await self._client.ttl(key)
            
        except Exception as e:
            logger.error(f"Failed to get TTL for key {key}: {e}")
            raise RedisOperationError(
                message=f"Failed to get TTL: {key}",
                details={"error": str(e)}
            )
    
    async def expire(self, key: str, seconds: int) -> bool:
        """
        Set expiration time for a key.
        
        Args:
            key: Redis key
            seconds: Expiration time in seconds
            
        Returns:
            True if timeout was set
        """
        self._ensure_connected()
        
        try:
            return await self._client.expire(key, seconds)
            
        except Exception as e:
            logger.error(f"Failed to set expiration for key {key}: {e}")
            raise RedisOperationError(
                message=f"Failed to set expiration: {key}",
                details={"error": str(e)}
            )
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """
        Get keys matching pattern.
        
        Args:
            pattern: Key pattern (default: all keys)
            
        Returns:
            List of matching keys
            
        Warning:
            Use with caution in production - can be slow with many keys
        """
        self._ensure_connected()
        
        try:
            keys = await self._client.keys(pattern)
            return [key.decode() if isinstance(key, bytes) else key for key in keys]
            
        except Exception as e:
            logger.error(f"Failed to get keys with pattern {pattern}: {e}")
            raise RedisOperationError(
                message=f"Failed to get keys: {pattern}",
                details={"error": str(e)}
            )
    
    async def publish(self, channel: str, message: Any) -> int:
        """
        Publish message to a channel.
        
        Args:
            channel: Channel name
            message: Message to publish (will be JSON serialized)
            
        Returns:
            Number of subscribers that received the message
        """
        self._ensure_connected()
        
        try:
            # Serialize message to JSON
            if not isinstance(message, (str, bytes)):
                message = json.dumps(message)
            
            return await self._pubsub_client.publish(channel, message)
            
        except Exception as e:
            logger.error(f"Failed to publish to channel {channel}: {e}")
            raise RedisOperationError(
                message=f"Failed to publish: {channel}",
                details={"error": str(e)}
            )
    
    async def subscribe(
        self,
        *channels: str,
        timeout: Optional[float] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Subscribe to channels and yield messages.
        
        Args:
            channels: Channel names to subscribe to
            timeout: Message timeout in seconds (None = infinite)
            
        Yields:
            Message dictionaries
            
        Example:
            ```python
            async for message in redis_client.subscribe("events"):
                print(message)
            ```
        """
        self._ensure_connected()
        
        pubsub = self._pubsub_client.pubsub()
        
        try:
            # Subscribe to channels
            await pubsub.subscribe(*channels)
            
            logger.info(f"Subscribed to channels: {channels}")
            
            # Listen for messages
            async for message in pubsub.listen():
                if message["type"] == "message":
                    # Parse message data
                    data = message["data"]
                    try:
                        # Try to parse as JSON
                        if isinstance(data, bytes):
                            data = data.decode()
                        data = json.loads(data)
                    except (json.JSONDecodeError, AttributeError):
                        # Keep as string if not JSON
                        pass
                    
                    yield {
                        "channel": message["channel"],
                        "data": data,
                        "pattern": message.get("pattern")
                    }
                    
        except asyncio.TimeoutError:
            logger.debug(f"Subscription timeout for channels: {channels}")
        except Exception as e:
            logger.error(f"Error in subscription: {e}", exc_info=True)
        finally:
            await pubsub.unsubscribe(*channels)
            await pubsub.close()
    
    async def incr(self, key: str, amount: int = 1) -> int:
        """
        Increment key by amount.
        
        Args:
            key: Redis key
            amount: Amount to increment by
            
        Returns:
            New value after increment
        """
        self._ensure_connected()
        
        try:
            return await self._client.incrby(key, amount)
            
        except Exception as e:
            logger.error(f"Failed to increment key {key}: {e}")
            raise RedisOperationError(
                message=f"Failed to increment: {key}",
                details={"error": str(e)}
            )
    
    async def decr(self, key: str, amount: int = 1) -> int:
        """
        Decrement key by amount.
        
        Args:
            key: Redis key
            amount: Amount to decrement by
            
        Returns:
            New value after decrement
        """
        self._ensure_connected()
        
        try:
            return await self._client.decrby(key, amount)
            
        except Exception as e:
            logger.error(f"Failed to decrement key {key}: {e}")
            raise RedisOperationError(
                message=f"Failed to decrement: {key}",
                details={"error": str(e)}
            )
    
    async def hget(self, name: str, key: str, use_pickle: bool = False) -> Any:
        """
        Get field from hash.
        
        Args:
            name: Hash name
            key: Field key
            use_pickle: Value was pickled
            
        Returns:
            Field value or None
        """
        self._ensure_connected()
        
        try:
            value = await self._client.hget(name, key)
            return self._deserialize(value, use_pickle=use_pickle)
            
        except Exception as e:
            logger.error(f"Failed to get hash field {name}:{key}: {e}")
            raise RedisOperationError(
                message=f"Failed to get hash field: {name}:{key}",
                details={"error": str(e)}
            )
    
    async def hset(
        self,
        name: str,
        key: str,
        value: Any,
        use_pickle: bool = False
    ) -> int:
        """
        Set field in hash.
        
        Args:
            name: Hash name
            key: Field key
            value: Field value
            use_pickle: Use pickle for serialization
            
        Returns:
            1 if new field, 0 if updated
        """
        self._ensure_connected()
        
        try:
            serialized = self._serialize(value, use_pickle=use_pickle)
            return await self._client.hset(name, key, serialized)
            
        except Exception as e:
            logger.error(f"Failed to set hash field {name}:{key}: {e}")
            raise RedisOperationError(
                message=f"Failed to set hash field: {name}:{key}",
                details={"error": str(e)}
            )
    
    async def hgetall(self, name: str, use_pickle: bool = False) -> Dict[str, Any]:
        """
        Get all fields from hash.
        
        Args:
            name: Hash name
            use_pickle: Values were pickled
            
        Returns:
            Dictionary of field:value pairs
        """
        self._ensure_connected()
        
        try:
            data = await self._client.hgetall(name)
            return {
                key.decode() if isinstance(key, bytes) else key:
                self._deserialize(value, use_pickle=use_pickle)
                for key, value in data.items()
            }
            
        except Exception as e:
            logger.error(f"Failed to get all hash fields {name}: {e}")
            raise RedisOperationError(
                message=f"Failed to get all hash fields: {name}",
                details={"error": str(e)}
            )
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()


# Global Redis client instance
_redis_client: Optional[RedisClient] = None


async def get_redis_client() -> RedisClient:
    """
    Get or create global Redis client instance.
    
    Returns:
        RedisClient instance
    """
    global _redis_client
    
    if _redis_client is None:
        _redis_client = RedisClient()
        await _redis_client.connect()
    
    return _redis_client


async def close_redis_client() -> None:
    """Close global Redis client."""
    global _redis_client
    
    if _redis_client is not None:
        await _redis_client.disconnect()
        _redis_client = None