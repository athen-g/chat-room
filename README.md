# Multiplayer Chat Room with an AI Participant

A real-time shared chat room application built with **FastAPI** (Python), **React + TypeScript + Vite** (Frontend), **WebSockets**, and **SQLite**.

Multiple users can join a room using a display name and room code, chat live with each other, and address an AI agent using `@agent <question>`.

---

## Key Feature: Guaranteed Per-User Context Isolation

The primary architectural requirement of this application is **context isolation**: when multiple users interact with `@agent` in the same room, each user maintains a completely isolated, private conversation thread history with the AI.

- **Shared Room Transcript (`messages` table)**: Stores all human messages and agent responses in chronological arrival order visible to everyone in the room.
- **Isolated User Agent Threads (`agent_threads` table)**: Stores conversation history strictly partitioned by `(room_id, user_id)`. When User A prompts `@agent`, the LLM prompt is constructed strictly from User A's thread — User B's messages or agent replies are **never** included in User A's context window.

---

## Architectural Choices & Justification

### 1. Transport: WebSockets
- **Rationale**: Chat rooms are naturally bi-directional. Both users send messages to the server and receive incoming messages and real-time state updates (such as `"Agent is thinking for @UserA..."`). WebSockets provide low-latency, full-duplex communication over a single connection, avoiding the overhead of HTTP polling or unidirectional SSE streams.

### 2. Persistence: SQLite (`aiosqlite`)
- **Rationale**: SQLite provides zero-configuration, self-contained persistence. Messages and agent context survive backend restarts cleanly without requiring external database servers (like PostgreSQL or Redis) to run locally. Async `aiosqlite` is used to maintain high throughput on FastAPI's async event loop.

---

## Prerequisites

- **Python 3.10+** (tested on 3.14)
- **Node.js 18+** (tested on v24.15)
- **npm** (tested on 11.12)

---

## Quick Start

### 1. Backend Setup

```bash
# Navigate to project root
cd f:\assignment

# Install backend dependencies
python -m pip install -r backend/requirements.txt

# (Optional) Copy .env.example to backend/.env and set your LLM API Key
# If no key is set, the server runs in deterministic Mock Agent mode for offline testing.
cp backend/.env.example backend/.env

# Run FastAPI backend server (runs on http://localhost:8000)
python backend/main.py
```

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd f:\assignment\frontend

# Install frontend dependencies
npm install

# Start Vite development server (runs on http://localhost:5173)
npm run dev
```

Open `http://localhost:5173` in two separate browser tabs (or windows):
1. Tab 1: Name `Alice`, Room Code `demo-room`
2. Tab 2: Name `Bob`, Room Code `demo-room`

---

## Running Automated Tests

To run the automated context isolation test suite:

```bash
python backend/test_isolation.py
```

Expected Output:
```
Using test database: test_chat_xxxxxx.db
Alice Prompt 1 -> Agent Response: '[Mock Agent] ...'
Bob Prompt 1   -> Agent Response: '[Mock Agent] ...'
Alice Prompt 2 -> Agent Response: '[Mock Agent] ...'

=======================================================
 PASSED: CONTEXT ISOLATION TEST SUCCEEDED! 
=======================================================
Alice Thread DB entries count: 4
Bob Thread DB entries count: 2
```

---

## LLM Provider Configuration

The backend supports:
1. **OpenAI API**: Set `OPENAI_API_KEY` and optional `OPENAI_MODEL` / `OPENAI_BASE_URL` in `backend/.env`.
2. **Google Gemini API**: Set `GEMINI_API_KEY` in `backend/.env`.
3. **Mock Mode (Default Fallback)**: If no keys are configured, the backend automatically uses a mock LLM responder that confirms per-user thread isolation and echo responses without hanging or failing.
