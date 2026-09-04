import os
import asyncio
import httpx
import logging
from typing import Optional
from dotenv import load_dotenv
from db import get_user_agent_thread, save_agent_thread_message
from models import AgentThreadMessage

load_dotenv()

logger = logging.getLogger("agent")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

SYSTEM_PROMPT = (
    "You are a helpful AI assistant in a shared chat room. "
    "Maintain a friendly, concise tone. "
    "Note: Your conversation thread with this user is strictly private and isolated to them."
)

async def _call_llm_api(messages: list[dict]) -> str:
    """Calls OpenAI-compatible or Gemini API endpoint with standard HTTP timeout."""
    if OPENAI_API_KEY:
        url = f"{OPENAI_BASE_URL.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": OPENAI_MODEL,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 500,
        }
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
            
    elif GEMINI_API_KEY:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        # Convert messages to Gemini format
        contents = []
        for m in messages:
            role = "user" if m["role"] == "user" else "model"
            if m["role"] == "system":
                continue
            contents.append({"role": role, "parts": [{"text": m["content"]}]})
            
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.post(url, json={"contents": contents})
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
            
    else:
        # Mock mode when no API key is provided
        await asyncio.sleep(1.0)  # Simulate network latency
        last_user_msg = messages[-1]["content"] if messages else ""
        
        # Simple mock intelligence based on thread history
        user_history = [m for m in messages if m["role"] == "user"]
        return f"[Mock Agent] Received: '{last_user_msg}'. You have sent {len(user_history)} prompt(s) in your isolated session."

async def process_agent_request(room_id: str, user_id: str, prompt: str) -> str:
    """
    Core Context Isolation Engine:
    1. Append user prompt to (room_id, user_id) agent thread.
    2. Read history ONLY for (room_id, user_id).
    3. Invoke LLM with timeout.
    4. Append assistant response to (room_id, user_id) agent thread.
    5. Return assistant response string.
    """
    # 1. Save user prompt to user's isolated thread
    user_thread_entry = AgentThreadMessage(
        room_id=room_id,
        user_id=user_id,
        role="user",
        content=prompt,
    )
    await save_agent_thread_message(user_thread_entry)

    # 2. Fetch history strictly isolated to (room_id, user_id)
    thread_history = await get_user_agent_thread(room_id, user_id, limit=20)

    # 3. Construct prompt array
    llm_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in thread_history:
        llm_messages.append({
            "role": "user" if msg.role == "user" else "assistant",
            "content": msg.content,
        })

    # 4. Call LLM with 15s hard timeout and exception handling
    try:
        response_text = await asyncio.wait_for(
            _call_llm_api(llm_messages),
            timeout=15.0
        )
    except asyncio.TimeoutError:
        logger.error(f"LLM call timed out for user {user_id} in room {room_id}")
        return f"@{user_id} @agent couldn't respond right now — request timed out after 15s."
    except Exception as e:
        logger.error(f"LLM call failed for user {user_id} in room {room_id}: {e}")
        return f"@{user_id} @agent encountered an error while generating a response — please try again."

    # 5. Save assistant response to user's isolated thread
    agent_thread_entry = AgentThreadMessage(
        room_id=room_id,
        user_id=user_id,
        role="assistant",
        content=response_text,
    )
    await save_agent_thread_message(agent_thread_entry)

    return response_text
