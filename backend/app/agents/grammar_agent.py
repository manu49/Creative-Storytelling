import json
from typing import List
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
    def model(self) -> str:
        """Use Sonnet for more nuanced grammar analysis"""
        return settings.SONNET_MODEL

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
                if block.name == "apply_grammar_corrections":
                    corrections = block.input.get("corrections", [])
                    if corrections:
                        suggestion_lines.append("Suggested improvements:\n")
                        for corr in corrections:
                            original = corr.get("original", "")
                            replacement = corr.get("replacement", "")
                            reason = corr.get("reason", "")
                            suggestion_lines.append(
                                f"- **{original}** → **{replacement}**\n  Reason: {reason}\n"
                            )
                    else:
                        suggestion_lines.append("No significant grammar issues found.\n")

        if len(suggestion_lines) == 1:
            suggestion_lines.append("Analysis complete.\n")

        return "\n".join(suggestion_lines)
