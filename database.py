"""
Database layer for persistence and offline access.
"""
import sqlite3
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
from contextlib import asynccontextmanager
import aiosqlite


class MessageStore:
    """
    Persistent storage for Telegram messages.
    
    Features:
    - Message caching for offline access
    - Full-text search
    - Analytics and statistics
    - Conversation history backup
    """
    
    def __init__(self, db_path: str = "telegram_mcp.db"):
        """
        Initialize message store.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.initialized = False
    
    async def initialize(self) -> None:
        """Initialize database schema."""
        if self.initialized:
            return
        
        async with aiosqlite.connect(self.db_path) as db:
            # Messages table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    message_id INTEGER NOT NULL,
                    text TEXT,
                    sender_id INTEGER,
                    sender_name TEXT,
                    timestamp DATETIME NOT NULL,
                    is_outgoing BOOLEAN DEFAULT 0,
                    has_media BOOLEAN DEFAULT 0,
                    media_type TEXT,
                    reply_to_msg_id INTEGER,
                    forward_from_id INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(chat_id, message_id)
                )
            """)
            
            # Chats table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS chats (
                    id INTEGER PRIMARY KEY,
                    title TEXT,
                    username TEXT,
                    chat_type TEXT,
                    participants_count INTEGER,
                    last_message_date DATETIME,
                    is_archived BOOLEAN DEFAULT 0,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Contacts table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS contacts (
                    id INTEGER PRIMARY KEY,
                    first_name TEXT,
                    last_name TEXT,
                    username TEXT,
                    phone TEXT,
                    is_bot BOOLEAN DEFAULT 0,
                    is_blocked BOOLEAN DEFAULT 0,
                    added_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Search history table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    results_count INTEGER,
                    searched_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Analytics table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_type TEXT NOT NULL,
                    metric_value REAL,
                    metadata TEXT,
                    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for performance
            await db.execute("CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp DESC)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_messages_sender_id ON messages(sender_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_chats_type ON chats(chat_type)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_contacts_username ON contacts(username)")
            
            # Create full-text search virtual table
            await db.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
                    text,
                    sender_name,
                    content='messages',
                    content_rowid='id'
                )
            """)
            
            await db.commit()
        
        self.initialized = True
        print(f"[Database] Initialized at {self.db_path}")
    
    async def store_message(
        self,
        chat_id: int,
        message_id: int,
        text: str,
        sender_id: int,
        sender_name: str = None,
        timestamp: datetime = None,
        is_outgoing: bool = False,
        has_media: bool = False,
        media_type: str = None,
        reply_to_msg_id: int = None,
        forward_from_id: int = None
    ) -> None:
        """
        Store a message in the database.
        
        Args:
            chat_id: Chat ID
            message_id: Message ID
            text: Message text
            sender_id: Sender user ID
            sender_name: Sender name
            timestamp: Message timestamp
            is_outgoing: Whether message is outgoing
            has_media: Whether message has media
            media_type: Type of media if present
            reply_to_msg_id: ID of message being replied to
            forward_from_id: ID of original sender if forwarded
        """
        if not self.initialized:
            await self.initialize()
        
        timestamp = timestamp or datetime.now()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO messages 
                (chat_id, message_id, text, sender_id, sender_name, timestamp, 
                 is_outgoing, has_media, media_type, reply_to_msg_id, forward_from_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (chat_id, message_id, text, sender_id, sender_name, timestamp,
                  is_outgoing, has_media, media_type, reply_to_msg_id, forward_from_id))
            
            # Update FTS index
            if text:
                await db.execute("""
                    INSERT OR REPLACE INTO messages_fts(rowid, text, sender_name)
                    SELECT id, text, sender_name FROM messages 
                    WHERE chat_id = ? AND message_id = ?
                """, (chat_id, message_id))
            
            await db.commit()
    
    async def get_messages(
        self,
        chat_id: int,
        limit: int = 100,
        offset: int = 0,
        order: str = "DESC"
    ) -> List[Dict[str, Any]]:
        """
        Get messages from a chat.
        
        Args:
            chat_id: Chat ID
            limit: Maximum number of messages
            offset: Offset for pagination
            order: Sort order (ASC or DESC)
            
        Returns:
            List of message dicts
        """
        if not self.initialized:
            await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(f"""
                SELECT * FROM messages 
                WHERE chat_id = ?
                ORDER BY timestamp {order}
                LIMIT ? OFFSET ?
            """, (chat_id, limit, offset)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def search_messages(
        self,
        query: str,
        chat_id: int = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Full-text search for messages.
        
        Args:
            query: Search query
            chat_id: Optional chat ID to restrict search
            limit: Maximum results
            
        Returns:
            List of matching messages
        """
        if not self.initialized:
            await self.initialize()
        
        # Record search query
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO search_history (query) VALUES (?)",
                (query,)
            )
            await db.commit()
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            if chat_id:
                sql = """
                    SELECT m.* FROM messages m
                    JOIN messages_fts fts ON m.id = fts.rowid
                    WHERE messages_fts MATCH ? AND m.chat_id = ?
                    ORDER BY rank
                    LIMIT ?
                """
                params = (query, chat_id, limit)
            else:
                sql = """
                    SELECT m.* FROM messages m
                    JOIN messages_fts fts ON m.id = fts.rowid
                    WHERE messages_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                """
                params = (query, limit)
            
            async with db.execute(sql, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def store_chat(
        self,
        chat_id: int,
        title: str,
        username: str = None,
        chat_type: str = "private",
        participants_count: int = None
    ) -> None:
        """Store or update chat information."""
        if not self.initialized:
            await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO chats 
                (id, title, username, chat_type, participants_count, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (chat_id, title, username, chat_type, participants_count))
            await db.commit()
    
    async def get_chat_stats(self, chat_id: int) -> Dict[str, Any]:
        """
        Get statistics for a chat.
        
        Args:
            chat_id: Chat ID
            
        Returns:
            Statistics dict
        """
        if not self.initialized:
            await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            # Message count
            async with db.execute(
                "SELECT COUNT(*) as count FROM messages WHERE chat_id = ?",
                (chat_id,)
            ) as cursor:
                row = await cursor.fetchone()
                message_count = row[0] if row else 0
            
            # Top senders
            async with db.execute("""
                SELECT sender_id, sender_name, COUNT(*) as count
                FROM messages
                WHERE chat_id = ?
                GROUP BY sender_id
                ORDER BY count DESC
                LIMIT 10
            """, (chat_id,)) as cursor:
                top_senders = []
                async for row in cursor:
                    top_senders.append({
                        "sender_id": row[0],
                        "sender_name": row[1],
                        "message_count": row[2]
                    })
            
            # Date range
            async with db.execute("""
                SELECT MIN(timestamp) as first, MAX(timestamp) as last
                FROM messages
                WHERE chat_id = ?
            """, (chat_id,)) as cursor:
                row = await cursor.fetchone()
                first_message = row[0] if row else None
                last_message = row[1] if row else None
            
            return {
                "chat_id": chat_id,
                "message_count": message_count,
                "top_senders": top_senders,
                "first_message": first_message,
                "last_message": last_message
            }
    
    async def cleanup_old_messages(self, days: int = 30) -> int:
        """
        Delete messages older than specified days.
        
        Args:
            days: Age threshold in days
            
        Returns:
            Number of messages deleted
        """
        if not self.initialized:
            await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                DELETE FROM messages 
                WHERE timestamp < datetime('now', '-' || ? || ' days')
            """, (days,))
            deleted = cursor.rowcount
            await db.commit()
            return deleted


# Global database instance
db_store = MessageStore()
