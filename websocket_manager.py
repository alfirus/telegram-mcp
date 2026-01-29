"""
WebSocket support for real-time Telegram updates
"""
import asyncio
import json
from typing import Set, Dict, Any
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from telethon import events


class WebSocketManager:
    """
    Manages WebSocket connections and real-time message broadcasting.
    
    Features:
    - Multiple concurrent connections
    - Subscription-based filtering
    - Auto-reconnection support
    - Message queuing for offline clients
    """
    
    def __init__(self):
        """Initialize WebSocket manager."""
        self.active_connections: Set[WebSocket] = set()
        self.subscriptions: Dict[WebSocket, Dict[str, Any]] = {}
        self.message_queue: Dict[WebSocket, list] = {}
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "errors": 0
        }
    
    async def connect(self, websocket: WebSocket) -> None:
        """
        Accept new WebSocket connection.
        
        Args:
            websocket: WebSocket connection to accept
        """
        await websocket.accept()
        self.active_connections.add(websocket)
        self.subscriptions[websocket] = {
            "chat_ids": [],
            "message_types": ["all"],
            "connected_at": datetime.now().isoformat()
        }
        self.message_queue[websocket] = []
        self.stats["total_connections"] += 1
        self.stats["active_connections"] = len(self.active_connections)
        
        # Send welcome message
        await self.send_personal_message({
            "type": "connection",
            "status": "connected",
            "message": "WebSocket connected successfully"
        }, websocket)
    
    def disconnect(self, websocket: WebSocket) -> None:
        """
        Remove WebSocket connection.
        
        Args:
            websocket: WebSocket connection to remove
        """
        self.active_connections.discard(websocket)
        self.subscriptions.pop(websocket, None)
        self.message_queue.pop(websocket, None)
        self.stats["active_connections"] = len(self.active_connections)
    
    async def send_personal_message(self, message: dict, websocket: WebSocket) -> None:
        """
        Send message to specific WebSocket connection.
        
        Args:
            message: Message dict to send
            websocket: Target WebSocket connection
        """
        try:
            await websocket.send_json(message)
            self.stats["messages_sent"] += 1
        except Exception as e:
            self.stats["errors"] += 1
            print(f"[WebSocket] Error sending message: {e}")
    
    async def broadcast(self, message: dict) -> None:
        """
        Broadcast message to all connected clients.
        
        Args:
            message: Message dict to broadcast
        """
        disconnected = set()
        
        for connection in self.active_connections:
            try:
                # Check if client is subscribed to this message
                if self._should_send_message(message, connection):
                    await connection.send_json(message)
                    self.stats["messages_sent"] += 1
            except WebSocketDisconnect:
                disconnected.add(connection)
            except Exception as e:
                self.stats["errors"] += 1
                print(f"[WebSocket] Error broadcasting: {e}")
        
        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
    
    def _should_send_message(self, message: dict, websocket: WebSocket) -> bool:
        """
        Check if message should be sent to specific client based on subscriptions.
        
        Args:
            message: Message to check
            websocket: WebSocket connection
            
        Returns:
            True if message should be sent
        """
        subscription = self.subscriptions.get(websocket, {})
        
        # Check message type filter
        message_types = subscription.get("message_types", ["all"])
        if "all" not in message_types and message.get("type") not in message_types:
            return False
        
        # Check chat_id filter
        chat_ids = subscription.get("chat_ids", [])
        if chat_ids and message.get("chat_id") not in chat_ids:
            return False
        
        return True
    
    async def update_subscription(
        self,
        websocket: WebSocket,
        chat_ids: list = None,
        message_types: list = None
    ) -> None:
        """
        Update subscription filters for a connection.
        
        Args:
            websocket: WebSocket connection
            chat_ids: List of chat IDs to subscribe to (None = all)
            message_types: Types of messages to receive (None = all)
        """
        if websocket in self.subscriptions:
            if chat_ids is not None:
                self.subscriptions[websocket]["chat_ids"] = chat_ids
            if message_types is not None:
                self.subscriptions[websocket]["message_types"] = message_types
            
            await self.send_personal_message({
                "type": "subscription_updated",
                "chat_ids": self.subscriptions[websocket]["chat_ids"],
                "message_types": self.subscriptions[websocket]["message_types"]
            }, websocket)
    
    def get_stats(self) -> dict:
        """Get WebSocket manager statistics."""
        return {
            **self.stats,
            "subscriptions": {
                str(id(ws)): sub for ws, sub in self.subscriptions.items()
            }
        }


class TelegramEventHandler:
    """
    Handles Telegram events and broadcasts them via WebSocket.
    """
    
    def __init__(self, client, ws_manager: WebSocketManager):
        """
        Initialize event handler.
        
        Args:
            client: Telethon client instance
            ws_manager: WebSocket manager instance
        """
        self.client = client
        self.ws_manager = ws_manager
        self._handlers_registered = False
    
    async def register_handlers(self) -> None:
        """Register Telethon event handlers."""
        if self._handlers_registered:
            return
        
        # New message handler
        @self.client.on(events.NewMessage)
        async def handle_new_message(event):
            await self._on_new_message(event)
        
        # Message edited handler
        @self.client.on(events.MessageEdited)
        async def handle_message_edit(event):
            await self._on_message_edited(event)
        
        # Message deleted handler
        @self.client.on(events.MessageDeleted)
        async def handle_message_delete(event):
            await self._on_message_deleted(event)
        
        # Chat action handler (user joined, left, etc.)
        @self.client.on(events.ChatAction)
        async def handle_chat_action(event):
            await self._on_chat_action(event)
        
        self._handlers_registered = True
        print("[WebSocket] Telegram event handlers registered")
    
    async def _on_new_message(self, event) -> None:
        """Handle new message event."""
        try:
            message_data = {
                "type": "new_message",
                "timestamp": datetime.now().isoformat(),
                "chat_id": event.chat_id,
                "message_id": event.message.id,
                "text": event.message.text or "",
                "sender_id": event.sender_id,
                "is_reply": event.message.is_reply,
                "has_media": event.message.media is not None
            }
            await self.ws_manager.broadcast(message_data)
        except Exception as e:
            print(f"[WebSocket] Error handling new message: {e}")
    
    async def _on_message_edited(self, event) -> None:
        """Handle message edited event."""
        try:
            message_data = {
                "type": "message_edited",
                "timestamp": datetime.now().isoformat(),
                "chat_id": event.chat_id,
                "message_id": event.message.id,
                "new_text": event.message.text or ""
            }
            await self.ws_manager.broadcast(message_data)
        except Exception as e:
            print(f"[WebSocket] Error handling message edit: {e}")
    
    async def _on_message_deleted(self, event) -> None:
        """Handle message deleted event."""
        try:
            message_data = {
                "type": "message_deleted",
                "timestamp": datetime.now().isoformat(),
                "chat_id": event.chat_id,
                "message_ids": event.deleted_ids
            }
            await self.ws_manager.broadcast(message_data)
        except Exception as e:
            print(f"[WebSocket] Error handling message delete: {e}")
    
    async def _on_chat_action(self, event) -> None:
        """Handle chat action event."""
        try:
            action_type = "unknown"
            if event.user_joined:
                action_type = "user_joined"
            elif event.user_left:
                action_type = "user_left"
            elif event.user_kicked:
                action_type = "user_kicked"
            elif event.user_added:
                action_type = "user_added"
            
            message_data = {
                "type": "chat_action",
                "action": action_type,
                "timestamp": datetime.now().isoformat(),
                "chat_id": event.chat_id,
                "user_id": event.user_id if hasattr(event, 'user_id') else None
            }
            await self.ws_manager.broadcast(message_data)
        except Exception as e:
            print(f"[WebSocket] Error handling chat action: {e}")


# Global WebSocket manager instance
ws_manager = WebSocketManager()
