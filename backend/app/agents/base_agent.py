import json
from abc import ABC, abstractmethod
from typing import Callable, Awaitable, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from anthropic.types.tool_param import ToolParam
from app.models import Scene, Character, AgentTask
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService
from app.config import get_settings

settings = get_settings()


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
    def tools(self) -> List[ToolParam]:
        """Tool definitions for this agent"""
        pass

    @property
    def model(self) -> str:
        """Model to use for this agent. Override in subclasses for specific models."""
        return settings.SONNET_MODEL

    async def _build_context(self, task: AgentTask, db: AsyncSession) -> dict:
        """Build context for the agent (RAG + scene/character data)"""
        context = {
            "story_id": task.story_id,
            "rag_results": [],
            "scenes": [],
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
                context["rag_results"] = rag_results if rag_results else []
        else:
            # For story-wide tasks (like coherence_check), fetch all scenes
            result = await db.execute(
                select(Scene).filter(Scene.story_id == task.story_id)
            )
            scenes = result.scalars().all()
            context["scenes"] = [
                {
                    "id": s.id,
                    "title": s.title,
                    "content": s.content,
                    "location": s.location,
                }
                for s in scenes
            ]

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
        on_chunk: Callable[[str], Awaitable[None]]
    ) -> str:
        """
        Run the agent on a task.
        Builds context, calls LLM with tool_use loop, streams chunks if callback provided.
        Returns final suggestion text.
        """
        try:
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
                    model=self.model,
                )

                # Extract the final suggestion from the response
                suggestion = self._extract_suggestion(response)
                if on_chunk:
                    await on_chunk(suggestion)
                return suggestion

            # Fallback
            return "Task completed"
        except IndexError as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"❌ IndexError in {self.task_type}: {e}\n{error_details}")
            raise
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"❌ Error in {self.task_type}: {e}\n{error_details}")
            raise

    @staticmethod
    def _extract_idea_text(input_context: Optional[str]) -> str:
        """Pull the writer's raw idea text out of a task's input_context.

        The ideas router stores the request body (e.g.
        ``{"raw_text": "...", "source_type": "text"}``). Older rows were saved
        with ``str(dict)`` (Python repr) and newer ones with ``json.dumps``, so
        try JSON first and fall back to ``ast.literal_eval`` before treating the
        value as a plain string.
        """
        if not input_context:
            return ""

        parsed = None
        try:
            parsed = json.loads(input_context)
        except (ValueError, TypeError):
            try:
                import ast

                parsed = ast.literal_eval(input_context)
            except (ValueError, SyntaxError):
                parsed = None

        if isinstance(parsed, dict):
            return str(parsed.get("raw_text") or parsed.get("text") or "").strip()
        return str(input_context).strip()

    def _build_user_prompt(self, task: AgentTask, context: dict) -> str:
        """Build the user prompt with context"""
        prompt = f"Task: {task.task_type}\n\n"

        # Include the writer's raw idea (e.g. a dumped scene) so generation
        # agents actually develop the story around the user's input.
        idea_text = self._extract_idea_text(getattr(task, "input_context", None))
        if idea_text:
            prompt += f"Raw idea to develop into a full scene:\n{idea_text}\n\n"

        if "scene" in context:
            scene = context["scene"]
            prompt += f"Scene: {scene['title']}\n"
            prompt += f"Location: {scene['location']}\n"
            prompt += f"Content:\n{scene['content']}\n\n"
        elif context.get("scenes"):
            # For story-wide tasks, include all scenes
            prompt += "Story Scenes:\n\n"
            for scene in context["scenes"]:
                prompt += f"**{scene['title']}**\n"
                if scene["location"]:
                    prompt += f"Location: {scene['location']}\n"
                prompt += f"{scene['content']}\n\n"

        if context.get("rag_results"):
            prompt += "Related content from story:\n"
            for result in context["rag_results"]:
                if result and len(result) > 0:
                    prompt += f"- {result[:100]}...\n"

        return prompt

    def _extract_suggestion(self, response) -> str:
        """Extract text suggestion from Claude response"""
        for block in response.content:
            if hasattr(block, "text"):
                return block.text
        return "No suggestion generated"
