import json
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from db import init_db, get_room_messages
from rooms import manager
from models import OutboundError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized successfully.")
    yield
    logger.info("Shutting down application.")

app = FastAPI(title="Multiplayer AI Chat Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

@app.get("/api/rooms/{room_id}/messages")
async def get_messages(room_id: str):
    """Fetches room message history for initial client load."""
    try:
        messages = await get_room_messages(room_id)
        return [
            {
                "id": m.id,
                "room_id": m.room_id,
                "user_id": m.user_id,
                "role": m.role.value if hasattr(m.role, "value") else m.role,
                "content": m.content,
                "created_at": m.created_at,
                "target_user_id": m.target_user_id,
            }
            for m in messages
        ]
    except Exception as e:
        logger.error(f"Error fetching messages for room {room_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/{room_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, user_id: str):
    await manager.connect(room_id, websocket)
    try:
        while True:
            raw_text = await websocket.receive_text()
            try:
                data = json.loads(raw_text)
                msg_type = data.get("type", "message")
                if msg_type == "ping":
                    await websocket.send_json({"type": "pong"})
                elif msg_type == "message":
                    content = data.get("content", "")
                    await manager.handle_user_message(room_id, user_id, content)
            except json.JSONDecodeError:
                # Handle plain text message fallback
                await manager.handle_user_message(room_id, user_id, raw_text)
    except WebSocketDisconnect:
        manager.disconnect(room_id, websocket)
    except Exception as e:
        logger.error(f"Unexpected WebSocket error for user {user_id} in room {room_id}: {e}")
        manager.disconnect(room_id, websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
