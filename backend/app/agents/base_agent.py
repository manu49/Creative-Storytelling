import json
from abc import ABC, abstractmethod
from typing import Callable, Awaitable
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from anthropic.types.tool_param import ToolParam
from app.models import Scene, Character, AgentTask
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService


class BaseAgent(ABC):
    """Abstract base class for all specialized agents"""

    def __init__(self, llm_service: LLMService, rag_service: RAGService):
        self.llm_service = llm_service
        self.rag_service = rag_service

    @property
    @abstractmethod
    def task_type(self) -> str:
        """Unique task type identifier (e.g., 'grammar_fix')"""
        pass

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """System prompt for this agent"""
        pass

    @property
    @abstractmethod
    def tools(self) -> list[ToolParam]:
        """Tool definitions for this agent"""
        pass

    async def _build_context(self, task: AgentTask, db: AsyncSession) -> dict:
        """Build context for the agent (RAG + scene/character data)"""
        context = {
            "story_id": task.story_id,
            "rag_results": [],
        }

        # Fetch scene if this is a scene-specific task
        if task.scene_id:
            result = await db.execute(
                select(Scene).filter(Scene.id == task.scene_id)
            )
            scene = result.scalar_one_or_none()
            if scene:
                context["scene"] = {
                    "id": scene.id,
                    "title": scene.title,
                    "content": scene.content,
                    "location": scene.location,
                }

                # RAG: retrieve similar scenes for context
                query = f"{scene.title or ''} {scene.content[:200]}"
                rag_results = await self.rag_service.retrieve(
                    query, task.story_id, top_k=3
                )
                context["rag_results"] = rag_results

        return context

    async def _handle_tool_use(
        self, tool_name: str, tool_input: dict
    ) -> str:
        """Handle tool use calls - to be overridden by subclasses"""
        return json.dumps({"status": "success", "input": tool_input})

    async def run(
        self,
        task: AgentTask,
        db: AsyncSession,
        on_chunk: Callable[[str], Awaitable[None]] | None = None,
    ) -> str:
        """
        Run the agent on a task.
        Builds context, calls LLM with tool_use loop, streams chunks if callback provided.
        Returns final suggestion text.
        """
        # Build context
        context = await self._build_context(task, db)

        # Build messages
        messages = [
            {
                "role": "user",
                "content": self._build_user_prompt(task, context),
            }
        ]

        # For streaming generation (without tool_use), yield chunks
        if on_chunk and not self.tools:
            full_text = ""
            async for chunk in self.llm_service.stream_generate(
                system_prompt=self.system_prompt,
                messages=messages,
            ):
                full_text += chunk
                await on_chunk(chunk)
            return full_text

        # For tool_use agents, run the tool loop
        if self.tools:
            response = await self.llm_service.run_tool_loop(
                system_prompt=self.system_prompt,
                messages=messages,
                tools=self.tools,
                tool_handler=self._handle_tool_use,
            )

            # Extract the final suggestion from the response
            suggestion = self._extract_suggestion(response)
            if on_chunk:
                await on_chunk(suggestion)
            return suggestion

        # Fallback
        return "Task completed"

    def _build_user_prompt(self, task: AgentTask, context: dict) -> str:
        """Build the user prompt with context"""
        prompt = f"Task: {task.task_type}\n\n"

        if "scene" in context:
            scene = context["scene"]
            prompt += f"Scene: {scene['title']}\n"
            prompt += f"Location: {scene['location']}\n"
            prompt += f"Content:\n{scene['content']}\n\n"

        if context["rag_results"]:
            prompt += "Related content from story:\n"
            for result in context["rag_results"]:
                prompt += f"- {result[:100]}...\n"

        return prompt

    def _extract_suggestion(self, response) -> str:
        """Extract text suggestion from Claude response"""
        for block in response.content:
            if hasattr(block, "text"):
                return block.text
        return "No suggestion generated"
