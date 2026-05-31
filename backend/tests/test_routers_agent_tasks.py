"""Tests for /stories/{story_id}/agent-tasks endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AgentTask
from app.models import Story, Scene


pytestmark = pytest.mark.asyncio


async def _setup_story_with_task(
    client: AsyncClient,
    db: AsyncSession,
    task_type: str = "grammar_fix",
    status: str = "completed",
    suggestion: str = "Fixed suggestion",
) -> tuple:
    """Helper: create a story + an agent task directly in DB."""
    from uuid import uuid4

    # Create story via API
    resp = await client.post("/stories", json={"title": "Agent Task Story"})
    story_id = resp.json()["id"]

    # Create task directly in DB (bypasses worker)
    task = AgentTask(
        id=str(uuid4()),
        story_id=story_id,
        task_type=task_type,
        status=status,
        suggestion=suggestion,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return story_id, task.id


async def test_list_agent_tasks_empty(client: AsyncClient, db_session: AsyncSession):
    story_resp = await client.post("/stories", json={"title": "Empty Tasks Story"})
    story_id = story_resp.json()["id"]

    resp = await client.get(f"/stories/{story_id}/agent-tasks")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_agent_tasks_story_not_found(client: AsyncClient):
    resp = await client.get("/stories/bad-id/agent-tasks")
    assert resp.status_code == 404


async def test_list_agent_tasks_returns_tasks(client: AsyncClient, db_session: AsyncSession):
    story_id, task_id = await _setup_story_with_task(client, db_session)
    resp = await client.get(f"/stories/{story_id}/agent-tasks")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["id"] == task_id


async def test_list_agent_tasks_filter_by_status(client: AsyncClient, db_session: AsyncSession):
    story_id, _ = await _setup_story_with_task(client, db_session, status="completed")

    # Filter for pending — should be empty
    resp = await client.get(f"/stories/{story_id}/agent-tasks?status=pending")
    assert resp.status_code == 200
    assert resp.json() == []

    # Filter for completed — should have 1
    resp = await client.get(f"/stories/{story_id}/agent-tasks?status=completed")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


async def test_get_agent_task(client: AsyncClient, db_session: AsyncSession):
    story_id, task_id = await _setup_story_with_task(client, db_session)
    resp = await client.get(f"/stories/{story_id}/agent-tasks/{task_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == task_id


async def test_get_agent_task_not_found(client: AsyncClient, db_session: AsyncSession):
    story_resp = await client.post("/stories", json={"title": "X"})
    story_id = story_resp.json()["id"]
    resp = await client.get(f"/stories/{story_id}/agent-tasks/nonexistent")
    assert resp.status_code == 404


async def test_reject_agent_task(client: AsyncClient, db_session: AsyncSession):
    story_id, task_id = await _setup_story_with_task(client, db_session, status="completed")
    resp = await client.put(f"/stories/{story_id}/agent-tasks/{task_id}/reject")
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"


async def test_accept_agent_task_non_grammar(client: AsyncClient, db_session: AsyncSession):
    """Accepting a coherence_check task (no scene) just marks it accepted."""
    story_id, task_id = await _setup_story_with_task(
        client, db_session, task_type="coherence_check", status="completed"
    )
    resp = await client.put(f"/stories/{story_id}/agent-tasks/{task_id}/accept")
    assert resp.status_code == 200
    assert resp.json()["status"] == "accepted"


async def test_accept_grammar_task_applies_suggestion(
    client: AsyncClient, db_session: AsyncSession
):
    """A grammar_fix task with a scene_id and plain-text suggestion updates the scene."""
    from uuid import uuid4

    story_resp = await client.post("/stories", json={"title": "Grammar Story"})
    story_id = story_resp.json()["id"]

    scene = Scene(
        id=str(uuid4()),
        story_id=story_id,
        title="Scene",
        content="Orignal content with typo.",
        scene_type="scene",
        order_index=0,
    )
    db_session.add(scene)
    await db_session.commit()

    task = AgentTask(
        id=str(uuid4()),
        story_id=story_id,
        scene_id=scene.id,
        task_type="grammar_fix",
        status="completed",
        suggestion="Original content without typo.",
    )
    db_session.add(task)
    await db_session.commit()

    resp = await client.put(f"/stories/{story_id}/agent-tasks/{task.id}/accept")
    assert resp.status_code == 200
    assert resp.json()["status"] == "accepted"

    # Scene content should have been updated
    from sqlalchemy import select
    result = await db_session.execute(select(Scene).filter(Scene.id == scene.id))
    updated_scene = result.scalar_one()
    assert updated_scene.content == "Original content without typo."
    assert updated_scene.version == 2


async def test_accept_task_not_found(client: AsyncClient, db_session: AsyncSession):
    story_resp = await client.post("/stories", json={"title": "X"})
    story_id = story_resp.json()["id"]
    resp = await client.put(f"/stories/{story_id}/agent-tasks/bad-id/accept")
    assert resp.status_code == 404
