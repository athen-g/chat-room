import asyncio
import json
import logging
from typing import Dict, Set
from fastapi import WebSocket
from models import ChatMessage, OutboundChatMessage, OutboundThinking, OutboundError, MessageRole
from db import save_message
from agent import process_agent_request

logger = logging.getLogger("rooms")

class RoomManager:
    def __init__(self):
        # room_id -> set of WebSocket connections
        self.active_rooms: Dict[str, Set[WebSocket]] = {}
        # room_id -> asyncio.Lock (for serializing DB writes and sequence ordering per room)
        self.room_locks: Dict[str, asyncio.Lock] = {}

    def get_lock(self, room_id: str) -> asyncio.Lock:
        if room_id not in self.room_locks:
            self.room_locks[room_id] = asyncio.Lock()
        return self.room_locks[room_id]

    async def connect(self, room_id: str, websocket: WebSocket):
        await websocket.accept()
        if room_id not in self.active_rooms:
            self.active_rooms[room_id] = set()
        self.active_rooms[room_id].add(websocket)
        logger.info(f"Client connected to room {room_id}. Total clients: {len(self.active_rooms[room_id])}")

    def disconnect(self, room_id: str, websocket: WebSocket):
        if room_id in self.active_rooms:
            self.active_rooms[room_id].discard(websocket)
            if not self.active_rooms[room_id]:
                del self.active_rooms[room_id]
                if room_id in self.room_locks:
                    del self.room_locks[room_id]
        logger.info(f"Client disconnected from room {room_id}")

    async def broadcast_to_room(self, room_id: str, payload: dict):
        if room_id not in self.active_rooms:
            return
        dead_sockets = set()
        message_json = json.dumps(payload)
        for ws in self.active_rooms[room_id]:
            try:
                await ws.send_text(message_json)
            except Exception as e:
                logger.warning(f"Error sending message to socket: {e}")
                dead_sockets.add(ws)

        for ws in dead_sockets:
            self.disconnect(room_id, ws)

    async def broadcast_thinking(self, room_id: str, user_id: str, is_thinking: bool):
        thinking_payload = OutboundThinking(user_id=user_id, is_thinking=is_thinking).model_dump()
        await self.broadcast_to_room(room_id, thinking_payload)

    async def handle_user_message(self, room_id: str, user_id: str, raw_content: str):
        content = raw_content.strip()
        if not content:
            return

        lock = self.get_lock(room_id)

        # Create & save user message under room lock
        async with lock:
            human_msg = ChatMessage(
                room_id=room_id,
                user_id=user_id,
                role=MessageRole.HUMAN,
                content=content,
            )
            saved_human_msg = await save_message(human_msg)

            # Broadcast human message to all room members
            outbound_msg = OutboundChatMessage(
                id=saved_human_msg.id,
                room_id=saved_human_msg.room_id,
                user_id=saved_human_msg.user_id,
                role=saved_human_msg.role.value,
                content=saved_human_msg.content,
                created_at=saved_human_msg.created_at,
            ).model_dump()
            await self.broadcast_to_room(room_id, outbound_msg)

        # Check if message addresses @agent
        if "@agent" in content.lower():
            # Trigger agent response as background task so WS loop remains responsive
            asyncio.create_task(self._process_and_broadcast_agent(room_id, user_id, content))

    async def _process_and_broadcast_agent(self, room_id: str, user_id: str, prompt: str):
        # 1. Notify room that agent is thinking for user_id
        await self.broadcast_thinking(room_id, user_id, is_thinking=True)

        try:
            # 2. Process isolated agent request
            agent_response_text = await process_agent_request(room_id, user_id, prompt)

            # 3. Save & broadcast agent response under room lock
            lock = self.get_lock(room_id)
            async with lock:
                agent_msg = ChatMessage(
                    room_id=room_id,
                    user_id="Agent",
                    role=MessageRole.AGENT,
                    content=agent_response_text,
                    target_user_id=user_id,
                )
                saved_agent_msg = await save_message(agent_msg)

                outbound_agent_msg = OutboundChatMessage(
                    id=saved_agent_msg.id,
                    room_id=saved_agent_msg.room_id,
                    user_id=saved_agent_msg.user_id,
                    role=saved_agent_msg.role.value,
                    content=saved_agent_msg.content,
                    created_at=saved_agent_msg.created_at,
                    target_user_id=saved_agent_msg.target_user_id,
                ).model_dump()
                await self.broadcast_to_room(room_id, outbound_agent_msg)

        except Exception as e:
            logger.error(f"Unexpected error in agent handling for room {room_id}, user {user_id}: {e}")
            error_payload = OutboundError(message=f"Agent failed to respond: {str(e)}").model_dump()
            await self.broadcast_to_room(room_id, error_payload)

        finally:
            # 4. Clear thinking state
            await self.broadcast_thinking(room_id, user_id, is_thinking=False)

manager = RoomManager()
