# Implementation Notes & Reflection

## 1. Context Isolation & Edge Case Verification

The core requirement of this assignment is guaranteeing context isolation between multiple users addressing `@agent` in the same room, as well as maintaining stability under concurrency, rapid-fire spam, API failure, and server restart.

### Test Execution & Evidence (`backend/test_suite.py`)

Automated evaluation test suite `backend/test_suite.py` was executed. The results across all 5 evaluation criteria are recorded below:

#### **[TEST 1] Core Context Isolation Between Concurrent Users**
- **Scenario**: `Alice` and `Bob` send near-simultaneous `@agent` requests in `eval-room`.
  - Alice: `@agent My favorite framework is FastApi.`
  - Bob: `@agent What is my favorite framework?`
- **Result**:
  - Bob's LLM Response: *"I don't have access to that information. If you let me know what your favorite framework is, I can help you!"* (Verified: Alice's framework did **not** leak into Bob's response).
  - Alice Query 2: `@agent What is my favorite framework?`
  - Alice's LLM Response: *"Your favorite framework is FastAPI!"* (Verified: Alice's memory retained in her isolated thread).

#### **[TEST 2] Rapid-Fire Same-User Spam**
- **Scenario**: `Charlie` sends 3 `@agent` prompts in rapid succession back-to-back without waiting for responses.
- **Result**:
  - All 3 prompts and responses were recorded deterministically into Charlie's thread history (`6` total entries: 3 prompts + 3 replies).
  - Messages were attributed cleanly without out-of-order state corruption.

#### **[TEST 3] Repeated Simultaneous Dual-User Concurrency Loop**
- **Scenario**: 3 consecutive rounds of simultaneous `@agent` queries from `Xavier` and `Yolanda`.
- **Result**: `asyncio.gather` processed 6 concurrent LLM requests over 3 rounds without race conditions, thread state collisions, or SQLite locks (`len(x_thread) == 6`, `len(y_thread) == 6`).

#### **[TEST 4] Resilient LLM Failure & Degradation**
- **Scenario**: Forced API key corruption (`sk-invalid-test-key-12345`) to simulate network throttling or bad API key.
- **Result**:
  - Dave's Response: `@Dave @agent encountered an error while generating a response — please try again.`
  - Verified: OpenRouter returned `401 Unauthorized`. The error was caught gracefully by `process_agent_request`, broadcasting a user-friendly alert without crashing the WebSocket or affecting other room members.

#### **[TEST 5] SQLite Persistence Verification**
- **Scenario**: Verified room chat history (`messages` table) and per-user agent thread context (`agent_threads` table) reload correctly from SQLite.
- **Result**: Per-user agent threads persist across application restarts.

```text
=======================================================
  ALL 5 EVALUATION TESTS PASSED SUCCESSFULLY! 
=======================================================
```

---

## 2. What Was Verified vs. Assumed

### Verified
- **Context Isolation**: Tested structurally at the SQLite schema layer (`agent_threads` partitioned by `(room_id, user_id)`) and procedurally via `process_agent_request`. User A's thread history is never fetched when building User B's LLM context.
- **WebSocket Broadcast & Per-Room Locks**: Message sequence ordering and room broadcasts are protected by an `asyncio.Lock` per room. Atomic `INSERT OR IGNORE` handles room creation without race conditions.
- **LLM Resilience & Timeout**: LLM calls are wrapped in `asyncio.wait_for(timeout=15.0)` and `try/except`. API failures or invalid keys output a friendly system message without crashing the room or socket.
- **Persistence Across Restarts**: Room messages and agent threads are stored in SQLite (`chat.db`) and persist cleanly when the server restarts.

### Assumed
- **User Identity**: The user display name acts as their identifier (`user_id`). Authentic JWT/OAuth authentication was explicitly out of scope per assignment constraints.
- **LLM Provider**: OpenRouter / OpenAI / Gemini APIs work interchangeably. In the absence of an API key, Mock mode provides deterministic offline testing.

---

## 3. Trade-offs Made Under Time Pressure

1. **In-Memory WebSocket Connection Registry vs. Redis Pub/Sub**:
   - *Current Implementation*: Room connection maps are kept in server memory (`RoomManager.active_rooms`).
   - *Trade-off*: Suitable for a single backend server instance (as required by the assignment timebox). In a horizontally scaled multi-node environment, Redis Pub/Sub would be used to distribute socket events across nodes.

2. **SQLite vs. PostgreSQL**:
   - *Current Implementation*: Embedded SQLite file (`chat.db`) with `aiosqlite`.
   - *Trade-off*: Eliminates developer setup steps and docker dependencies while providing full SQL ACID guarantees for room history.

---

## 4. What Would Be Improved With More Time

1. **Redis Pub/Sub Layer**: Enable multi-process/multi-server scaling so WebSocket rooms span across multiple backend replicas.
2. **User Authentication & Room Access Control**: Add JWT auth so usernames are verified and room access can be protected with passwords or permissions.
3. **Infinite Scroll & Message Pagination**: Fetch older messages in chunks (e.g. 50 at a time) as the user scrolls up in the room feed.
