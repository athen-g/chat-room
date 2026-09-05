import os
import aiosqlite
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import List, Optional
from models import ChatMessage, AgentThreadMessage, MessageRole

DB_PATH = os.environ.get("DB_PATH", "chat.db")

@asynccontextmanager
async def get_db(path: Optional[str] = None):
    target_path = path or os.environ.get("DB_PATH", "chat.db")
    conn = await aiosqlite.connect(target_path)
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
    finally:
        await conn.close()

async def init_db(db_path: Optional[str] = None):
    target_path = db_path or os.environ.get("DB_PATH", "chat.db")
    async with get_db(target_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS rooms (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL
            );
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                target_user_id TEXT,
                FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
            );
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS agent_threads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
            );
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_room ON messages(room_id, id);
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_threads_user ON agent_threads(room_id, user_id, id);
        """)
        await db.commit()

async def ensure_room_exists(room_id: str):
    """Atomically ensures room entry exists in SQLite without race conditions."""
    async with get_db() as db:
        now = datetime.now(timezone.utc).isoformat()
        await db.execute("INSERT OR IGNORE INTO rooms (id, created_at) VALUES (?, ?)", (room_id, now))
        await db.commit()

async def save_message(message: ChatMessage) -> ChatMessage:
    await ensure_room_exists(message.room_id)
    async with get_db() as db:
        cursor = await db.execute(
            """
            INSERT INTO messages (room_id, user_id, role, content, created_at, target_user_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                message.room_id,
                message.user_id,
                message.role.value if isinstance(message.role, MessageRole) else message.role,
                message.content,
                message.created_at,
                message.target_user_id,
            ),
        )
        await db.commit()
        message.id = cursor.lastrowid
        return message

async def get_room_messages(room_id: str, limit: int = 100) -> List[ChatMessage]:
    async with get_db() as db:
        async with db.execute(
            """
            SELECT id, room_id, user_id, role, content, created_at, target_user_id
            FROM messages
            WHERE room_id = ?
            ORDER BY id ASC
            LIMIT ?
            """,
            (room_id, limit),
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                ChatMessage(
                    id=row["id"],
                    room_id=row["room_id"],
                    user_id=row["user_id"],
                    role=MessageRole(row["role"]),
                    content=row["content"],
                    created_at=row["created_at"],
                    target_user_id=row["target_user_id"],
                )
                for row in rows
            ]

async def save_agent_thread_message(thread_msg: AgentThreadMessage) -> AgentThreadMessage:
    await ensure_room_exists(thread_msg.room_id)
    async with get_db() as db:
        cursor = await db.execute(
            """
            INSERT INTO agent_threads (room_id, user_id, role, content, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                thread_msg.room_id,
                thread_msg.user_id,
                thread_msg.role,
                thread_msg.content,
                thread_msg.created_at,
            ),
        )
        await db.commit()
        thread_msg.id = cursor.lastrowid
        return thread_msg

async def get_user_agent_thread(room_id: str, user_id: str, limit: int = 20) -> List[AgentThreadMessage]:
    """
    CRITICAL CONTEXT ISOLATION FUNCTION:
    Fetches agent conversation history strictly for the specific (room_id, user_id) tuple.
    User B's history is NEVER returned here for User A.
    """
    async with get_db() as db:
        async with db.execute(
            """
            SELECT id, room_id, user_id, role, content, created_at
            FROM agent_threads
            WHERE room_id = ? AND user_id = ?
            ORDER BY id ASC
            LIMIT ?
            """,
            (room_id, user_id, limit),
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                AgentThreadMessage(
                    id=row["id"],
                    room_id=row["room_id"],
                    user_id=row["user_id"],
                    role=row["role"],
                    content=row["content"],
                    created_at=row["created_at"],
                )
                for row in rows
            ]
