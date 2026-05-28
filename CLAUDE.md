# Creative-Storytelling — Claude Code Guide

AI-powered creative writing assistant. Writers dump raw ideas; background agents (Claude Haiku + Sonnet) refine grammar, coherence, characters, and scenes. Real-time updates via WebSocket.

## Dev Setup

### Prerequisites

- Python 3.9+ (3.11 recommended; code maintains 3.8 compat — see [Python Compatibility](#python-compatibility))
- Node.js 18+
- Anthropic API key

### Environment

```bash
cp .env.example backend/.env
# Edit backend/.env and set ANTHROPIC_API_KEY
```

### Backend

```bash
cd backend
pip install -e .
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The app auto-creates SQLite tables on first startup (`init_db()`). No Alembic migration step needed for local dev.

### Frontend

```bash
cd frontend
npm install
npm run dev   # http://localhost:3000
```

### Docker (recommended for full stack)

```bash
docker-compose up
# Frontend: http://localhost:3000
# Backend API + Swagger: http://localhost:8000/docs
```

## Key Commands

| Task | Command |
|---|---|
| Backend dev server | `cd backend && uvicorn app.main:app --reload` |
| Frontend dev server | `cd frontend && npm run dev` |
| Type check (backend) | `cd backend && python -m mypy app/` |
| Lint (backend) | `cd backend && ruff check app/` |
| Format (backend) | `cd backend && black app/` |
| Type check (frontend) | `cd frontend && npx tsc --noEmit` |
| Lint (frontend) | `cd frontend && npm run lint` |

## Architecture

```
User (browser)
   │  REST + WebSocket
   ▼
Next.js 15 (frontend/:3000)
   │
FastAPI (backend/:8000)
   ├── Routers: stories, scenes, characters, agent_tasks, ideas, export
   ├── AgentWorker — polls task queue every 3s, runs ≤2 concurrent agents
   │     ├── GrammarAgent (Haiku) — typos, style
   │     ├── CoherenceAgent (Sonnet) — plot consistency, pacing
   │     ├── CharacterAgent (Sonnet) — arc/motivation consistency
   │     └── SceneExpandAgent (Sonnet) — raw idea → full scene draft
   ├── RAGService — Sentence-Transformers + FAISS for story context retrieval
   └── WebSocket manager — streams agent events to browser in real-time
```

### Agent Flow

1. Scene saved → `AgentTask` rows created in SQLite
2. `AgentWorker.run()` polls queue, dispatches to correct agent
3. Agent calls Claude API (tool use for structured output)
4. Suggestion written back to DB; WebSocket broadcasts to frontend
5. User accepts/rejects → scene updated + FAISS re-indexed

## Project Structure

```
creative-storytelling/
├── CLAUDE.md                 # ← you are here
├── skills.md                 # Python 3.8 compatibility rules
├── .env.example              # env var template
├── docker-compose.yml
├── backend/
│   ├── pyproject.toml
│   └── app/
│       ├── main.py           # FastAPI app + lifespan
│       ├── config.py         # Pydantic Settings (reads backend/.env)
│       ├── database.py       # async SQLAlchemy engine + init_db()
│       ├── agents/           # GrammarAgent, CoherenceAgent, CharacterAgent, SceneExpandAgent, worker
│       ├── models/           # SQLAlchemy ORM: Story, Scene, Character, AgentTask, RagChunk
│       ├── routers/          # FastAPI route handlers
│       ├── schemas/          # Pydantic I/O schemas
│       ├── services/         # LLMService (Anthropic SDK), RAGService (FAISS), StoryManager
│       ├── tools/            # Claude tool definitions for structured agent output
│       └── ws/               # WebSocket connection manager
└── frontend/
    └── src/
        ├── app/              # Next.js pages (dashboard + /stories/[id])
        ├── components/       # Editor (Tiptap), modals
        ├── hooks/            # useStoryWebSocket
        ├── store/            # Zustand: storyStore
        └── types/            # Shared TypeScript types
```

## Environment Variables

All vars live in `backend/.env`. Required:

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Your Claude API key (required) |
| `DATABASE_URL` | SQLite URL (default: `sqlite+aiosqlite:///./data/creative_storytelling.db`) |
| `HAIKU_MODEL` | Fast agent model (default: `claude-haiku-4-5-20251001`) |
| `SONNET_MODEL` | Deep analysis model (default: `claude-sonnet-4-6`) |
| `FAISS_INDEX_PATH` | Path for FAISS index (default: `./data/faiss_index`) |
| `EMBEDDING_MODEL` | Sentence-Transformers model (default: `all-MiniLM-L6-v2`) |
| `AGENT_POLL_INTERVAL_SECONDS` | Worker poll interval (default: `3.0`) |
| `AGENT_MAX_CONCURRENT_TASKS` | Max parallel agents (default: `2`) |
| `CORS_ORIGINS` | JSON list of allowed origins (default: `["http://localhost:3000"]`) |

Frontend reads `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_WS_URL` from environment (set in Docker or a `.env.local` in `frontend/`).

## Python Compatibility

The backend targets Python 3.8+ syntax. Full rules in `skills.md`. Key constraints:

- Use `List[str]` not `list[str]` — use `from typing import List, Dict, Optional, Union`
- Use `Optional[str]` not `str | None`
- No walrus operator (`:=`) in hot paths

## Key Patterns

### Adding a new agent

1. Create `backend/app/agents/my_agent.py` extending `BaseAgent`
2. Define Claude tool in `backend/app/tools/story_tools.py`
3. Register in `backend/app/agents/worker.py` dispatch table
4. Add `AgentTask.task_type` enum value in `backend/app/models/agent_task.py`

### Adding a new API route

1. Create `backend/app/routers/my_router.py` with `APIRouter`
2. Add Pydantic schemas in `backend/app/schemas/`
3. Register router in `backend/app/main.py`

### Resetting local data

```bash
rm -rf data/
# Restart backend — init_db() recreates tables
```
