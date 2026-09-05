import asyncio
import json
import time
import websockets
import httpx
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stress_test")

BASE_WS_URL = "ws://localhost:8000/ws"
BASE_HTTP_URL = "http://localhost:8000"
ROOM_ID = "stress-test-room"

NUM_USERS = 10         # Concurrent users
MESSAGES_PER_USER = 5  # Messages sent per user
AGENT_PROMPTS_PER_USER = 2 # @agent prompts sent per user

async def simulate_user(user_index: int, results: dict):
    user_id = f"User_{user_index}"
    ws_url = f"{BASE_WS_URL}/{ROOM_ID}/{user_id}"

    received_count = 0
    agent_replies_count = 0
    errors_count = 0

    try:
        async with websockets.connect(ws_url) as ws:
            # Task to listen for incoming broadcasts
            async def listen():
                nonlocal received_count, agent_replies_count, errors_count
                try:
                    while True:
                        msg_text = await ws.recv()
                        data = json.loads(msg_text)
                        if data.get("type") == "message":
                            received_count += 1
                            if data.get("user_id") == "Agent":
                                agent_replies_count += 1
                        elif data.get("type") == "error":
                            errors_count += 1
                except (websockets.ConnectionClosed, asyncio.CancelledError):
                    pass

            listen_task = asyncio.create_task(listen())

            # Send human messages
            for i in range(MESSAGES_PER_USER):
                payload = {"type": "message", "content": f"Hello from {user_id}, msg #{i+1}"}
                await ws.send(json.dumps(payload))
                await asyncio.sleep(0.05)

            # Send @agent prompts concurrently
            for i in range(AGENT_PROMPTS_PER_USER):
                payload = {
                    "type": "message",
                    "content": f"@agent {user_id} secret code is CODE_{user_index}_{i}. What is my code?"
                }
                await ws.send(json.dumps(payload))
                await asyncio.sleep(0.1)

            # Wait briefly for incoming agent responses
            await asyncio.sleep(4.0)
            listen_task.cancel()

            results[user_id] = {
                "received_count": received_count,
                "agent_replies": agent_replies_count,
                "errors": errors_count,
                "status": "SUCCESS"
            }

    except Exception as e:
        logger.error(f"User {user_id} error: {e}")
        results[user_id] = {"status": "FAILED", "error": str(e)}

async def run_stress_test():
    # 1. Health check backend server
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{BASE_HTTP_URL}/api/health")
            if resp.status_code != 200:
                print("[ERROR] Backend health check failed! Make sure backend is running (`python backend/main.py`).")
                return
        except Exception:
            print("[ERROR] Cannot connect to backend server at http://localhost:8000! Start backend first.")
            return

    print(f"=== STRESS TEST STARTED: Spawning {NUM_USERS} concurrent users in room '{ROOM_ID}' ===")
    start_time = time.time()

    results = {}
    tasks = [simulate_user(i, results) for i in range(NUM_USERS)]
    await asyncio.gather(*tasks)

    duration = time.time() - start_time
    print(f"\n=== STRESS TEST COMPLETED IN {duration:.2f} SECONDS ===")
    print("=" * 60)

    success_users = sum(1 for r in results.values() if r.get("status") == "SUCCESS")
    total_messages_received = sum(r.get("received_count", 0) for r in results.values() if r.get("status") == "SUCCESS")
    total_agent_replies = sum(r.get("agent_replies", 0) for r in results.values() if r.get("status") == "SUCCESS")
    total_errors = sum(r.get("errors", 0) for r in results.values() if r.get("status") == "SUCCESS")

    print(f"Concurrent Users Connected:  {success_users} / {NUM_USERS}")
    print(f"Total Broadcast Messages:     {total_messages_received}")
    print(f"Total AI Agent Replies:       {total_agent_replies}")
    print(f"Errors Broadcasted:           {total_errors}")
    print("=" * 60)

    # Verify room history persistence from REST endpoint
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_HTTP_URL}/api/rooms/{ROOM_ID}/messages")
        if resp.is_success:
            history = resp.json()
            print(f"[SUCCESS] DB Persistence Verified: {len(history)} messages saved in SQLite for room '{ROOM_ID}'.")
        else:
            print("[ERROR] DB Verification Failed!")

if __name__ == "__main__":
    asyncio.run(run_stress_test())
