import json
from app.agents.base_agent import BaseAgent
from app.tools.story_tools import GRAMMAR_TOOLS
from anthropic.types.tool_param import ToolParam
from app.config import get_settings

settings = get_settings()


class GrammarAgent(BaseAgent):
    """Agent for grammar and style corrections"""

    @property
    def task_type(self) -> str:
        return "grammar_fix"

    @property
    def system_prompt(self) -> str:
        return """You are a professional copyeditor specializing in creative writing.
Your task is to identify and suggest grammar, spelling, style, and clarity improvements.

Review the scene content carefully and use the apply_grammar_corrections tool to suggest specific fixes.
Be respectful and maintain the author's voice while improving clarity and correctness.
Focus on:
- Grammar and syntax errors
- Spelling mistakes
- Punctuation issues
- Style consistency
- Clarity and readability

Only suggest meaningful improvements, not nitpicky changes."""

    @property
    def tools(self) -> List[ToolParam]:
        return GRAMMAR_TOOLS

    async def _handle_tool_use(self, tool_name: str, tool_input: dict) -> str:
        """Handle grammar corrections tool call"""
        if tool_name == "apply_grammar_corrections":
            corrections = tool_input.get("corrections", [])
            return json.dumps({
                "status": "success",
                "corrections_count": len(corrections),
                "corrections": corrections,
            })
        return json.dumps({"status": "error", "message": f"Unknown tool: {tool_name}"})

    def _extract_suggestion(self, response) -> str:
        """Extract formatted suggestion from grammar corrections"""
        for block in response.content:
            if hasattr(block, "text"):
                return block.text

        # Try to extract from tool use
        suggestion_lines = ["## Grammar & Style Corrections\n"]
        for block in response.content:
            if hasattr(block, "type") and block.type == "tool_use":
                # The tool was called, format the corrections nicely
                suggestion_lines.append("Suggested improvements:\n")

        return "\n".join(suggestion_lines)
