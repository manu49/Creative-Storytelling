from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.ws.manager import connection_manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/{story_id}")
async def websocket_endpoint(websocket: WebSocket, story_id: str):
    """WebSocket endpoint for real-time agent events"""
    await connection_manager.connect(story_id, websocket)

    try:
        while True:
            # Keep connection alive, listen for ping/pong
            data = await websocket.receive_text()
            # Echo ping/pong for keepalive
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await connection_manager.disconnect(story_id, websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        await connection_manager.disconnect(story_id, websocket)
