from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.database import get_db
from app.models import AgentTask, Story
from app.schemas import AgentTaskResponse, AgentTaskUpdate

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

    task.status = "accepted"
    await db.commit()
    await db.refresh(task)

    # TODO: Apply suggestion to scene if scene_id exists

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
