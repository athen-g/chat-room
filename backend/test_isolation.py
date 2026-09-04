import os
import time
import asyncio
import pytest

# Set unique test environment DB
test_db_filename = f"test_chat_{int(time.time())}.db"
os.environ["DB_PATH"] = test_db_filename

from db import init_db, get_user_agent_thread
from agent import process_agent_request

async def run_test():
    """
    Core test: Context isolation between two users.
    User A and User B talk to @agent in the same room.
    User A's thread context must NEVER bleed into User B's prompt or history.
    """
    print(f"Using test database: {test_db_filename}")
    await init_db(test_db_filename)

    room_id = "test-isolation-room"
    user_a = "Alice"
    user_b = "Bob"

    # Step 1: Alice tells agent her secret favorite color
    response_a1 = await process_agent_request(
        room_id=room_id,
        user_id=user_a,
        prompt="@agent My secret favorite color is Electric Magenta."
    )
    assert response_a1 is not None
    print(f"Alice Prompt 1 -> Agent Response: '{response_a1}'")

    # Step 2: Bob asks agent what HIS secret favorite color is
    response_b1 = await process_agent_request(
        room_id=room_id,
        user_id=user_b,
        prompt="@agent What is my secret favorite color?"
    )
    print(f"Bob Prompt 1   -> Agent Response: '{response_b1}'")

    # Context isolation assertion 1: Bob's response must NOT mention Electric Magenta
    assert "Electric Magenta" not in response_b1, (
        f"CONTEXT ISOLATION LEAK! Bob's response contained Alice's context: {response_b1}"
    )

    # Step 3: Alice asks agent what HER secret favorite color is
    response_a2 = await process_agent_request(
        room_id=room_id,
        user_id=user_a,
        prompt="@agent What is my secret favorite color?"
    )
    print(f"Alice Prompt 2 -> Agent Response: '{response_a2}'")

    # Fetch DB thread contents
    alice_thread = await get_user_agent_thread(room_id, user_a)
    bob_thread = await get_user_agent_thread(room_id, user_b)

    # Structural assertion: Thread contents in DB are strictly separated by user_id
    alice_contents = " ".join([t.content for t in alice_thread])
    bob_contents = " ".join([t.content for t in bob_thread])

    assert "Electric Magenta" in alice_contents, "Alice's thread missing her prompt"
    assert "Electric Magenta" not in bob_contents, "Alice's prompt leaked into Bob's thread DB records!"

    print("\n=======================================================")
    print(" PASSED: CONTEXT ISOLATION TEST SUCCEEDED! ")
    print("=======================================================")
    print(f"Alice Thread DB entries count: {len(alice_thread)}")
    print(f"Bob Thread DB entries count: {len(bob_thread)}")

    # Clean up test DB file
    await asyncio.sleep(0.5)
    try:
        if os.path.exists(test_db_filename):
            os.remove(test_db_filename)
    except Exception as e:
        print(f"Note on cleanup: {e}")

if __name__ == "__main__":
    asyncio.run(run_test())
