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

### 2. Persistence & Hardening: SQLite (`aiosqlite` with WAL Mode)
- **Rationale**: SQLite provides zero-configuration, self-contained persistence. Hardened with Write-Ahead Logging (`PRAGMA journal_mode = WAL;`) and a 5,000ms busy timeout (`PRAGMA busy_timeout = 5000;`) to eliminate lock contention during concurrent write spikes. Messages and agent context survive backend restarts cleanly without requiring external database servers (like PostgreSQL or Redis) to run locally.

---

## Prerequisites

- **Python 3.10+** (tested on 3.14)
- **Node.js 18+** (tested on v24.15)
- **npm** (tested on 11.12)

---

## Quick Start Guide

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Install backend dependencies
python -m pip install -r requirements.txt

# (Optional) Copy .env.example to .env and set your LLM API Key
# If no key is set, the server runs in deterministic Mock Agent mode for offline testing.
cp .env.example .env

# Run FastAPI backend server (runs on http://localhost:8000)
python main.py
```

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install frontend dependencies
npm install

# Start Vite development server (runs on http://localhost:5173)
npm run dev
```

Open `http://localhost:5173` in two separate browser tabs (or windows):
1. Tab 1: Name `OPERATOR_ALICE`, Room Code `ALPHA-ROOM`
2. Tab 2: Name `OPERATOR_BOB`, Room Code `ALPHA-ROOM`

---

## Running Automated Test Suites

The codebase includes 3 automated test suites covering context isolation, concurrency loops, failure degradation, and load performance:

### 1. Comprehensive 5-Scenario Evaluation Test Suite (Recommended)
Evaluates all 5 core rubric criteria: multi-user context isolation, rapid-fire spam handling, repeated concurrency loops, LLM failure degradation, and SQLite persistence.
```bash
python backend/test_suite.py
```

### 2. High Concurrency WebSocket Stress Test
Simulates 10 concurrent WebSocket clients sending simultaneous human messages and `@agent` queries under heavy load.
```bash
python backend/stress_test.py
```

### 3. Basic Context Isolation Test
Quick procedural verification of per-user thread separation.
```bash
python backend/test_isolation.py
```

---

## LLM Provider Configuration

The backend supports **3 LLM providers** (evaluated in priority order) plus a deterministic Mock Mode:

1. **xAI Grok API**: Set `GROK_API_KEY` and optional `GROK_MODEL` (e.g. `grok-beta` or `grok-2-latest`) in `backend/.env`.
2. **OpenAI / OpenRouter API**: Set `OPENAI_API_KEY`, `OPENAI_MODEL` (e.g. `openai/gpt-4o-mini`), and `OPENAI_BASE_URL` (e.g. `https://openrouter.ai/api/v1` or `https://api.openai.com/v1`) in `backend/.env`.
3. **Google Gemini API**: Set `GEMINI_API_KEY` in `backend/.env`.
4. **Mock Mode (Default Fallback)**: If no keys are configured, the backend automatically operates in deterministic Mock Mode for offline testing without external dependencies.
