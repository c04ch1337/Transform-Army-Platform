"""
Rate limiting middleware.

This middleware implements comprehensive rate limiting with:
- IP-based limits
- Tenant-based limits
- Per-endpoint limits
- Exponential backoff for repeat offenders
- Allow-list bypass for trusted IPs
"""

import time
import hashlib
from typing import Callable, Optional, Dict, Tuple
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import redis.asyncio as redis
from fnmatch import fnmatch

from ..security_config import SecuritySettings, RateLimitConfig
from ..logging import get_logger

logger = get_logger(__name__)


class RateLimitExceeded(HTTPException):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(
        self,
        detail: str = "Rate limit exceeded",
        retry_after: Optional[int] = None
    ):
        """
        Initialize rate limit exception.
        
        Args:
            detail: Error message
            retry_after: Seconds until retry is allowed
        """
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers={"Retry-After": str(retry_after)} if retry_after else {}
        )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for comprehensive rate limiting.
    
    Implements multiple layers of rate limiting:
    1. IP-based limits (per IP address)
    2. Tenant-based limits (per tenant_id)
    3. Per-endpoint limits (specific routes)
    4. Exponential backoff for repeat offenders
    
    Rate limit data is stored in Redis with appropriate TTLs.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        redis_url: str,
        security_settings: SecuritySettings
    ):
        """
        Initialize rate limiting middleware.
        
        Args:
            app: ASGI application
            redis_url: Redis connection URL
            security_settings: Security configuration settings
        """
        super().__init__(app)
        self.redis_url = redis_url
        self.settings = security_settings
        self.config = security_settings.rate_limit
        self.redis_client: Optional[redis.Redis] = None
        
        if self.config.enabled:
            logger.info(
                f"Rate limiting enabled: "
                f"{self.config.requests_per_minute} req/min, "
                f"{self.config.requests_per_hour} req/hour"
            )
        else:
            logger.warning("Rate limiting is DISABLED")
    
    async def _get_redis(self) -> redis.Redis:
        """Get or create Redis connection."""
        if self.redis_client is None:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
        return self.redis_client
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP address from request.
        
        Checks X-Forwarded-For and X-Real-IP headers for proxy scenarios.
        
        Args:
            request: Incoming request
            
        Returns:
            Client IP address
        """
        # Check X-Forwarded-For (proxy/load balancer)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Take the first IP in the chain
            return forwarded.split(",")[0].strip()
        
        # Check X-Real-IP
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # Fall back to direct client
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _is_ip_allowed(self, ip: str) -> bool:
        """
        Check if IP is in allow-list (bypass rate limiting).
        
        Args:
            ip: IP address to check
            
        Returns:
            True if IP is allowed to bypass rate limits
        """
        return ip in self.config.ip_allow_list
    
    def _match_endpoint_pattern(self, path: str) -> Optional[int]:
        """
        Find matching endpoint-specific rate limit.
        
        Args:
            path: Request path
            
        Returns:
            Rate limit for the endpoint, or None if no match
        """
        for pattern, limit in self.config.endpoint_limits.items():
            if fnmatch(path, pattern):
                return limit
        return None
    
    async def _check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int
    ) -> Tuple[bool, int, int]:
        """
        Check if rate limit is exceeded using token bucket algorithm.
        
        Args:
            key: Redis key for this rate limit
            limit: Maximum requests allowed
            window_seconds: Time window in seconds
            
        Returns:
            Tuple of (allowed, current_count, retry_after_seconds)
        """
        try:
            redis_client = await self._get_redis()
            current_time = int(time.time())
            window_start = current_time - window_seconds
            
            # Use Redis sorted set for sliding window
            pipe = redis_client.pipeline()
            
            # Remove old entries outside the window
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Count requests in current window
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {str(current_time): current_time})
            
            # Set expiry
            pipe.expire(key, window_seconds)
            
            results = await pipe.execute()
            current_count = results[1]
            
            # Check if limit exceeded
            if current_count >= limit:
                # Calculate retry-after
                oldest_request = await redis_client.zrange(key, 0, 0)
                if oldest_request:
                    oldest_time = int(oldest_request[0])
                    retry_after = window_seconds - (current_time - oldest_time)
                    return False, current_count, max(1, retry_after)
                return False, current_count, window_seconds
            
            return True, current_count + 1, 0
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # Fail open - allow request if Redis is down
            return True, 0, 0
    
    async def _check_backoff(
        self,
        ip: str,
        redis_client: redis.Redis
    ) -> Optional[int]:
        """
        Check if IP is in exponential backoff.
        
        Args:
            ip: Client IP address
            redis_client: Redis client
            
        Returns:
            Seconds remaining in backoff, or None if not in backoff
        """
        if not self.config.enable_exponential_backoff:
            return None
        
        backoff_key = f"rate_limit:backoff:{ip}"
        backoff_until = await redis_client.get(backoff_key)
        
        if backoff_until:
            remaining = int(backoff_until) - int(time.time())
            if remaining > 0:
                return remaining
        
        return None
    
    async def _record_violation(
        self,
        ip: str,
        redis_client: redis.Redis
    ):
        """
        Record rate limit violation and apply exponential backoff if needed.
        
        Args:
            ip: Client IP address
            redis_client: Redis client
        """
        if not self.config.enable_exponential_backoff:
            return
        
        violations_key = f"rate_limit:violations:{ip}"
        backoff_key = f"rate_limit:backoff:{ip}"
        
        # Increment violation counter
        violations = await redis_client.incr(violations_key)
        await redis_client.expire(violations_key, 3600)  # 1 hour window
        
        # Apply backoff if threshold exceeded
        if violations >= self.config.backoff_threshold:
            backoff_until = int(time.time()) + self.config.backoff_duration_seconds
            await redis_client.set(
                backoff_key,
                str(backoff_until),
                ex=self.config.backoff_duration_seconds
            )
            logger.warning(
                f"IP {ip} exceeded rate limit {violations} times - "
                f"applying {self.config.backoff_duration_seconds}s backoff"
            )
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        Apply rate limiting to incoming requests.
        
        Args:
            request: Incoming request
            call_next: Next middleware in chain
            
        Returns:
            Response or raises RateLimitExceeded
        """
        # Skip if rate limiting disabled
        if not self.config.enabled:
            return await call_next(request)
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Check allow-list
        if self._is_ip_allowed(client_ip):
            return await call_next(request)
        
        try:
            redis_client = await self._get_redis()
            
            # Check if in exponential backoff
            backoff_remaining = await self._check_backoff(client_ip, redis_client)
            if backoff_remaining:
                logger.warning(
                    f"Request from {client_ip} blocked by backoff "
                    f"({backoff_remaining}s remaining)"
                )
                raise RateLimitExceeded(
                    detail=f"Too many violations. Try again in {backoff_remaining} seconds",
                    retry_after=backoff_remaining
                )
            
            # 1. Check IP-based rate limit
            ip_key = f"rate_limit:ip:{client_ip}"
            ip_allowed, ip_count, ip_retry = await self._check_rate_limit(
                ip_key,
                self.config.max_requests_per_ip,
                60  # per minute
            )
            
            if not ip_allowed:
                await self._record_violation(client_ip, redis_client)
                logger.warning(
                    f"IP rate limit exceeded for {client_ip}: "
                    f"{ip_count}/{self.config.max_requests_per_ip}"
                )
                raise RateLimitExceeded(
                    detail=f"IP rate limit exceeded: {ip_count} requests per minute",
                    retry_after=ip_retry
                )
            
            # 2. Check tenant-based rate limit
            tenant_id = getattr(request.state, "tenant_id", None)
            if tenant_id:
                tenant_key = f"rate_limit:tenant:{tenant_id}"
                tenant_allowed, tenant_count, tenant_retry = await self._check_rate_limit(
                    tenant_key,
                    self.config.max_requests_per_tenant,
                    60  # per minute
                )
                
                if not tenant_allowed:
                    logger.warning(
                        f"Tenant rate limit exceeded for {tenant_id}: "
                        f"{tenant_count}/{self.config.max_requests_per_tenant}"
                    )
                    raise RateLimitExceeded(
                        detail=f"Tenant rate limit exceeded: {tenant_count} requests per minute",
                        retry_after=tenant_retry
                    )
            
            # 3. Check endpoint-specific rate limit
            endpoint_limit = self._match_endpoint_pattern(request.url.path)
            if endpoint_limit:
                endpoint_key = f"rate_limit:endpoint:{client_ip}:{request.url.path}"
                endpoint_allowed, endpoint_count, endpoint_retry = await self._check_rate_limit(
                    endpoint_key,
                    endpoint_limit,
                    60  # per minute
                )
                
                if not endpoint_allowed:
                    logger.warning(
                        f"Endpoint rate limit exceeded for {request.url.path}: "
                        f"{endpoint_count}/{endpoint_limit}"
                    )
                    raise RateLimitExceeded(
                        detail=f"Endpoint rate limit exceeded: {endpoint_count} requests per minute",
                        retry_after=endpoint_retry
                    )
            
            # 4. Check global per-minute limit
            global_minute_key = f"rate_limit:global:minute:{client_ip}"
            minute_allowed, minute_count, minute_retry = await self._check_rate_limit(
                global_minute_key,
                self.config.requests_per_minute,
                60
            )
            
            if not minute_allowed:
                await self._record_violation(client_ip, redis_client)
                logger.warning(
                    f"Global minute rate limit exceeded for {client_ip}: "
                    f"{minute_count}/{self.config.requests_per_minute}"
                )
                raise RateLimitExceeded(
                    detail=f"Rate limit exceeded: {minute_count} requests per minute",
                    retry_after=minute_retry
                )
            
            # 5. Check global per-hour limit
            global_hour_key = f"rate_limit:global:hour:{client_ip}"
            hour_allowed, hour_count, hour_retry = await self._check_rate_limit(
                global_hour_key,
                self.config.requests_per_hour,
                3600
            )
            
            if not hour_allowed:
                await self._record_violation(client_ip, redis_client)
                logger.warning(
                    f"Global hour rate limit exceeded for {client_ip}: "
                    f"{hour_count}/{self.config.requests_per_hour}"
                )
                raise RateLimitExceeded(
                    detail=f"Rate limit exceeded: {hour_count} requests per hour",
                    retry_after=hour_retry
                )
            
            # Add rate limit headers to response
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(self.config.requests_per_minute)
            response.headers["X-RateLimit-Remaining"] = str(
                max(0, self.config.requests_per_minute - minute_count)
            )
            response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)
            
            return response
            
        except RateLimitExceeded:
            raise
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Fail open - allow request if there's an error
            return await call_next(request)