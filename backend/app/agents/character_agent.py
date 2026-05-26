import json
from typing import List
from app.agents.base_agent import BaseAgent
from app.tools.story_tools import CHARACTER_TOOLS
from anthropic.types.tool_param import ToolParam
from app.config import get_settings

settings = get_settings()


class CharacterAgent(BaseAgent):
    """Agent for character consistency and arc development"""

    @property
    def task_type(self) -> str:
        return "character_arc"

    @property
    def model(self) -> str:
        """Use Sonnet for nuanced character analysis"""
        return settings.SONNET_MODEL

    @property
    def system_prompt(self) -> str:
        return """You are a character development specialist.
Your task is to analyze character arcs and consistency across the story.

Use the update_character_arc tool to:
- Summarize the character's development throughout the story
- Flag any inconsistencies in behavior, motivation, or characterization
- Suggest ways to strengthen the character arc
- Ensure character development aligns with plot events

Focus on character authenticity and growth."""

    @property
    def tools(self) -> List[ToolParam]:
        return CHARACTER_TOOLS

    async def _handle_tool_use(self, tool_name: str, tool_input: dict) -> str:
        """Handle character arc analysis"""
        if tool_name == "update_character_arc":
            arc_notes = tool_input.get("arc_notes", "")
            inconsistencies = tool_input.get("inconsistencies", [])
            suggestions = tool_input.get("development_suggestions", [])

            return json.dumps({
                "status": "success",
                "arc_notes": arc_notes,
                "inconsistencies_count": len(inconsistencies),
                "suggestions_count": len(suggestions),
                "data": {
                    "arc_notes": arc_notes,
                    "inconsistencies": inconsistencies,
                    "suggestions": suggestions,
                }
            })
        return json.dumps({"status": "error", "message": f"Unknown tool: {tool_name}"})

    def _extract_suggestion(self, response) -> str:
        """Extract formatted suggestion from character analysis"""
        suggestion_lines = ["## Character Arc Analysis\n"]

        for block in response.content:
            if hasattr(block, "text"):
                suggestion_lines.append(block.text)
            elif hasattr(block, "type") and block.type == "tool_use":
                if block.name == "update_character_arc":
                    arc_notes = block.input.get("arc_notes", "")
                    inconsistencies = block.input.get("inconsistencies", [])
                    suggestions = block.input.get("development_suggestions", [])

                    if arc_notes:
                        suggestion_lines.append(f"\n### Arc Development:\n{arc_notes}\n")
                    if inconsistencies:
                        suggestion_lines.append("\n### Inconsistencies Found:\n")
                        for inconsistency in inconsistencies:
                            suggestion_lines.append(f"- {inconsistency}\n")
                    if suggestions:
                        suggestion_lines.append("\n### Development Suggestions:\n")
                        for suggestion in suggestions:
                            suggestion_lines.append(f"- {suggestion}\n")

        if len(suggestion_lines) == 1:
            suggestion_lines.append("Analysis complete.\n")

        return "\n".join(suggestion_lines)
