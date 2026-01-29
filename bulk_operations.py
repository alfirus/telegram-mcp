"""
Bulk operations for Telegram MCP to handle multiple actions efficiently.
"""
import asyncio
from typing import List, Union, Dict, Any
from datetime import datetime
import json


class BulkOperationResult:
    """Result container for bulk operations."""
    
    def __init__(self):
        """Initialize result container."""
        self.successful: List[Dict[str, Any]] = []
        self.failed: List[Dict[str, Any]] = []
        self.total = 0
        self.start_time = datetime.now()
        self.end_time = None
    
    def add_success(self, item_id: Any, result: Any = None) -> None:
        """Add successful operation."""
        self.successful.append({
            "item_id": item_id,
            "status": "success",
            "result": result
        })
        self.total += 1
    
    def add_failure(self, item_id: Any, error: str) -> None:
        """Add failed operation."""
        self.failed.append({
            "item_id": item_id,
            "status": "error",
            "error": error
        })
        self.total += 1
    
    def finalize(self) -> None:
        """Finalize the result."""
        self.end_time = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        duration = (
            (self.end_time - self.start_time).total_seconds()
            if self.end_time else 0
        )
        
        return {
            "total": self.total,
            "successful": len(self.successful),
            "failed": len(self.failed),
            "duration_seconds": duration,
            "success_rate": f"{len(self.successful) / self.total * 100:.2f}%" if self.total > 0 else "0%",
            "successful_items": self.successful,
            "failed_items": self.failed
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)


class BulkOperations:
    """
    Manager for bulk operations with rate limiting and error handling.
    """
    
    def __init__(self, client, rate_limiter=None):
        """
        Initialize bulk operations manager.
        
        Args:
            client: Telegram client instance
            rate_limiter: Optional rate limiter instance
        """
        self.client = client
        self.rate_limiter = rate_limiter
    
    async def send_bulk_messages(
        self,
        chat_ids: List[Union[int, str]],
        message: str,
        delay_seconds: float = 1.0
    ) -> str:
        """
        Send the same message to multiple chats.
        
        Args:
            chat_ids: List of chat IDs or usernames
            message: Message text to send
            delay_seconds: Delay between sends
            
        Returns:
            JSON result summary
        """
        result = BulkOperationResult()
        
        for chat_id in chat_ids:
            try:
                # Apply rate limiting
                if self.rate_limiter:
                    await self.rate_limiter.acquire("write")
                
                # Send message
                await self.client.send_message(chat_id, message)
                result.add_success(chat_id, "Message sent successfully")
                
            except Exception as e:
                result.add_failure(chat_id, str(e))
            
            # Delay between operations
            if delay_seconds > 0:
                await asyncio.sleep(delay_seconds)
        
        result.finalize()
        return result.to_json()
    
    async def forward_bulk_messages(
        self,
        from_chat_id: Union[int, str],
        message_ids: List[int],
        to_chat_ids: List[Union[int, str]],
        delay_seconds: float = 1.0
    ) -> str:
        """
        Forward multiple messages to multiple chats.
        
        Args:
            from_chat_id: Source chat ID
            message_ids: List of message IDs to forward
            to_chat_ids: List of destination chat IDs
            delay_seconds: Delay between operations
            
        Returns:
            JSON result summary
        """
        result = BulkOperationResult()
        
        for to_chat_id in to_chat_ids:
            for message_id in message_ids:
                try:
                    if self.rate_limiter:
                        await self.rate_limiter.acquire("write")
                    
                    await self.client.forward_messages(
                        to_chat_id,
                        message_id,
                        from_chat_id
                    )
                    result.add_success(
                        f"{to_chat_id}:{message_id}",
                        "Message forwarded"
                    )
                    
                except Exception as e:
                    result.add_failure(
                        f"{to_chat_id}:{message_id}",
                        str(e)
                    )
                
                if delay_seconds > 0:
                    await asyncio.sleep(delay_seconds)
        
        result.finalize()
        return result.to_json()
    
    async def delete_bulk_messages(
        self,
        chat_id: Union[int, str],
        message_ids: List[int],
        delay_seconds: float = 0.5
    ) -> str:
        """
        Delete multiple messages from a chat.
        
        Args:
            chat_id: Chat ID
            message_ids: List of message IDs to delete
            delay_seconds: Delay between deletions
            
        Returns:
            JSON result summary
        """
        result = BulkOperationResult()
        
        for message_id in message_ids:
            try:
                if self.rate_limiter:
                    await self.rate_limiter.acquire("write")
                
                await self.client.delete_messages(chat_id, message_id)
                result.add_success(message_id, "Message deleted")
                
            except Exception as e:
                result.add_failure(message_id, str(e))
            
            if delay_seconds > 0:
                await asyncio.sleep(delay_seconds)
        
        result.finalize()
        return result.to_json()
    
    async def invite_bulk_users(
        self,
        group_id: Union[int, str],
        user_ids: List[Union[int, str]],
        delay_seconds: float = 2.0
    ) -> str:
        """
        Invite multiple users to a group.
        
        Args:
            group_id: Group ID
            user_ids: List of user IDs to invite
            delay_seconds: Delay between invites
            
        Returns:
            JSON result summary
        """
        result = BulkOperationResult()
        
        for user_id in user_ids:
            try:
                if self.rate_limiter:
                    await self.rate_limiter.acquire("admin")
                
                await self.client(
                    functions.channels.InviteToChannelRequest(
                        group_id,
                        [user_id]
                    )
                )
                result.add_success(user_id, "User invited")
                
            except Exception as e:
                result.add_failure(user_id, str(e))
            
            if delay_seconds > 0:
                await asyncio.sleep(delay_seconds)
        
        result.finalize()
        return result.to_json()
    
    async def export_bulk_contacts(
        self,
        format: str = "json"
    ) -> str:
        """
        Export all contacts in specified format.
        
        Args:
            format: Export format (json, csv)
            
        Returns:
            Exported contacts string
        """
        try:
            if self.rate_limiter:
                await self.rate_limiter.acquire("read")
            
            contacts = await self.client.get_contacts()
            
            if format == "json":
                contacts_data = []
                for user in contacts:
                    contacts_data.append({
                        "id": user.id,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "username": user.username,
                        "phone": user.phone,
                        "is_bot": user.bot
                    })
                return json.dumps(contacts_data, indent=2)
            
            elif format == "csv":
                import csv
                import io
                
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(["ID", "First Name", "Last Name", "Username", "Phone", "Is Bot"])
                
                for user in contacts:
                    writer.writerow([
                        user.id,
                        user.first_name or "",
                        user.last_name or "",
                        user.username or "",
                        user.phone or "",
                        user.bot
                    ])
                
                return output.getvalue()
            
            else:
                return json.dumps({"error": "Unsupported format"})
        
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    async def mark_bulk_as_read(
        self,
        chat_ids: List[Union[int, str]],
        delay_seconds: float = 0.5
    ) -> str:
        """
        Mark all messages as read in multiple chats.
        
        Args:
            chat_ids: List of chat IDs
            delay_seconds: Delay between operations
            
        Returns:
            JSON result summary
        """
        result = BulkOperationResult()
        
        for chat_id in chat_ids:
            try:
                if self.rate_limiter:
                    await self.rate_limiter.acquire("write")
                
                await self.client.send_read_acknowledge(chat_id)
                result.add_success(chat_id, "Marked as read")
                
            except Exception as e:
                result.add_failure(chat_id, str(e))
            
            if delay_seconds > 0:
                await asyncio.sleep(delay_seconds)
        
        result.finalize()
        return result.to_json()
    
    async def batch_get_chat_info(
        self,
        chat_ids: List[Union[int, str]],
        delay_seconds: float = 0.5
    ) -> str:
        """
        Get information for multiple chats.
        
        Args:
            chat_ids: List of chat IDs
            delay_seconds: Delay between requests
            
        Returns:
            JSON result with chat information
        """
        result = BulkOperationResult()
        
        for chat_id in chat_ids:
            try:
                if self.rate_limiter:
                    await self.rate_limiter.acquire("read")
                
                entity = await self.client.get_entity(chat_id)
                
                chat_info = {
                    "id": entity.id,
                    "title": getattr(entity, "title", None) or getattr(entity, "first_name", "Unknown"),
                    "username": getattr(entity, "username", None),
                    "type": entity.__class__.__name__
                }
                
                result.add_success(chat_id, chat_info)
                
            except Exception as e:
                result.add_failure(chat_id, str(e))
            
            if delay_seconds > 0:
                await asyncio.sleep(delay_seconds)
        
        result.finalize()
        return result.to_json()


# Helper function to create bulk operations instance
def create_bulk_operations(client, rate_limiter=None):
    """
    Create a bulk operations instance.
    
    Args:
        client: Telegram client
        rate_limiter: Optional rate limiter
        
    Returns:
        BulkOperations instance
    """
    return BulkOperations(client, rate_limiter)
