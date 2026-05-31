"""Tests for BaseAgent — context building, prompt building, suggestion extraction."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base_agent import BaseAgent
from app.models import AgentTask, Scene


pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Minimal concrete subclass for testing
# ---------------------------------------------------------------------------

class _TestAgent(BaseAgent):
    @property
    def task_type(self) -> str:
        return "test_task"

    @property
    def system_prompt(self) -> str:
        return "You are a test agent."

    @property
    def tools(self):
        return []  # No tools — uses stream path


class _ToolAgent(BaseAgent):
    """Agent with tools — uses tool_loop path."""
    @property
    def task_type(self) -> str:
        return "tool_task"

    @property
    def system_prompt(self) -> str:
        return "You are a tool agent."

    @property
    def tools(self):
        from anthropic.types.tool_param import ToolParam
        return [
            ToolParam(
                name="dummy_tool",
                description="Does nothing",
                input_schema={"type": "object", "properties": {}},
            )
        ]


# ---------------------------------------------------------------------------
# _build_user_prompt
# ---------------------------------------------------------------------------

def test_build_user_prompt_with_scene(mock_llm_service, mock_rag_service):
    agent = _TestAgent(mock_llm_service, mock_rag_service)
    task = MagicMock(spec=AgentTask)
    task.task_type = "grammar_fix"
    context = {
        "story_id": "s1",
        "scene": {
            "id": "sc1",
            "title": "Opening",
            "content": "He run fast.",
            "location": "Forest",
        },
        "rag_results": ["Some prior context..."],
        "scenes": [],
    }
    prompt = agent._build_user_prompt(task, context)
    assert "Opening" in prompt
    assert "He run fast." in prompt
    assert "Forest" in prompt
    assert "Related content" in prompt


def test_build_user_prompt_story_wide(mock_llm_service, mock_rag_service):
    agent = _TestAgent(mock_llm_service, mock_rag_service)
    task = MagicMock(spec=AgentTask)
    task.task_type = "coherence_check"
    context = {
        "story_id": "s1",
        "scenes": [
            {"id": "sc1", "title": "Act 1", "content": "Intro.", "location": None},
            {"id": "sc2", "title": "Act 2", "content": "Conflict.", "location": "Castle"},
        ],
        "rag_results": [],
    }
    prompt = agent._build_user_prompt(task, context)
    assert "Act 1" in prompt
    assert "Act 2" in prompt


def test_build_user_prompt_empty_context(mock_llm_service, mock_rag_service):
    agent = _TestAgent(mock_llm_service, mock_rag_service)
    task = MagicMock(spec=AgentTask)
    task.task_type = "anything"
    context = {"story_id": "s1", "scenes": [], "rag_results": []}
    prompt = agent._build_user_prompt(task, context)
    assert "anything" in prompt


# ---------------------------------------------------------------------------
# _extract_suggestion
# ---------------------------------------------------------------------------

def test_extract_suggestion_text_block(mock_llm_service, mock_rag_service):
    agent = _TestAgent(mock_llm_service, mock_rag_service)
    block = MagicMock()
    block.text = "Great suggestion here"
    response = MagicMock()
    response.content = [block]
    assert agent._extract_suggestion(response) == "Great suggestion here"


def test_extract_suggestion_no_text_block(mock_llm_service, mock_rag_service):
    agent = _TestAgent(mock_llm_service, mock_rag_service)
    block = MagicMock(spec=[])  # No .text attribute
    response = MagicMock()
    response.content = [block]
    result = agent._extract_suggestion(response)
    assert result == "No suggestion generated"


# ---------------------------------------------------------------------------
# run() — streaming path (no tools)
# ---------------------------------------------------------------------------

async def test_run_streaming_path(mock_llm_service, mock_rag_service, db_session: AsyncSession):
    agent = _TestAgent(mock_llm_service, mock_rag_service)
    task = MagicMock(spec=AgentTask)
    task.task_type = "test_task"
    task.story_id = "s1"
    task.scene_id = None

    chunks_received = []
    async def on_chunk(c):
        chunks_received.append(c)

    with patch.object(agent, "_build_context", new=AsyncMock(return_value={"story_id": "s1", "scenes": [], "rag_results": []})):
        result = await agent.run(task, db_session, on_chunk)

    assert result == "Hello world"
    assert chunks_received == ["Hello ", "world"]


# ---------------------------------------------------------------------------
# run() — tool_use path
# ---------------------------------------------------------------------------

async def test_run_tool_path(mock_llm_service, mock_rag_service, db_session: AsyncSession):
    agent = _ToolAgent(mock_llm_service, mock_rag_service)
    task = MagicMock(spec=AgentTask)
    task.task_type = "tool_task"
    task.story_id = "s1"
    task.scene_id = None

    chunks = []
    async def on_chunk(c):
        chunks.append(c)

    with patch.object(agent, "_build_context", new=AsyncMock(return_value={"story_id": "s1", "scenes": [], "rag_results": []})):
        result = await agent.run(task, db_session, on_chunk)

    assert result == "Agent suggestion text"
    mock_llm_service.run_tool_loop.assert_called_once()


# ---------------------------------------------------------------------------
# _build_context — scene path
# ---------------------------------------------------------------------------

async def test_build_context_scene_path(mock_llm_service, mock_rag_service, db_session: AsyncSession):
    from uuid import uuid4
    from app.models import Story

    story = Story(id=str(uuid4()), title="Context Story")
    db_session.add(story)
    scene = Scene(
        id=str(uuid4()),
        story_id=story.id,
        title="Test Scene",
        content="Some content for RAG.",
        scene_type="scene",
        order_index=0,
    )
    db_session.add(scene)
    await db_session.commit()

    task = MagicMock(spec=AgentTask)
    task.story_id = story.id
    task.scene_id = scene.id

    agent = _TestAgent(mock_llm_service, mock_rag_service)
    ctx = await agent._build_context(task, db_session)

    assert ctx["scene"]["id"] == scene.id
    assert ctx["scene"]["title"] == "Test Scene"
    mock_rag_service.retrieve.assert_called_once()


async def test_build_context_story_wide_path(mock_llm_service, mock_rag_service, db_session: AsyncSession):
    from uuid import uuid4
    from app.models import Story

    story = Story(id=str(uuid4()), title="Wide Story")
    db_session.add(story)
    s1 = Scene(id=str(uuid4()), story_id=story.id, title="S1", content="c1", scene_type="scene", order_index=0)
    s2 = Scene(id=str(uuid4()), story_id=story.id, title="S2", content="c2", scene_type="scene", order_index=1)
    db_session.add_all([s1, s2])
    await db_session.commit()

    task = MagicMock(spec=AgentTask)
    task.story_id = story.id
    task.scene_id = None

    agent = _TestAgent(mock_llm_service, mock_rag_service)
    ctx = await agent._build_context(task, db_session)

    assert len(ctx["scenes"]) == 2
    assert "scene" not in ctx
