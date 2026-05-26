from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Story
import json

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/{story_id}")
async def websocket_endpoint(websocket: WebSocket, story_id: str):
    """WebSocket endpoint for real-time agent events"""
    await websocket.accept()
    # TODO: Implement WebSocket connection manager
    # TODO: Register connection with ConnectionManager
    # TODO: Handle incoming messages and broadcast agent events

    try:
        while True:
            data = await websocket.receive_text()
            # Echo for now
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        # TODO: Unregister connection
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close(code=1000)
