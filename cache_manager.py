"""
Caching layer for Telegram MCP to reduce API calls and improve performance.
"""
import asyncio
import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Optional, Tuple


class TelegramCache:
    """
    Intelligent caching with TTL (Time To Live) for frequently accessed data.
    
    Features:
    - Configurable TTL per cache type
    - Memory-efficient with automatic cleanup
    - Thread-safe operations
    - Cache hit/miss statistics
    """
    
    def __init__(self, default_ttl_seconds: int = 300):
        """
        Initialize cache manager.
        
        Args:
            default_ttl_seconds: Default time-to-live for cached items (default: 5 minutes)
        """
        self.cache: Dict[str, Tuple[Any, datetime]] = {}
        self.default_ttl = timedelta(seconds=default_ttl_seconds)
        self.lock = asyncio.Lock()
        
        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }
        
        # Custom TTL for different data types
        self.ttl_config = {
            "chat_info": timedelta(seconds=600),      # 10 minutes
            "user_info": timedelta(seconds=600),      # 10 minutes
            "messages": timedelta(seconds=120),       # 2 minutes
            "contacts": timedelta(seconds=900),       # 15 minutes
            "dialogs": timedelta(seconds=300),        # 5 minutes
            "participants": timedelta(seconds=600),   # 10 minutes
        }
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a unique cache key from function arguments."""
        key_parts = [prefix]
        key_parts.extend(str(arg) for arg in args)
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        key_string = ":".join(key_parts)
        
        # Use hash for very long keys
        if len(key_string) > 100:
            return f"{prefix}:{hashlib.md5(key_string.encode()).hexdigest()}"
        return key_string
    
    def _get_ttl(self, cache_type: str) -> timedelta:
        """Get TTL for specific cache type."""
        return self.ttl_config.get(cache_type, self.default_ttl)
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if not expired.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        async with self.lock:
            if key in self.cache:
                value, timestamp = self.cache[key]
                # Check if expired (using default TTL)
                if datetime.now() - timestamp < self.default_ttl:
                    self.stats["hits"] += 1
                    return value
                else:
                    # Remove expired entry
                    del self.cache[key]
                    self.stats["evictions"] += 1
            
            self.stats["misses"] += 1
            return None
    
    async def set(self, key: str, value: Any) -> None:
        """
        Store value in cache with timestamp.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        async with self.lock:
            self.cache[key] = (value, datetime.now())
    
    async def get_or_fetch(
        self, 
        cache_type: str,
        fetch_func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Get cached value or fetch and cache if not present.
        
        Args:
            cache_type: Type of cache (determines TTL)
            fetch_func: Async function to fetch data if not cached
            *args, **kwargs: Arguments to pass to fetch_func
            
        Returns:
            Cached or freshly fetched value
        """
        key = self._generate_key(cache_type, *args, **kwargs)
        
        async with self.lock:
            if key in self.cache:
                value, timestamp = self.cache[key]
                ttl = self._get_ttl(cache_type)
                
                if datetime.now() - timestamp < ttl:
                    self.stats["hits"] += 1
                    return value
                else:
                    # Expired, remove it
                    del self.cache[key]
                    self.stats["evictions"] += 1
            
            self.stats["misses"] += 1
        
        # Fetch new data
        value = await fetch_func(*args, **kwargs)
        await self.set(key, value)
        return value
    
    async def invalidate(self, cache_type: str, *args, **kwargs) -> None:
        """
        Invalidate specific cache entry.
        
        Args:
            cache_type: Type of cache
            *args, **kwargs: Arguments to identify the entry
        """
        key = self._generate_key(cache_type, *args, **kwargs)
        async with self.lock:
            if key in self.cache:
                del self.cache[key]
                self.stats["evictions"] += 1
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all cache entries matching a pattern.
        
        Args:
            pattern: Pattern to match (e.g., "chat_info:123")
            
        Returns:
            Number of entries invalidated
        """
        count = 0
        async with self.lock:
            keys_to_delete = [k for k in self.cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self.cache[key]
                count += 1
            self.stats["evictions"] += count
        return count
    
    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self.lock:
            self.stats["evictions"] += len(self.cache)
            self.cache.clear()
    
    async def cleanup_expired(self) -> int:
        """
        Remove all expired entries from cache.
        
        Returns:
            Number of entries removed
        """
        count = 0
        async with self.lock:
            now = datetime.now()
            keys_to_delete = []
            
            for key, (value, timestamp) in self.cache.items():
                # Determine cache type from key prefix
                cache_type = key.split(":")[0] if ":" in key else "default"
                ttl = self._get_ttl(cache_type)
                
                if now - timestamp >= ttl:
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                del self.cache[key]
                count += 1
            
            self.stats["evictions"] += count
        
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "entries": len(self.cache),
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "evictions": self.stats["evictions"],
            "hit_rate": f"{hit_rate:.2f}%",
            "total_requests": total_requests
        }
    
    async def start_cleanup_task(self, interval_seconds: int = 300):
        """
        Start background task to periodically clean up expired entries.
        
        Args:
            interval_seconds: Cleanup interval (default: 5 minutes)
        """
        while True:
            await asyncio.sleep(interval_seconds)
            removed = await self.cleanup_expired()
            if removed > 0:
                print(f"[Cache] Cleaned up {removed} expired entries")


# Global cache instance
cache = TelegramCache()
