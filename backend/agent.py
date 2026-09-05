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

GROK_API_KEY = os.getenv("GROK_API_KEY") or os.getenv("XAI_API_KEY")
GROK_MODEL = os.getenv("GROK_MODEL", "grok-beta")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

SYSTEM_PROMPT = (
    "You are a helpful AI assistant in a shared chat room. "
    "Maintain a friendly, concise tone. "
    "Note: Your conversation thread with this user is strictly private and isolated to them."
)

async def _call_llm_api(messages: list[dict]) -> str:
    """Calls OpenAI, xAI (Grok), or Gemini API endpoint with standard HTTP timeout."""
    # Option 1: xAI Grok API
    if GROK_API_KEY and GROK_API_KEY.strip():
        url = "https://api.x.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROK_API_KEY.strip()}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": GROK_MODEL,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 500,
        }
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()

    # Option 2: OpenAI / OpenAI-compatible API
    elif OPENAI_API_KEY and OPENAI_API_KEY.strip():
        url = f"{OPENAI_BASE_URL.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY.strip()}",
            "Content-Type": "application/json",
        }
        if "openrouter.ai" in OPENAI_BASE_URL:
            headers["HTTP-Referer"] = "http://localhost:5173"
            headers["X-Title"] = "Multiplayer Chat Room"

        payload = {
            "model": OPENAI_MODEL,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 500,
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()

    # Option 3: Gemini API (tries modern gemini-2.0-flash / gemini-3.6-flash first)
    elif GEMINI_API_KEY and GEMINI_API_KEY.strip():
        key = GEMINI_API_KEY.strip()

        contents = []
        for m in messages:
            if m["role"] == "system":
                continue
            role = "user" if m["role"] == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": m["content"]}]
            })

        system_msgs = [m["content"] for m in messages if m["role"] == "system"]
        payload = {"contents": contents}
        if system_msgs:
            payload["systemInstruction"] = {
                "parts": [{"text": " ".join(system_msgs)}]
            }

        gemini_models = ["gemini-2.0-flash", "gemini-3.6-flash", "gemini-1.5-flash"]
        async with httpx.AsyncClient(timeout=15.0) as client:
            for model_name in gemini_models:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"].strip()

            resp.raise_for_status()

    # Option 4: Mock mode when no valid API key is configured
    else:
        await asyncio.sleep(0.8)
        last_user_msg = messages[-1]["content"] if messages else ""
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
    user_thread_entry = AgentThreadMessage(
        room_id=room_id,
        user_id=user_id,
        role="user",
        content=prompt,
    )
    await save_agent_thread_message(user_thread_entry)

    thread_history = await get_user_agent_thread(room_id, user_id, limit=20)

    llm_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in thread_history:
        llm_messages.append({
            "role": "user" if msg.role == "user" else "assistant",
            "content": msg.content,
        })

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
        err_snippet = str(e)[:120]
        return f"@{user_id} @agent encountered an error: {err_snippet}"

    agent_thread_entry = AgentThreadMessage(
        room_id=room_id,
        user_id=user_id,
        role="assistant",
        content=response_text,
    )
    await save_agent_thread_message(agent_thread_entry)

    return response_text
