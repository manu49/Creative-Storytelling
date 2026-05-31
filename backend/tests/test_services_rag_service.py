"""Tests for RAGService — chunking, embedding, index, retrieve."""
import os
import tempfile
import pytest
import numpy as np
from unittest.mock import patch, MagicMock


pytestmark = pytest.mark.asyncio


def _make_rag_service(tmp_path: str):
    """Instantiate RAGService with a temp index path (no real disk index)."""
    os.environ["FAISS_INDEX_PATH"] = os.path.join(tmp_path, "test_faiss")
    # Re-import to pick up the env override after monkeypatching settings
    from app.services.rag_service import RAGService
    return RAGService()


@pytest.fixture()
def rag_service():
    with tempfile.TemporaryDirectory() as tmp:
        yield _make_rag_service(tmp)


# ---------------------------------------------------------------------------
# _chunk_text
# ---------------------------------------------------------------------------

def test_chunk_text_basic(rag_service):
    words = ["word"] * 350
    text = " ".join(words)
    chunks = rag_service._chunk_text(text, chunk_size=300, overlap=50)
    assert len(chunks) >= 2
    for chunk in chunks:
        assert chunk.strip() != ""


def test_chunk_text_short_input(rag_service):
    text = "Short sentence."
    chunks = rag_service._chunk_text(text)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_text_empty(rag_service):
    chunks = rag_service._chunk_text("")
    assert chunks == []


def test_chunk_text_overlap_continuity(rag_service):
    words = [str(i) for i in range(400)]
    text = " ".join(words)
    chunks = rag_service._chunk_text(text, chunk_size=100, overlap=20)
    # Check that each chunk after the first shares some words with the previous
    for i in range(1, len(chunks)):
        prev_words = set(chunks[i - 1].split())
        curr_words = set(chunks[i].split())
        assert prev_words & curr_words, "Overlapping chunks should share words"


# ---------------------------------------------------------------------------
# embed_text
# ---------------------------------------------------------------------------

def test_embed_text_returns_float32_array(rag_service):
    embedding = rag_service.embed_text("Hello world")
    assert isinstance(embedding, np.ndarray)
    assert embedding.dtype == np.float32
    assert embedding.shape == (384,)


def test_embed_text_shape_and_dtype_consistent(rag_service):
    """embed_text always returns a (384,) float32 vector regardless of input."""
    e1 = rag_service.embed_text("cat")
    e2 = rag_service.embed_text("quantum physics")
    assert e1.shape == e2.shape == (384,)
    assert e1.dtype == e2.dtype == np.float32


# ---------------------------------------------------------------------------
# retrieve — empty index
# ---------------------------------------------------------------------------

async def test_retrieve_empty_index_returns_empty(rag_service):
    results = await rag_service.retrieve("query", story_id="story-1")
    assert results == []


# ---------------------------------------------------------------------------
# index_scene + retrieve (with mocked DB session)
# ---------------------------------------------------------------------------

async def test_index_and_retrieve(rag_service):
    """Index a mock scene and verify retrieve returns its text."""
    from unittest.mock import AsyncMock, MagicMock
    from sqlalchemy.ext.asyncio import AsyncSession

    # Build a minimal mock scene
    scene = MagicMock()
    scene.id = "scene-1"
    scene.story_id = "story-abc"
    scene.title = "Battle of the Horizon"
    scene.content = "The armies clashed at dawn. Swords rang against shields. The hero charged forward."

    # Mock DB session
    db = MagicMock(spec=AsyncSession)
    db.execute = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()

    await rag_service.index_scene(scene, db)

    # Now retrieve
    results = await rag_service.retrieve("battle", story_id="story-abc", top_k=3)
    assert isinstance(results, list)
    assert len(results) >= 1
    assert any("armies" in r or "battle" in r.lower() or "horizon" in r.lower() for r in results)


async def test_retrieve_filters_by_story_id(rag_service):
    """Chunks indexed under story-A should not appear when querying story-B."""
    from unittest.mock import AsyncMock, MagicMock
    from sqlalchemy.ext.asyncio import AsyncSession

    scene = MagicMock()
    scene.id = "scene-2"
    scene.story_id = "story-A"
    scene.title = "Unique title xyzzy"
    scene.content = "The xyzzy character did something remarkable and unusual."

    db = MagicMock(spec=AsyncSession)
    db.execute = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()

    await rag_service.index_scene(scene, db)

    results = await rag_service.retrieve("xyzzy", story_id="story-B", top_k=5)
    # story-B has no indexed chunks, so nothing should be returned
    assert results == []
