from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Story, Scene, Character, AgentTask
from uuid import uuid4
from datetime import datetime


class StoryManager:
    """Manager for story operations and task enqueueing"""

    @staticmethod
    async def enqueue_task(
        db: AsyncSession,
        story_id: str,
        task_type: str,
        priority: int = 5,
        scene_id: str | None = None,
        input_context: dict | None = None,
    ) -> AgentTask:
        """
        Enqueue an agent task. Deduplicates pending tasks of the same type.
        """
        # Check if a pending task of same type already exists
        if scene_id:
            result = await db.execute(
                select(AgentTask).filter(
                    AgentTask.story_id == story_id,
                    AgentTask.scene_id == scene_id,
                    AgentTask.task_type == task_type,
                    AgentTask.status == "pending",
                )
            )
            existing = result.scalar_one_or_none()
            if existing:
                # Update existing task to bump priority
                existing.updated_at = datetime.utcnow()
                await db.commit()
                await db.refresh(existing)
                return existing

        # Create new task
        task = AgentTask(
            id=str(uuid4()),
            story_id=story_id,
            scene_id=scene_id,
            task_type=task_type,
            status="pending",
            priority=priority,
            input_context=str(input_context) if input_context else None,
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)
        return task

    @staticmethod
    async def enqueue_scene_tasks(
        db: AsyncSession,
        story_id: str,
        scene_id: str,
    ) -> tuple[AgentTask, AgentTask]:
        """Enqueue grammar fix and coherence check for a scene"""
        grammar_task = await StoryManager.enqueue_task(
            db,
            story_id=story_id,
            task_type="grammar_fix",
            priority=3,
            scene_id=scene_id,
        )

        coherence_task = await StoryManager.enqueue_task(
            db,
            story_id=story_id,
            task_type="coherence_check",
            priority=5,
            scene_id=None,  # Story-wide task
        )

        return grammar_task, coherence_task

    @staticmethod
    async def enqueue_character_task(
        db: AsyncSession,
        story_id: str,
        character_id: str,
    ) -> AgentTask:
        """Enqueue character arc analysis"""
        return await StoryManager.enqueue_task(
            db,
            story_id=story_id,
            task_type="character_arc",
            priority=7,
            scene_id=None,
        )
