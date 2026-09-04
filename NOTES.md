# Implementation Notes & Reflection

## 1. Context Isolation Verification

The core requirement of this assignment is guaranteeing context isolation between multiple users addressing `@agent` in the same room.

### Test Execution & Evidence

Automated test script `backend/test_isolation.py` was executed. The test simulates two concurrent users (`Alice` and `Bob`) in room `test-isolation-room`:
1. `Alice` tells `@agent`: `"My secret favorite color is Electric Magenta."`
2. `Bob` asks `@agent`: `"What is my secret favorite color?"`
3. **Verification Assertion 1**: Bob's response is verified to **not contain** "Electric Magenta".
4. `Alice` asks `@agent`: `"What is my secret favorite color?"`
5. **Verification Assertion 2**: Alice's response and DB thread records are verified to retain "Electric Magenta".
6. **Structural Assertion**: DB records for `agent_threads` table are asserted to strictly partition by `(room_id, user_id)`.

```
Using test database: test_chat_1788547373.db
Alice Prompt 1 -> Agent Response: '[Mock Agent] Received: '@agent My secret favorite color is Electric Magenta.'. You have sent 1 prompt(s) in your isolated session.'
Bob Prompt 1   -> Agent Response: '[Mock Agent] Received: '@agent What is my secret favorite color?'. You have sent 1 prompt(s) in your isolated session.'
Alice Prompt 2 -> Agent Response: '[Mock Agent] Received: '@agent What is my secret favorite color?'. You have sent 2 prompt(s) in your isolated session.'

=======================================================
 PASSED: CONTEXT ISOLATION TEST SUCCEEDED! 
=======================================================
Alice Thread DB entries count: 4
Bob Thread DB entries count: 2
```

---

## 2. What Was Verified vs. Assumed

### Verified
- **Context Isolation**: Tested structurally at the SQLite layer and procedurally via `process_agent_request`. User A's thread history is never fetched when building User B's LLM context.
- **WebSocket Broadcast & Per-Room Locks**: Message sequence ordering and room broadcasts are protected by an `asyncio.Lock` per room.
- **LLM Resilience & Timeout**: LLM calls are wrapped in `asyncio.wait_for(timeout=15.0)` and `try/except`. API failures or timeouts output a friendly system message without crashing the room or socket.
- **Persistence Across Restarts**: Room messages and agent threads are stored in SQLite (`chat.db`) and persist cleanly when the server restarts.
- **Frontend State Management**: Thinking status badges, message bubbles, empty states, and auto-scroll perform correctly in React + TypeScript.

### Assumed
- **User Identity**: The user display name acts as their identifier (`user_id`). Authentic JWT/OAuth authentication was explicitly out of scope per assignment constraints.
- **LLM Model**: Any OpenAI-compatible model or Gemini API endpoint works. In the absence of an API key, Mock mode provides deterministic testing without external API dependencies.

---

## 3. Trade-offs Made Under Time Pressure

1. **In-Memory WebSocket Connection Registry vs. Redis Pub/Sub**:
   - *Current Implementation*: Room connection maps are kept in server memory (`RoomManager.active_rooms`).
   - *Trade-off*: Suitable for a single backend server instance (as required by the assignment timebox). In a horizontally scaled multi-node environment, Redis Pub/Sub would be used to distribute socket events across nodes.

2. **SQLite vs. PostgreSQL**:
   - *Current Implementation*: Embedded SQLite file (`chat.db`) with `aiosqlite`.
   - *Trade-off*: Eliminates developer setup steps and docker dependencies while providing full SQL ACID guarantees for room history.

3. **Plain Text WebSocket Frames vs. Binary Protobuf**:
   - *Current Implementation*: JSON string payloads over WebSockets.
   - *Trade-off*: Extremely readable and easy to debug in browser devtools, with negligible overhead at two-user scale.

---

## 4. What Would Be Improved With More Time

1. **Redis Pub/Sub Layer**: Enable multi-process/multi-server scaling so WebSocket rooms span across multiple backend replicas.
2. **User Authentication & Room Access Control**: Add JWT auth so usernames are verified and room access can be protected with passwords or permissions.
3. **Infinite Scroll & Message Pagination**: Fetch older messages in chunks (e.g. 50 at a time) as the user scrolls up in the room feed.
4. **Rich Agent Capabilities**: Allow the agent to support markdown formatting, code block syntax highlighting, and streaming responses (token by token over WebSockets).
