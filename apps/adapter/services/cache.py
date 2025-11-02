"""
Caching service with decorators and tenant-scoped caching.

This module provides a comprehensive caching layer with:
- Async caching operations
- Function result caching via decorators
- Tenant-scoped cache keys
- TTL configuration per cache type
- Pattern-based cache invalidation
- Cache warming strategies
"""

import asyncio
import hashlib
import inspect
from functools import wraps
from typing import Any, Optional, Callable, Dict, List, TypeVar, ParamSpec
from datetime import timedelta

from ..core.redis_client import RedisClient, get_redis_client
from ..core.logging import get_logger
from ..core.exceptions import AdapterException


logger = get_logger(__name__)

P = ParamSpec('P')
T = TypeVar('T')


class CacheError(AdapterException):
    """Raised when cache operation fails."""
    pass


class CacheService:
    """
    Service for caching data with tenant isolation.
    
    Features:
    - Tenant-scoped caching
    - Get-or-fetch pattern
    - TTL per cache type
    - Pattern-based invalidation
    - Async operations
    
    Example:
        ```python
        cache = CacheService(redis_client)
        
        # Get or fetch from source
        result = await cache.get_or_fetch(
            key="workflow:123",
            fetch_func=lambda: db.get_workflow(workflow_id),
            ttl=3600,
            tenant_id="tenant-1"
        )
        
        # Invalidate cache
        await cache.invalidate("workflow:123", tenant_id="tenant-1")
        
        # Invalidate by pattern
        await cache.invalidate_pattern("workflow:*", tenant_id="tenant-1")
        ```
    """
    
    # Default TTL values for different cache types (in seconds)
    DEFAULT_TTLS = {
        "workflow": 3600,          # 1 hour
        "workflow_def": 7200,      # 2 hours
        "tenant_config": 1800,     # 30 minutes
        "provider_config": 1800,   # 30 minutes
        "api_response": 300,       # 5 minutes
        "user_session": 86400,     # 24 hours
        "rate_limit": 60,          # 1 minute
        "health_check": 30,        # 30 seconds
        "default": 600             # 10 minutes
    }
    
    def __init__(self, redis_client: Optional[RedisClient] = None):
        """
        Initialize cache service.
        
        Args:
            redis_client: Redis client instance (will create if None)
        """
        self.redis_client = redis_client
        self._initialized = False
        
        logger.info("Initialized CacheService")
    
    async def _ensure_initialized(self) -> None:
        """Ensure Redis client is initialized."""
        if not self._initialized:
            if self.redis_client is None:
                self.redis_client = await get_redis_client()
            self._initialized = True
    
    def _generate_key(
        self,
        key: str,
        tenant_id: Optional[str] = None,
        namespace: str = "cache"
    ) -> str:
        """
        Generate cache key with tenant scope.
        
        Args:
            key: Base cache key
            tenant_id: Tenant ID for scoping
            namespace: Cache namespace
            
        Returns:
            Full cache key
        """
        if tenant_id:
            return f"{namespace}:tenant:{tenant_id}:{key}"
        return f"{namespace}:{key}"
    
    def _get_cache_type(self, key: str) -> str:
        """
        Extract cache type from key.
        
        Args:
            key: Cache key
            
        Returns:
            Cache type string
        """
        # Extract first segment as cache type
        parts = key.split(":")
        if len(parts) > 0:
            return parts[0]
        return "default"
    
    def _get_ttl(self, cache_type: Optional[str] = None, ttl: Optional[int] = None) -> int:
        """
        Get TTL for cache type.
        
        Args:
            cache_type: Type of cache
            ttl: Explicit TTL override
            
        Returns:
            TTL in seconds
        """
        if ttl is not None:
            return ttl
        
        return self.DEFAULT_TTLS.get(cache_type or "default", self.DEFAULT_TTLS["default"])
    
    async def get(
        self,
        key: str,
        tenant_id: Optional[str] = None,
        use_pickle: bool = False
    ) -> Any:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            tenant_id: Tenant ID for scoping
            use_pickle: Value was pickled
            
        Returns:
            Cached value or None if not found
        """
        await self._ensure_initialized()
        
        full_key = self._generate_key(key, tenant_id)
        
        try:
            value = await self.redis_client.get(full_key, use_pickle=use_pickle)
            
            if value is not None:
                logger.debug(f"Cache hit: {full_key}")
            else:
                logger.debug(f"Cache miss: {full_key}")
            
            return value
            
        except Exception as e:
            logger.error(f"Cache get error for {full_key}: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        tenant_id: Optional[str] = None,
        use_pickle: bool = False
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            tenant_id: Tenant ID for scoping
            use_pickle: Use pickle for serialization
            
        Returns:
            True if successful
        """
        await self._ensure_initialized()
        
        full_key = self._generate_key(key, tenant_id)
        cache_type = self._get_cache_type(key)
        actual_ttl = self._get_ttl(cache_type, ttl)
        
        try:
            await self.redis_client.set(
                full_key,
                value,
                ttl=actual_ttl,
                use_pickle=use_pickle
            )
            
            logger.debug(f"Cache set: {full_key} (TTL: {actual_ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for {full_key}: {e}")
            return False
    
    async def get_or_fetch(
        self,
        key: str,
        fetch_func: Callable[[], Any],
        ttl: Optional[int] = None,
        tenant_id: Optional[str] = None,
        use_pickle: bool = False
    ) -> Any:
        """
        Get value from cache or fetch from source if not cached.
        
        Args:
            key: Cache key
            fetch_func: Function to fetch value if not cached
            ttl: Time to live in seconds
            tenant_id: Tenant ID for scoping
            use_pickle: Use pickle for serialization
            
        Returns:
            Cached or fetched value
        """
        await self._ensure_initialized()
        
        # Try to get from cache
        value = await self.get(key, tenant_id=tenant_id, use_pickle=use_pickle)
        
        if value is not None:
            return value
        
        # Fetch from source
        try:
            if inspect.iscoroutinefunction(fetch_func):
                value = await fetch_func()
            else:
                value = fetch_func()
            
            # Cache the result
            await self.set(
                key,
                value,
                ttl=ttl,
                tenant_id=tenant_id,
                use_pickle=use_pickle
            )
            
            logger.debug(f"Fetched and cached: {key}")
            return value
            
        except Exception as e:
            logger.error(f"Error fetching for cache key {key}: {e}")
            raise
    
    async def invalidate(
        self,
        key: str,
        tenant_id: Optional[str] = None
    ) -> bool:
        """
        Invalidate (delete) cached value.
        
        Args:
            key: Cache key
            tenant_id: Tenant ID for scoping
            
        Returns:
            True if key was deleted
        """
        await self._ensure_initialized()
        
        full_key = self._generate_key(key, tenant_id)
        
        try:
            deleted = await self.redis_client.delete(full_key)
            
            if deleted > 0:
                logger.info(f"Cache invalidated: {full_key}")
                return True
            else:
                logger.debug(f"Cache key not found: {full_key}")
                return False
                
        except Exception as e:
            logger.error(f"Cache invalidation error for {full_key}: {e}")
            return False
    
    async def invalidate_pattern(
        self,
        pattern: str,
        tenant_id: Optional[str] = None
    ) -> int:
        """
        Invalidate all keys matching pattern.
        
        Args:
            pattern: Key pattern (e.g., "workflow:*")
            tenant_id: Tenant ID for scoping
            
        Returns:
            Number of keys deleted
            
        Warning:
            Use with caution in production - can be slow with many keys
        """
        await self._ensure_initialized()
        
        full_pattern = self._generate_key(pattern, tenant_id)
        
        try:
            # Get all matching keys
            keys = await self.redis_client.keys(full_pattern)
            
            if not keys:
                logger.debug(f"No keys found matching pattern: {full_pattern}")
                return 0
            
            # Delete all matching keys
            deleted = await self.redis_client.delete(*keys)
            
            logger.info(f"Cache pattern invalidated: {full_pattern} ({deleted} keys)")
            return deleted
            
        except Exception as e:
            logger.error(f"Cache pattern invalidation error for {full_pattern}: {e}")
            return 0
    
    async def exists(
        self,
        key: str,
        tenant_id: Optional[str] = None
    ) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key
            tenant_id: Tenant ID for scoping
            
        Returns:
            True if key exists
        """
        await self._ensure_initialized()
        
        full_key = self._generate_key(key, tenant_id)
        
        try:
            return await self.redis_client.exists(full_key) > 0
            
        except Exception as e:
            logger.error(f"Cache exists check error for {full_key}: {e}")
            return False
    
    async def get_ttl(
        self,
        key: str,
        tenant_id: Optional[str] = None
    ) -> int:
        """
        Get remaining TTL for key.
        
        Args:
            key: Cache key
            tenant_id: Tenant ID for scoping
            
        Returns:
            TTL in seconds (-1 if no expiry, -2 if key doesn't exist)
        """
        await self._ensure_initialized()
        
        full_key = self._generate_key(key, tenant_id)
        
        try:
            return await self.redis_client.ttl(full_key)
            
        except Exception as e:
            logger.error(f"Cache TTL check error for {full_key}: {e}")
            return -2
    
    async def get_many(
        self,
        keys: List[str],
        tenant_id: Optional[str] = None,
        use_pickle: bool = False
    ) -> Dict[str, Any]:
        """
        Get multiple values from cache.
        
        Args:
            keys: List of cache keys
            tenant_id: Tenant ID for scoping
            use_pickle: Values were pickled
            
        Returns:
            Dictionary of key:value pairs (only existing keys)
        """
        await self._ensure_initialized()
        
        results = {}
        
        for key in keys:
            value = await self.get(key, tenant_id=tenant_id, use_pickle=use_pickle)
            if value is not None:
                results[key] = value
        
        return results
    
    async def set_many(
        self,
        items: Dict[str, Any],
        ttl: Optional[int] = None,
        tenant_id: Optional[str] = None,
        use_pickle: bool = False
    ) -> int:
        """
        Set multiple values in cache.
        
        Args:
            items: Dictionary of key:value pairs
            ttl: Time to live in seconds
            tenant_id: Tenant ID for scoping
            use_pickle: Use pickle for serialization
            
        Returns:
            Number of items successfully cached
        """
        await self._ensure_initialized()
        
        success_count = 0
        
        for key, value in items.items():
            if await self.set(key, value, ttl=ttl, tenant_id=tenant_id, use_pickle=use_pickle):
                success_count += 1
        
        return success_count


def cached(
    ttl: Optional[int] = None,
    key_prefix: Optional[str] = None,
    tenant_param: str = "tenant_id",
    use_pickle: bool = False
):
    """
    Decorator for caching function results.
    
    Args:
        ttl: Cache TTL in seconds (None = use default for cache type)
        key_prefix: Prefix for cache key (None = use function name)
        tenant_param: Parameter name for tenant ID
        use_pickle: Use pickle for serialization
        
    Example:
        ```python
        @cached(ttl=3600, key_prefix="workflow")
        async def get_workflow(workflow_id: str, tenant_id: str):
            # Fetch from database
            return workflow
        
        # First call fetches from DB and caches
        result = await get_workflow("123", tenant_id="tenant-1")
        
        # Second call returns from cache
        result = await get_workflow("123", tenant_id="tenant-1")
        ```
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # Get cache service
            cache = CacheService()
            await cache._ensure_initialized()
            
            # Extract tenant_id from params
            tenant_id = kwargs.get(tenant_param)
            
            # Generate cache key from function name and arguments
            func_name = key_prefix or func.__name__
            
            # Create deterministic key from args and kwargs
            args_str = "_".join(str(arg) for arg in args)
            kwargs_str = "_".join(f"{k}={v}" for k, v in sorted(kwargs.items()) if k != tenant_param)
            
            parts = [func_name]
            if args_str:
                parts.append(args_str)
            if kwargs_str:
                parts.append(kwargs_str)
            
            cache_key = ":".join(parts)
            
            # Hash if key is too long
            if len(cache_key) > 200:
                key_hash = hashlib.sha256(cache_key.encode()).hexdigest()[:16]
                cache_key = f"{func_name}:{key_hash}"
            
            # Try to get from cache
            cached_value = await cache.get(
                cache_key,
                tenant_id=tenant_id,
                use_pickle=use_pickle
            )
            
            if cached_value is not None:
                logger.debug(f"Cache hit for {func_name}")
                return cached_value
            
            # Call function
            result = await func(*args, **kwargs)
            
            # Cache result
            await cache.set(
                cache_key,
                result,
                ttl=ttl,
                tenant_id=tenant_id,
                use_pickle=use_pickle
            )
            
            logger.debug(f"Cached result for {func_name}")
            return result
        
        # Handle sync functions
        if not inspect.iscoroutinefunction(func):
            @wraps(func)
            def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                # For sync functions, run async wrapper in event loop
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(async_wrapper(*args, **kwargs))
            
            return sync_wrapper
        
        return async_wrapper
    
    return decorator


def cache_key(prefix: str, *parts: str, tenant_id: Optional[str] = None) -> str:
    """
    Generate cache key from parts.
    
    Args:
        prefix: Key prefix
        parts: Key components
        tenant_id: Tenant ID for scoping
        
    Returns:
        Cache key string
        
    Example:
        ```python
        key = cache_key("workflow", workflow_id, "steps", tenant_id=tenant_id)
        # Returns: "workflow:123:steps" (with tenant scoping)
        ```
    """
    key_parts = [prefix, *parts]
    key = ":".join(str(part) for part in key_parts if part)
    
    if tenant_id:
        return f"tenant:{tenant_id}:{key}"
    
    return key


# Global cache service instance
_cache_service: Optional[CacheService] = None


async def get_cache_service() -> CacheService:
    """
    Get or create global cache service instance.
    
    Returns:
        CacheService instance
    """
    global _cache_service
    
    if _cache_service is None:
        _cache_service = CacheService()
        await _cache_service._ensure_initialized()
    
    return _cache_service