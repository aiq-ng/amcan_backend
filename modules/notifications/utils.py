import json
import logging
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Store active connections: {user_id: WebSocket}
        self.active_connections: Dict[int, WebSocket] = {}
        # Store user subscriptions: {user_id: Set[notification_types]}
        self.user_subscriptions: Dict[int, Set[str]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        """Connect a user to the WebSocket"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.user_subscriptions[user_id] = set()
        logger.info(f"[WEBSOCKET] User {user_id} connected")

    def disconnect(self, user_id: int):
        """Disconnect a user from the WebSocket"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.user_subscriptions:
            del self.user_subscriptions[user_id]
        logger.info(f"[WEBSOCKET] User {user_id} disconnected")

    async def send_personal_message(self, message: dict, user_id: int):
        """Send a message to a specific user"""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(json.dumps(message))
                logger.info(f"[WEBSOCKET] Message sent to user {user_id}")
            except Exception as e:
                logger.error(f"[WEBSOCKET] Failed to send message to user {user_id}: {e}")
                self.disconnect(user_id)

    async def broadcast(self, message: dict, notification_type: str = None):
        """Broadcast a message to all connected users or users subscribed to a specific type"""
        disconnected_users = []
        
        for user_id, websocket in self.active_connections.items():
            try:
                # If notification_type is specified, only send to subscribed users
                if notification_type and user_id in self.user_subscriptions:
                    if notification_type not in self.user_subscriptions[user_id]:
                        continue
                
                await websocket.send_text(json.dumps(message))
                logger.info(f"[WEBSOCKET] Broadcast message sent to user {user_id}")
            except Exception as e:
                logger.error(f"[WEBSOCKET] Failed to send broadcast to user {user_id}: {e}")
                disconnected_users.append(user_id)
        
        # Clean up disconnected users
        for user_id in disconnected_users:
            self.disconnect(user_id)

    def subscribe_user(self, user_id: int, notification_type: str):
        """Subscribe a user to a specific notification type"""
        if user_id in self.user_subscriptions:
            self.user_subscriptions[user_id].add(notification_type)
            logger.info(f"[WEBSOCKET] User {user_id} subscribed to {notification_type}")

    def unsubscribe_user(self, user_id: int, notification_type: str):
        """Unsubscribe a user from a specific notification type"""
        if user_id in self.user_subscriptions:
            self.user_subscriptions[user_id].discard(notification_type)
            logger.info(f"[WEBSOCKET] User {user_id} unsubscribed from {notification_type}")

# Global connection manager instance
manager = ConnectionManager()

async def send_notification_to_user(user_id: int, notification_data: dict):
    """Send a notification to a specific user via WebSocket"""
    message = {
        "type": "notification",
        "data": notification_data,
        "timestamp": datetime.utcnow().isoformat()
    }
    await manager.send_personal_message(message, user_id)

async def broadcast_notification(notification_data: dict, notification_type: str = None):
    """Broadcast a notification to all connected users"""
    message = {
        "type": "notification",
        "data": notification_data,
        "timestamp": datetime.utcnow().isoformat()
    }
    await manager.broadcast(message, notification_type)
