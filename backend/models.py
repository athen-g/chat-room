from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Literal
from pydantic import BaseModel, Field

class MessageRole(str, Enum):
    HUMAN = "human"
    AGENT = "agent"
    SYSTEM = "system"

class ChatMessage(BaseModel):
    id: Optional[int] = None
    room_id: str
    user_id: str
    role: MessageRole
    content: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    target_user_id: Optional[str] = None  # Populated when an agent message is in response to a specific user

class AgentThreadMessage(BaseModel):
    id: Optional[int] = None
    room_id: str
    user_id: str
    role: Literal["user", "assistant"]
    content: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# WebSocket Payloads
class InboundMessage(BaseModel):
    type: Literal["message", "ping"] = "message"
    content: str

class OutboundPayload(BaseModel):
    type: str

class OutboundChatMessage(OutboundPayload):
    type: Literal["message"] = "message"
    id: int
    room_id: str
    user_id: str
    role: str
    content: str
    created_at: str
    target_user_id: Optional[str] = None

class OutboundThinking(OutboundPayload):
    type: Literal["thinking"] = "thinking"
    user_id: str
    is_thinking: bool

class OutboundError(OutboundPayload):
    type: Literal["error"] = "error"
    message: str
