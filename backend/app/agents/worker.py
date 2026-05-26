import asyncio
import json
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.models import AgentTask
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService
from app.ws.manager import connection_manager
from app.config import get_settings
from app.agents.grammar_agent import GrammarAgent
from app.agents.coherence_agent import CoherenceAgent
from app.agents.character_agent import CharacterAgent
from app.agents.scene_expand_agent import SceneExpandAgent
from app.database import AsyncSessionLocal

settings = get_settings()


class AgentWorker:
    """Background worker that polls task queue and dispatches agents"""

    def __init__(self):
        self.llm_service = LLMService()
        self.rag_service = RAGService()

        # Agent instances
        self.agents = {
            "grammar_fix": GrammarAgent(self.llm_service, self.rag_service),
            "coherence_check": CoherenceAgent(self.llm_service, self.rag_service),
            "character_arc": CharacterAgent(self.llm_service, self.rag_service),
            "idea_generate": SceneExpandAgent(self.llm_service, self.rag_service),
        }

    async def run(self) -> None:
        """Main worker loop - continuously polls for tasks"""
        print("🤖 Agent worker started")
        semaphore = asyncio.Semaphore(settings.AGENT_MAX_CONCURRENT_TASKS)

        try:
            while True:
                # Fetch pending tasks
                async with AsyncSessionLocal() as db:
                    pending_tasks = await self._fetch_pending_tasks(db)

                # Dispatch tasks with concurrency control
                for task in pending_tasks:
                    asyncio.create_task(
                        self._process_with_semaphore(semaphore, task)
                    )

                # Poll interval
                await asyncio.sleep(settings.AGENT_POLL_INTERVAL_SECONDS)

        except asyncio.CancelledError:
            print("🛑 Agent worker stopped")
        except Exception as e:
            print(f"❌ Agent worker error: {e}")

    async def _fetch_pending_tasks(self, db: AsyncSession, limit: int = 2):
        """Fetch pending tasks ordered by priority"""
        result = await db.execute(
            select(AgentTask)
            .filter(AgentTask.status == "pending")
            .order_by(AgentTask.priority.asc(), AgentTask.created_at.asc())
            .limit(limit)
        )
        return result.scalars().all()

    async def _process_with_semaphore(self, semaphore, task: AgentTask) -> None:
        """Process task with concurrency control"""
        async with semaphore:
            await self._process_task(task)

    async def _process_task(self, task: AgentTask) -> None:
        """Process a single agent task"""
        async with AsyncSessionLocal() as db:
            try:
                # Mark as running
                task.status = "running"
                await db.merge(task)
                await db.commit()

                # Broadcast task started
                await connection_manager.broadcast_to_story(
                    task.story_id,
                    {
                        "type": "agent:task_started",
                        "task_id": task.id,
                        "task_type": task.task_type,
                    },
                )

                # Get agent
                agent = self.agents.get(task.task_type)
                if not agent:
                    raise ValueError(f"Unknown task type: {task.task_type}")

                # Define chunk callback for streaming
                async def on_chunk(text: str):
                    await connection_manager.broadcast_to_story(
                        task.story_id,
                        {
                            "type": "agent:chunk",
                            "task_id": task.id,
                            "text": text,
                        },
                    )

                # Run agent
                suggestion = await agent.run(task, db, on_chunk=on_chunk)

                # Mark as completed
                task.status = "completed"
                task.suggestion = suggestion
                task.completed_at = datetime.utcnow()
                await db.merge(task)
                await db.commit()

                # Broadcast task done
                await connection_manager.broadcast_to_story(
                    task.story_id,
                    {
                        "type": "agent:task_done",
                        "task_id": task.id,
                        "suggestion": suggestion,
                    },
                )

                print(f"✅ Task {task.id} ({task.task_type}) completed")

            except Exception as e:
                print(f"❌ Task {task.id} failed: {e}")
                # Mark as failed
                task.status = "failed"
                task.error_message = str(e)
                await db.merge(task)
                await db.commit()

                # Broadcast error
                await connection_manager.broadcast_to_story(
                    task.story_id,
                    {
                        "type": "agent:task_failed",
                        "task_id": task.id,
                        "error": str(e),
                    },
                )


# Global worker instance
agent_worker = AgentWorker()
