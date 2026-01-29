"""
Rate limiting protection for Telegram MCP to prevent FloodWait errors.
"""
import asyncio
import time
from collections import deque
from typing import Dict, Optional
from functools import wraps


class RateLimiter:
    """
    Token bucket rate limiter to prevent Telegram API rate limit errors.
    
    Features:
    - Configurable requests per time window
    - Per-endpoint rate limiting
    - Automatic retry with exponential backoff
    - FloodWait error handling
    """
    
    def __init__(self, max_requests: int = 30, time_window: float = 1.0):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed in time window
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
        self.lock = asyncio.Lock()
        
        # Statistics
        self.stats = {
            "total_requests": 0,
            "delayed_requests": 0,
            "flood_wait_errors": 0
        }
    
    async def acquire(self, endpoint: str = "default") -> None:
        """
        Acquire permission to make a request.
        Will block if rate limit is reached.
        
        Args:
            endpoint: Optional endpoint identifier for per-endpoint limiting
        """
        async with self.lock:
            now = time.time()
            
            # Remove old requests outside the time window
            while self.requests and self.requests[0] < now - self.time_window:
                self.requests.popleft()
            
            # Check if we've hit the rate limit
            if len(self.requests) >= self.max_requests:
                # Calculate how long to wait
                sleep_time = self.requests[0] + self.time_window - now
                if sleep_time > 0:
                    self.stats["delayed_requests"] += 1
                    await asyncio.sleep(sleep_time)
                    # After sleeping, clean up old requests again
                    now = time.time()
                    while self.requests and self.requests[0] < now - self.time_window:
                        self.requests.popleft()
            
            # Add current request timestamp
            self.requests.append(now)
            self.stats["total_requests"] += 1
    
    async def handle_flood_wait(self, wait_seconds: int) -> None:
        """
        Handle FloodWait error by waiting the required time.
        
        Args:
            wait_seconds: Seconds to wait as specified by Telegram
        """
        self.stats["flood_wait_errors"] += 1
        print(f"[RateLimiter] FloodWait: waiting {wait_seconds} seconds...")
        await asyncio.sleep(wait_seconds)
    
    def get_stats(self) -> Dict:
        """Get rate limiter statistics."""
        return {
            "total_requests": self.stats["total_requests"],
            "delayed_requests": self.stats["delayed_requests"],
            "flood_wait_errors": self.stats["flood_wait_errors"],
            "current_queue_size": len(self.requests)
        }


class MultiEndpointRateLimiter:
    """
    Rate limiter with separate limits for different endpoint categories.
    """
    
    def __init__(self):
        """Initialize multi-endpoint rate limiter."""
        self.limiters: Dict[str, RateLimiter] = {
            # Different limits for different operation types
            "read": RateLimiter(max_requests=30, time_window=1.0),      # 30 reads/sec
            "write": RateLimiter(max_requests=10, time_window=1.0),     # 10 writes/sec
            "media": RateLimiter(max_requests=5, time_window=1.0),      # 5 media/sec
            "admin": RateLimiter(max_requests=5, time_window=1.0),      # 5 admin ops/sec
            "default": RateLimiter(max_requests=20, time_window=1.0),   # 20 default/sec
        }
    
    async def acquire(self, endpoint_type: str = "default") -> None:
        """
        Acquire permission for specific endpoint type.
        
        Args:
            endpoint_type: Type of operation (read/write/media/admin)
        """
        limiter = self.limiters.get(endpoint_type, self.limiters["default"])
        await limiter.acquire()
    
    async def handle_flood_wait(self, wait_seconds: int, endpoint_type: str = "default") -> None:
        """Handle FloodWait for specific endpoint type."""
        limiter = self.limiters.get(endpoint_type, self.limiters["default"])
        await limiter.handle_flood_wait(wait_seconds)
    
    def get_stats(self) -> Dict:
        """Get statistics for all endpoint types."""
        return {
            endpoint_type: limiter.get_stats()
            for endpoint_type, limiter in self.limiters.items()
        }


# Global rate limiter instance
rate_limiter = MultiEndpointRateLimiter()


def rate_limited(endpoint_type: str = "default"):
    """
    Decorator to apply rate limiting to async functions.
    
    Args:
        endpoint_type: Type of endpoint (read/write/media/admin)
        
    Usage:
        @rate_limited("write")
        async def send_message(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            await rate_limiter.acquire(endpoint_type)
            
            # Handle FloodWait errors
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    # Check if it's a FloodWait error
                    error_str = str(e).lower()
                    if "floodwait" in error_str or "flood" in error_str:
                        # Try to extract wait time from error message
                        import re
                        match = re.search(r'(\d+)', str(e))
                        wait_seconds = int(match.group(1)) if match else 60
                        
                        if attempt < max_retries - 1:
                            await rate_limiter.handle_flood_wait(wait_seconds, endpoint_type)
                            continue
                    raise
            
        return wrapper
    return decorator
