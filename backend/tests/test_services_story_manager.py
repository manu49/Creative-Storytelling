"""Tests for StoryManager task enqueueing logic."""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Story, AgentTask
from app.services.story_manager import StoryManager


pytestmark = pytest.mark.asyncio


async def _make_story(db: AsyncSession) -> str:
    from uuid import uuid4
    story = Story(id=str(uuid4()), title="Manager Test Story")
    db.add(story)
    await db.commit()
    return story.id


async def test_enqueue_task_creates_task(db_session: AsyncSession):
    story_id = await _make_story(db_session)
    task = await StoryManager.enqueue_task(db_session, story_id, "grammar_fix", priority=3)
    assert task.task_type == "grammar_fix"
    assert task.status == "pending"
    assert task.priority == 3
    assert task.story_id == story_id


async def test_enqueue_task_deduplication(db_session: AsyncSession):
    """Enqueueing the same task type+scene twice returns the existing pending task."""
    from uuid import uuid4
    story_id = await _make_story(db_session)
    scene_id = str(uuid4())

    task1 = await StoryManager.enqueue_task(db_session, story_id, "grammar_fix", scene_id=scene_id)
    task2 = await StoryManager.enqueue_task(db_session, story_id, "grammar_fix", scene_id=scene_id)

    assert task1.id == task2.id


async def test_enqueue_task_no_dedup_without_scene(db_session: AsyncSession):
    """Story-wide tasks (no scene_id) are not deduplicated — a new one is always created."""
    story_id = await _make_story(db_session)

    task1 = await StoryManager.enqueue_task(db_session, story_id, "coherence_check")
    task2 = await StoryManager.enqueue_task(db_session, story_id, "coherence_check")

    # Two tasks created (no scene_id dedup)
    assert task1.id != task2.id


async def test_enqueue_scene_tasks(db_session: AsyncSession):
    from uuid import uuid4
    story_id = await _make_story(db_session)
    scene_id = str(uuid4())

    grammar_task, coherence_task = await StoryManager.enqueue_scene_tasks(
        db_session, story_id, scene_id
    )

    assert grammar_task.task_type == "grammar_fix"
    assert grammar_task.scene_id == scene_id
    assert coherence_task.task_type == "coherence_check"
    assert coherence_task.scene_id is None  # story-wide


async def test_enqueue_character_task(db_session: AsyncSession):
    from uuid import uuid4
    story_id = await _make_story(db_session)
    char_id = str(uuid4())

    task = await StoryManager.enqueue_character_task(db_session, story_id, char_id)
    assert task.task_type == "character_arc"
    assert task.story_id == story_id


async def test_enqueue_task_with_input_context(db_session: AsyncSession):
    story_id = await _make_story(db_session)
    ctx = {"trigger": "scene_saved", "scene_id": "abc"}
    task = await StoryManager.enqueue_task(
        db_session, story_id, "grammar_fix", input_context=ctx
    )
    assert task.input_context is not None
    assert "trigger" in task.input_context
