"""
Shared fixtures for the test suite.

Strategy:
- In-memory SQLite for all DB tests (isolated, fast).
- SentenceTransformer is monkey-patched at module level *before* any app code
  is imported, so RAGService never tries to download a model.
- LLMService is mocked per-test to avoid hitting the Anthropic API.
"""
import os
import sys
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch
import numpy as np

# ---------------------------------------------------------------------------
# 1.  Environment — must be set before app.config is imported
# ---------------------------------------------------------------------------
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-dummy")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("FAISS_INDEX_PATH", "/tmp/test_faiss_index")

# ---------------------------------------------------------------------------
# 2.  Stub SentenceTransformer **before** any app module is imported.
#     rag_service.py does `from sentence_transformers import SentenceTransformer`
#     at import time, so we must replace the attribute on the real module
#     (which is already installed as faiss-cpu was) before that line runs.
# ---------------------------------------------------------------------------
import types

_mock_st_instance = MagicMock()
_mock_st_instance.encode = MagicMock(return_value=np.zeros(384, dtype="float32"))
_MockSentenceTransformer = MagicMock(return_value=_mock_st_instance)

try:
    import sentence_transformers as _st_mod  # imported here so we can mutate it
    # Replace the class on the module — rag_service.py will pick up this binding
    _st_mod.SentenceTransformer = _MockSentenceTransformer  # type: ignore[attr-defined]
except Exception:
    # sentence-transformers (and its heavy torch dependency) isn't installed —
    # provide a lightweight stub so the suite runs in lean environments.
    _st_mod = types.ModuleType("sentence_transformers")
    _st_mod.SentenceTransformer = _MockSentenceTransformer
    sys.modules["sentence_transformers"] = _st_mod

# faiss is likewise optional for the test suite; stub it if unavailable.
try:
    import faiss  # noqa: F401
except Exception:
    sys.modules["faiss"] = MagicMock()

# ---------------------------------------------------------------------------
# 3.  Now it's safe to import the app
# ---------------------------------------------------------------------------
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import pool
from httpx import AsyncClient, ASGITransport

from app.database import Base, get_db
from app.main import app


# ---------------------------------------------------------------------------
# In-memory database engine
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
    poolclass=pool.StaticPool,
    connect_args={"check_same_thread": False},
)

_TestSession = async_sessionmaker(
    _engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _create_tables():
    """Create all tables once per test session."""
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture()
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Transactional session rolled back after each test."""
    async with _engine.begin() as connection:
        async with AsyncSession(connection, expire_on_commit=False) as session:
            yield session
            await connection.rollback()


# ---------------------------------------------------------------------------
# HTTP test client
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture()
async def client(db_session: AsyncSession):
    """AsyncClient with in-memory DB and mocked RAG + worker."""
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    mock_rag = MagicMock()
    mock_rag.index_scene = AsyncMock(return_value=None)
    mock_rag.retrieve = AsyncMock(return_value=[])
    mock_rag.reindex_story = AsyncMock(return_value=None)

    with patch("app.routers.scenes.RAGService", return_value=mock_rag), \
         patch("app.routers.agent_tasks.RAGService", return_value=mock_rag):
        with patch("app.main.agent_worker.run", new_callable=AsyncMock):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                yield ac

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Mocks for unit tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_llm_service():
    service = MagicMock()

    async def _stream(*args, **kwargs):
        for chunk in ["Hello ", "world"]:
            yield chunk

    service.stream_generate = _stream

    fake_response = MagicMock()
    fake_block = MagicMock()
    fake_block.text = "Agent suggestion text"
    fake_block.type = "text"
    fake_response.content = [fake_block]
    fake_response.stop_reason = "end_turn"
    service.run_tool_loop = AsyncMock(return_value=fake_response)

    return service


@pytest.fixture()
def mock_rag_service():
    service = MagicMock()
    service.index_scene = AsyncMock(return_value=None)
    service.retrieve = AsyncMock(return_value=["Relevant context snippet"])
    service.reindex_story = AsyncMock(return_value=None)
    return service
