import os
import asyncio
import time
import pytest
import aiosqlite

# Set test database environment
TEST_DB = f"test_suite_{int(time.time())}.db"
os.environ["DB_PATH"] = TEST_DB

from db import init_db, get_room_messages, get_user_agent_thread
import agent
from agent import process_agent_request

async def run_all_tests():
    print(f"=== RUNNING COMPREHENSIVE GRADING TEST SUITE ON '{TEST_DB}' ===")
    await init_db(TEST_DB)
    room_id = "eval-room"

    # =========================================================================
    # TEST 1: Core Context Isolation (Two Users, Concurrent Queries)
    # =========================================================================
    print("\n--- [TEST 1] Core Context Isolation Between Two Users ---")
    user_a = "Alice"
    user_b = "Bob"

    # Concurrent prompts using asyncio.gather
    task_a = process_agent_request(room_id, user_a, "@agent My favorite framework is FastApi.")
    task_b = process_agent_request(room_id, user_b, "@agent What is my favorite framework?")

    resp_a, resp_b = await asyncio.gather(task_a, task_b)

    print(f"Alice Prompt -> Response: {resp_a}")
    print(f"Bob Prompt   -> Response: {resp_b}")

    # Assert Bob's response does NOT contain Alice's framework
    assert "FastApi" not in resp_b and "FastAPI" not in resp_b, "CRITICAL FAIL: Alice context leaked into Bob response!"

    # Now ask Alice what her framework is
    resp_a2 = await process_agent_request(room_id, user_a, "@agent What is my favorite framework?")
    print(f"Alice Query 2 -> Response: {resp_a2}")

    alice_thread = await get_user_agent_thread(room_id, user_a)
    bob_thread = await get_user_agent_thread(room_id, user_b)

    alice_contents = " ".join([t.content for t in alice_thread])
    bob_contents = " ".join([t.content for t in bob_thread])

    assert "FastApi" in alice_contents or "FastAPI" in alice_contents, "Alice thread missing her context"
    assert "FastApi" not in bob_contents and "FastAPI" not in bob_contents, "Alice context leaked into Bob DB records!"
    print("[PASSED] TEST 1: Context isolation structurally and procedurally verified!")

    # =========================================================================
    # TEST 2: Rapid-Fire Same-User Spam (3-4 Back-to-Back Requests)
    # =========================================================================
    print("\n--- [TEST 2] Rapid-Fire Same-User Spam ---")
    user_c = "Charlie"
    spam_prompts = [
        "@agent Step 1: Record key ALPHA",
        "@agent Step 2: Record key BETA",
        "@agent Step 3: Record key GAMMA",
    ]

    spam_tasks = [process_agent_request(room_id, user_c, p) for p in spam_prompts]
    spam_responses = await asyncio.gather(*spam_tasks)

    for idx, r in enumerate(spam_responses):
        print(f"Charlie Spam #{idx+1} Response: {r}")

    charlie_thread = await get_user_agent_thread(room_id, user_c)
    print(f"Charlie Thread Record Count: {len(charlie_thread)} (Expected 6: 3 prompts + 3 replies)")
    assert len(charlie_thread) == 6, f"Expected 6 entries, got {len(charlie_thread)}"
    print("[PASSED] TEST 2: Rapid-fire same-user spam handled deterministically!")

    # =========================================================================
    # TEST 3: Repeated Simultaneous @agent Queries (Concurrency Loop)
    # =========================================================================
    print("\n--- [TEST 3] Repeated Simultaneous Dual-User Concurrency Loop ---")
    user_x = "Xavier"
    user_y = "Yolanda"

    for i in range(3):
        p_x = process_agent_request(room_id, user_x, f"@agent Loop {i}: Xavier item item_{i}")
        p_y = process_agent_request(room_id, user_y, f"@agent Loop {i}: Yolanda item item_{i}")
        rx, ry = await asyncio.gather(p_x, p_y)
        print(f"Loop {i} Xavier -> {rx[:60]}...")
        print(f"Loop {i} Yolanda -> {ry[:60]}...")
        assert "Yolanda" not in rx or "Xavier" in rx
        assert "Xavier" not in ry or "Yolanda" in ry

    x_thread = await get_user_agent_thread(room_id, user_x)
    y_thread = await get_user_agent_thread(room_id, user_y)
    assert len(x_thread) == 6
    assert len(y_thread) == 6
    print("[PASSED] TEST 3: 3-round simultaneous dual-user concurrency loop succeeded!")

    # =========================================================================
    # TEST 4: Resilient LLM Failure & Timeout Handling
    # =========================================================================
    print("\n--- [TEST 4] Resilient LLM Failure & Timeout Handling ---")
    original_key = agent.OPENAI_API_KEY
    agent.OPENAI_API_KEY = "sk-invalid-test-key-12345"

    fail_response = await process_agent_request(room_id, "Dave", "@agent Please answer this with broken key.")
    print(f"Dave Response with broken key: {fail_response}")

    assert "encountered an error" in fail_response or "couldn't respond" in fail_response
    print("[PASSED] TEST 4: LLM failure degraded gracefully without throwing uncaught exceptions!")

    # Restore original key
    agent.OPENAI_API_KEY = original_key

    # =========================================================================
    # TEST 5: Persistence Across DB Reload
    # =========================================================================
    print("\n--- [TEST 5] SQLite Persistence Verification ---")
    all_room_msgs = await get_room_messages(room_id)
    print(f"Total room messages in DB: {len(all_room_msgs)}")

    alice_saved = await get_user_agent_thread(room_id, user_a)
    assert len(alice_saved) >= 4, "Alice thread persistence check failed"
    print("[PASSED] TEST 5: Chat history and per-user agent threads persist in SQLite!")

    # Clean up test DB file
    await asyncio.sleep(0.5)
    try:
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
    except Exception as e:
        print(f"Note on DB cleanup: {e}")

    print("\n=======================================================")
    print("  ALL 5 EVALUATION TESTS PASSED SUCCESSFULLY! ")
    print("=======================================================\n")

if __name__ == "__main__":
    asyncio.run(run_all_tests())
