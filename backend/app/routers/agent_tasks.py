from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.database import get_db
from app.models import AgentTask, Story, Scene
from app.schemas import AgentTaskResponse, AgentTaskUpdate
from datetime import datetime

router = APIRouter(prefix="/stories/{story_id}/agent-tasks", tags=["agent-tasks"])


@router.get("", response_model=list[AgentTaskResponse])
async def list_agent_tasks(
    story_id: str,
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List agent tasks for a story"""
    # Verify story exists
    story_result = await db.execute(select(Story).filter(Story.id == story_id))
    if not story_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Story not found")

    query = select(AgentTask).filter(AgentTask.story_id == story_id)
    if status:
        query = query.filter(AgentTask.status == status)

    result = await db.execute(query)
    tasks = result.scalars().all()
    return tasks


@router.get("/{task_id}", response_model=AgentTaskResponse)
async def get_agent_task(
    story_id: str,
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific agent task"""
    result = await db.execute(
        select(AgentTask).filter(
            and_(AgentTask.id == task_id, AgentTask.story_id == story_id)
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{task_id}/accept", response_model=AgentTaskResponse)
async def accept_agent_task(
    story_id: str,
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Accept an agent task suggestion"""
    result = await db.execute(
        select(AgentTask).filter(
            and_(AgentTask.id == task_id, AgentTask.story_id == story_id)
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # If this is a grammar fix on a scene, apply the suggestion to scene content
    if task.scene_id and task.task_type == "grammar_fix":
        scene_result = await db.execute(
            select(Scene).filter(Scene.id == task.scene_id)
        )
        scene = scene_result.scalar_one_or_none()
        if scene and task.suggestion:
            # For now, append suggestion as a note (in production, parse and apply)
            scene.content = f"{scene.content}\n\n[Grammar Fix Applied]:\n{task.suggestion}"
            scene.version += 1
            scene.updated_at = datetime.utcnow()

    task.status = "accepted"
    task.completed_at = datetime.utcnow()
    await db.commit()
    await db.refresh(task)

    return task


@router.put("/{task_id}/reject", response_model=AgentTaskResponse)
async def reject_agent_task(
    story_id: str,
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Reject an agent task suggestion"""
    result = await db.execute(
        select(AgentTask).filter(
            and_(AgentTask.id == task_id, AgentTask.story_id == story_id)
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = "rejected"
    await db.commit()
    await db.refresh(task)
    return task
