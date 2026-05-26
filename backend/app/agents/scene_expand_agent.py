import json
from typing import List
from app.agents.base_agent import BaseAgent
from app.tools.story_tools import SCENE_EXPAND_TOOLS
from anthropic.types.tool_param import ToolParam
from app.config import get_settings

settings = get_settings()


class SceneExpandAgent(BaseAgent):
    """Agent for expanding raw ideas into full scene drafts"""

    @property
    def task_type(self) -> str:
        return "idea_generate"

    @property
    def model(self) -> str:
        """Use Sonnet for creative scene generation"""
        return settings.SONNET_MODEL

    @property
    def system_prompt(self) -> str:
        return """You are a creative screenwriter and novelist helping develop story ideas into full scenes.
Your task is to transform a raw idea or outline into a compelling, fully-formed scene.

Use the expand_scene tool to provide:
1. Complete scene content in narrative form
2. Key dialogue lines that bring the scene to life
3. Notes on setting, mood, pacing, and character arcs involved

Write scenes that are:
- Vivid and engaging
- Consistent with the story's tone and setting
- Focused on character development and plot advancement
- Include sensory details and emotional depth

Remember to maintain narrative continuity with the existing story."""

    @property
    def tools(self) -> List[ToolParam]:
        return SCENE_EXPAND_TOOLS

    async def _handle_tool_use(self, tool_name: str, tool_input: dict) -> str:
        """Handle scene expansion"""
        if tool_name == "expand_scene":
            content = tool_input.get("expanded_content", "")
            dialogue = tool_input.get("suggested_dialogue", [])
            notes = tool_input.get("scene_notes", "")

            return json.dumps({
                "status": "success",
                "content_length": len(content),
                "dialogue_count": len(dialogue),
                "expanded_content": content,
                "suggested_dialogue": dialogue,
                "scene_notes": notes,
            })
        return json.dumps({"status": "error", "message": f"Unknown tool: {tool_name}"})

    def _extract_suggestion(self, response) -> str:
        """Extract the expanded scene content"""
        for block in response.content:
            if hasattr(block, "text"):
                return block.text
            elif hasattr(block, "type") and block.type == "tool_use":
                if block.name == "expand_scene":
                    content = block.input.get("expanded_content", "")
                    dialogue = block.input.get("suggested_dialogue", [])
                    notes = block.input.get("scene_notes", "")

                    result = content + "\n"
                    if dialogue:
                        result += "\n### Key Dialogue:\n"
                        for line in dialogue:
                            result += f"- {line}\n"
                    if notes:
                        result += f"\n### Notes:\n{notes}\n"
                    return result

        return "Scene generation failed"
