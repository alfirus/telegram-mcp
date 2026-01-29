"""
Telemetry and monitoring with Prometheus metrics.
"""
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest
from functools import wraps
import time
from typing import Callable


class TelemetryManager:
    """
    Manages metrics collection and monitoring for Telegram MCP.
    
    Metrics tracked:
    - Request counts by tool and status
    - Request duration by tool
    - Active connections
    - Cache hit rate
    - Rate limiter statistics
    - Error counts by type
    """
    
    def __init__(self):
        """Initialize telemetry metrics."""
        
        # Request metrics
        self.request_count = Counter(
            'telegram_mcp_requests_total',
            'Total requests by tool',
            ['tool', 'status']
        )
        
        self.request_duration = Histogram(
            'telegram_mcp_request_duration_seconds',
            'Request duration by tool',
            ['tool'],
            buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0)
        )
        
        # Connection metrics
        self.active_connections = Gauge(
            'telegram_mcp_active_connections',
            'Number of active connections'
        )
        
        self.websocket_connections = Gauge(
            'telegram_mcp_websocket_connections',
            'Number of active WebSocket connections'
        )
        
        # Cache metrics
        self.cache_hits = Counter(
            'telegram_mcp_cache_hits_total',
            'Total cache hits'
        )
        
        self.cache_misses = Counter(
            'telegram_mcp_cache_misses_total',
            'Total cache misses'
        )
        
        self.cache_size = Gauge(
            'telegram_mcp_cache_entries',
            'Number of entries in cache'
        )
        
        # Rate limiter metrics
        self.rate_limit_delays = Counter(
            'telegram_mcp_rate_limit_delays_total',
            'Total rate limit delays'
        )
        
        self.flood_wait_errors = Counter(
            'telegram_mcp_flood_wait_errors_total',
            'Total FloodWait errors encountered'
        )
        
        # Error metrics
        self.errors = Counter(
            'telegram_mcp_errors_total',
            'Total errors by category',
            ['category', 'tool']
        )
        
        # Message metrics
        self.messages_sent = Counter(
            'telegram_mcp_messages_sent_total',
            'Total messages sent'
        )
        
        self.messages_received = Counter(
            'telegram_mcp_messages_received_total',
            'Total messages received via WebSocket'
        )
        
        # Database metrics
        self.db_operations = Counter(
            'telegram_mcp_db_operations_total',
            'Total database operations',
            ['operation']
        )
        
        self.db_operation_duration = Histogram(
            'telegram_mcp_db_operation_duration_seconds',
            'Database operation duration',
            ['operation']
        )
        
        # System info
        self.info = Info('telegram_mcp_info', 'Telegram MCP server information')
        self.info.info({
            'version': '2.0.1',
            'python_version': '3.10+'
        })
    
    def track_request(self, tool_name: str):
        """
        Decorator to track request metrics.
        
        Args:
            tool_name: Name of the tool being tracked
        """
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                status = "success"
                
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    status = "error"
                    self.errors.labels(
                        category=type(e).__name__,
                        tool=tool_name
                    ).inc()
                    raise
                finally:
                    duration = time.time() - start_time
                    self.request_count.labels(
                        tool=tool_name,
                        status=status
                    ).inc()
                    self.request_duration.labels(tool=tool_name).observe(duration)
            
            return wrapper
        return decorator
    
    def update_cache_metrics(self, stats: dict) -> None:
        """
        Update cache-related metrics.
        
        Args:
            stats: Cache statistics dict
        """
        self.cache_size.set(stats.get("entries", 0))
        
        # Set counters to absolute values (cache stats are cumulative)
        hits = stats.get("hits", 0)
        misses = stats.get("misses", 0)
        
        # Prometheus counters can only increase, so we track differences
        # This is a simplified version - in production, use proper counter tracking
    
    def update_rate_limiter_metrics(self, stats: dict) -> None:
        """
        Update rate limiter metrics.
        
        Args:
            stats: Rate limiter statistics dict
        """
        if "delayed_requests" in stats:
            # Track increment only
            pass
        
        if "flood_wait_errors" in stats:
            # Track increment only
            pass
    
    def update_websocket_metrics(self, active_count: int) -> None:
        """
        Update WebSocket connection metrics.
        
        Args:
            active_count: Number of active WebSocket connections
        """
        self.websocket_connections.set(active_count)
    
    def update_connection_pool_metrics(self, pool_stats: dict) -> None:
        """
        Update connection pool metrics.
        
        Args:
            pool_stats: Connection pool statistics
        """
        available = pool_stats.get("available_clients", 0)
        self.active_connections.set(
            pool_stats.get("pool_size", 0) - available
        )
    
    def record_message_sent(self) -> None:
        """Record a message sent event."""
        self.messages_sent.inc()
    
    def record_message_received(self) -> None:
        """Record a message received event."""
        self.messages_received.inc()
    
    def record_db_operation(self, operation: str, duration: float) -> None:
        """
        Record database operation.
        
        Args:
            operation: Operation type (select/insert/update/delete)
            duration: Operation duration in seconds
        """
        self.db_operations.labels(operation=operation).inc()
        self.db_operation_duration.labels(operation=operation).observe(duration)
    
    def get_metrics(self) -> bytes:
        """
        Get Prometheus metrics in exposition format.
        
        Returns:
            Metrics in Prometheus format
        """
        return generate_latest()


# Global telemetry instance
telemetry = TelemetryManager()
