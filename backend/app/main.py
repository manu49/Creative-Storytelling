import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import init_db
from app.routers import stories, scenes, characters, agent_tasks, ideas, websocket
from app.agents.worker import agent_worker

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Creative-Storytelling API...")
    await init_db()
    print("✅ Database initialized")

    # Initialize RAG service (loads or creates FAISS index)
    print("📚 Initializing RAG service...")
    # RAG service is initialized on first use via the agents

    # Start agent worker
    print("🤖 Starting agent worker...")
    worker_task = asyncio.create_task(agent_worker.run())

    yield

    # Shutdown
    print("🛑 Shutting down...")
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="Creative-Storytelling API",
    description="AI-powered creative writing assistant with agentic framework",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(stories.router)
app.include_router(scenes.router)
app.include_router(characters.router)
app.include_router(agent_tasks.router)
app.include_router(ideas.router)
app.include_router(websocket.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
