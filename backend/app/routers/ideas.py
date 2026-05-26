from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Story, AgentTask
from app.schemas import AgentTaskResponse
from uuid import uuid4

router = APIRouter(prefix="/stories/{story_id}/ideas", tags=["ideas"])


@router.post("", response_model=AgentTaskResponse, status_code=201)
async def dump_idea(
    story_id: str,
    data: dict,
    db: AsyncSession = Depends(get_db),
):
    """Dump a raw creative idea - triggers scene expansion task"""
    # Verify story exists
    story_result = await db.execute(select(Story).filter(Story.id == story_id))
    if not story_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Story not found")

    # Create agent task for idea generation (highest priority)
    task = AgentTask(
        id=str(uuid4()),
        story_id=story_id,
        task_type="idea_generate",
        status="pending",
        priority=1,  # Highest priority
        input_context=str(data),
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task
