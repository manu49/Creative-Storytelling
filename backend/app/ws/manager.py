import json
from fastapi import WebSocket
from typing import Dict, Set, Any


class ConnectionManager:
    """Manages WebSocket connections per story for real-time agent updates"""

    def __init__(self):
        # story_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, story_id: str, websocket: WebSocket) -> None:
        """Register a new WebSocket connection"""
        await websocket.accept()
        if story_id not in self.active_connections:
            self.active_connections[story_id] = set()
        self.active_connections[story_id].add(websocket)

    async def disconnect(self, story_id: str, websocket: WebSocket) -> None:
        """Unregister a WebSocket connection"""
        if story_id in self.active_connections:
            self.active_connections[story_id].discard(websocket)
            if not self.active_connections[story_id]:
                del self.active_connections[story_id]

    async def broadcast_to_story(
        self, story_id: str, message: Dict[str, Any]
    ) -> None:
        """Broadcast a message to all connections for a story"""
        if story_id not in self.active_connections:
            return

        # Create JSON string
        json_message = json.dumps(message)

        # Send to all connected clients
        disconnected = set()
        for websocket in self.active_connections[story_id]:
            try:
                await websocket.send_text(json_message)
            except Exception as e:
                print(f"WebSocket send error: {e}")
                disconnected.add(websocket)

        # Clean up disconnected clients
        for ws in disconnected:
            await self.disconnect(story_id, ws)

    async def send_personal(
        self, websocket: WebSocket, message: Dict[str, Any]
    ) -> None:
        """Send a message to a specific connection"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            print(f"WebSocket send error: {e}")


# Global connection manager instance
connection_manager = ConnectionManager()
