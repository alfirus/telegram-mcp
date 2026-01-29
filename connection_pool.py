"""
Connection pooling for Telegram MCP to handle concurrent operations efficiently.
"""
import asyncio
from typing import Optional, List
from telethon import TelegramClient
from telethon.sessions import StringSession


class TelegramClientPool:
    """
    Connection pool manager for Telegram clients.
    
    Features:
    - Multiple client instances for parallel operations
    - Automatic connection management
    - Health checking and reconnection
    - Load balancing across clients
    """
    
    def __init__(
        self,
        api_id: int,
        api_hash: str,
        session_string: str = None,
        session_name: str = "telegram_session",
        pool_size: int = 5
    ):
        """
        Initialize client pool.
        
        Args:
            api_id: Telegram API ID
            api_hash: Telegram API hash
            session_string: Optional session string
            session_name: Session file name (if not using string session)
            pool_size: Number of clients in the pool
        """
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_string = session_string
        self.session_name = session_name
        self.pool_size = pool_size
        
        self.pool: asyncio.Queue = asyncio.Queue(maxsize=pool_size)
        self.clients: List[TelegramClient] = []
        self.initialized = False
        
        # Statistics
        self.stats = {
            "total_acquisitions": 0,
            "active_clients": 0,
            "failed_connections": 0
        }
    
    async def initialize(self) -> None:
        """Initialize all clients in the pool."""
        if self.initialized:
            return
        
        print(f"[ConnectionPool] Initializing {self.pool_size} clients...")
        
        for i in range(self.pool_size):
            try:
                # Create client with unique session
                if self.session_string:
                    client = TelegramClient(
                        StringSession(self.session_string),
                        self.api_id,
                        self.api_hash
                    )
                else:
                    client = TelegramClient(
                        f"{self.session_name}_{i}",
                        self.api_id,
                        self.api_hash
                    )
                
                await client.start()
                self.clients.append(client)
                await self.pool.put(client)
                print(f"[ConnectionPool] Client {i+1}/{self.pool_size} connected")
                
            except Exception as e:
                self.stats["failed_connections"] += 1
                print(f"[ConnectionPool] Failed to initialize client {i}: {e}")
        
        self.initialized = True
        print(f"[ConnectionPool] Initialized with {len(self.clients)} clients")
    
    async def acquire(self, timeout: float = 10.0) -> Optional[TelegramClient]:
        """
        Acquire a client from the pool.
        
        Args:
            timeout: Maximum wait time in seconds
            
        Returns:
            TelegramClient instance or None if timeout
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            client = await asyncio.wait_for(self.pool.get(), timeout=timeout)
            self.stats["total_acquisitions"] += 1
            self.stats["active_clients"] = self.pool_size - self.pool.qsize()
            return client
        except asyncio.TimeoutError:
            print("[ConnectionPool] Timeout acquiring client from pool")
            return None
    
    async def release(self, client: TelegramClient) -> None:
        """
        Release a client back to the pool.
        
        Args:
            client: Client to release
        """
        if client in self.clients:
            # Check if client is still connected
            if not client.is_connected():
                print("[ConnectionPool] Reconnecting disconnected client...")
                try:
                    await client.connect()
                except Exception as e:
                    print(f"[ConnectionPool] Failed to reconnect client: {e}")
            
            await self.pool.put(client)
            self.stats["active_clients"] = self.pool_size - self.pool.qsize()
    
    async def execute(self, func, *args, **kwargs):
        """
        Execute a function with an automatically managed client.
        
        Args:
            func: Async function to execute (receives client as first arg)
            *args, **kwargs: Arguments to pass to func
            
        Returns:
            Result of func
        """
        client = await self.acquire()
        if not client:
            raise Exception("Failed to acquire client from pool")
        
        try:
            return await func(client, *args, **kwargs)
        finally:
            await self.release(client)
    
    async def health_check(self) -> dict:
        """
        Check health of all clients in the pool.
        
        Returns:
            Health status dict
        """
        healthy = 0
        unhealthy = 0
        
        for client in self.clients:
            if client.is_connected():
                healthy += 1
            else:
                unhealthy += 1
        
        return {
            "total_clients": len(self.clients),
            "healthy": healthy,
            "unhealthy": unhealthy,
            "available": self.pool.qsize(),
            "in_use": self.pool_size - self.pool.qsize()
        }
    
    async def shutdown(self) -> None:
        """Shutdown all clients in the pool."""
        print("[ConnectionPool] Shutting down all clients...")
        
        for client in self.clients:
            try:
                await client.disconnect()
            except Exception as e:
                print(f"[ConnectionPool] Error disconnecting client: {e}")
        
        self.clients.clear()
        self.initialized = False
        print("[ConnectionPool] Shutdown complete")
    
    def get_stats(self) -> dict:
        """Get pool statistics."""
        return {
            **self.stats,
            "pool_size": self.pool_size,
            "available_clients": self.pool.qsize()
        }


class PooledClientContext:
    """Context manager for pooled client usage."""
    
    def __init__(self, pool: TelegramClientPool):
        """
        Initialize context manager.
        
        Args:
            pool: Client pool to use
        """
        self.pool = pool
        self.client = None
    
    async def __aenter__(self) -> TelegramClient:
        """Acquire client from pool."""
        self.client = await self.pool.acquire()
        return self.client
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Release client back to pool."""
        if self.client:
            await self.pool.release(self.client)
