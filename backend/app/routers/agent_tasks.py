from typing import List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from app.database import get_db
from app.models import AgentTask, Story, Scene
from app.schemas import AgentTaskResponse, AgentTaskUpdate
from app.services.rag_service import RAGService
from datetime import datetime
from uuid import uuid4
import re

router = APIRouter(prefix="/stories/{story_id}/agent-tasks", tags=["agent-tasks"])


@router.get("", response_model=List[AgentTaskResponse])
async def list_agent_tasks(
    story_id: str,
    status: Optional[str] = None,
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
            # Extract corrected text from the grammar suggestion
            match = re.search(r"### ✨ Corrected Scene\s*\n\s*> \*(.*?)\*", task.suggestion, re.DOTALL)
            if match:
                corrected_text = match.group(1).strip()
                scene.content = corrected_text
            else:
                scene.content = task.suggestion
            scene.version += 1
            scene.updated_at = datetime.utcnow()

            # Re-index scene in RAG
            rag_service = RAGService()
            await rag_service.index_scene(scene, db)

    # If this is an idea generation task, create a new scene from the suggestion
    elif task.task_type == "idea_generate" and task.suggestion:
        # Get next scene order index
        max_index_result = await db.execute(
            select(func.max(Scene.order_index)).filter(Scene.story_id == story_id)
        )
        max_index = max_index_result.scalar() or -1
        next_index = max_index + 1

        # Create new scene from the expanded idea
        new_scene = Scene(
            id=str(uuid4()),
            story_id=story_id,
            title="Expanded Scene",
            content=task.suggestion,  # The full expanded content
            scene_type="scene",
            order_index=next_index,
        )
        db.add(new_scene)
        await db.commit()
        await db.refresh(new_scene)

        # Index the new scene in RAG
        rag_service = RAGService()
        await rag_service.index_scene(new_scene, db)

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
