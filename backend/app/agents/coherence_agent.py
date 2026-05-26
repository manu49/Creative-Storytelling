import json
from app.agents.base_agent import BaseAgent
from app.tools.story_tools import COHERENCE_TOOLS
from anthropic.types.tool_param import ToolParam
from app.config import get_settings

settings = get_settings()


class CoherenceAgent(BaseAgent):
    """Agent for narrative coherence and consistency analysis"""

    @property
    def task_type(self) -> str:
        return "coherence_check"

    @property
    def system_prompt(self) -> str:
        return """You are a story editor specializing in narrative structure and coherence.
Your task is to analyze the story for issues with:
- Pacing and narrative flow
- Plot consistency and logical gaps
- Character consistency with established arcs
- Tone and voice consistency
- Timeline and world-building consistency

Use the flag_coherence_issues tool to report issues with severity levels.
Provide constructive suggestions for improvement."""

    @property
    def tools(self) -> List[ToolParam]:
        return COHERENCE_TOOLS

    async def _handle_tool_use(self, tool_name: str, tool_input: dict) -> str:
        """Handle coherence issues flagging"""
        if tool_name == "flag_coherence_issues":
            issues = tool_input.get("issues", [])
            # Count by severity
            severity_counts = {"low": 0, "medium": 0, "high": 0}
            for issue in issues:
                severity = issue.get("severity", "low")
                if severity in severity_counts:
                    severity_counts[severity] += 1

            return json.dumps({
                "status": "success",
                "total_issues": len(issues),
                "severity_counts": severity_counts,
                "issues": issues,
            })
        return json.dumps({"status": "error", "message": f"Unknown tool: {tool_name}"})

    def _extract_suggestion(self, response) -> str:
        """Extract formatted suggestion from coherence analysis"""
        suggestion_lines = ["## Narrative Coherence Analysis\n"]

        for block in response.content:
            if hasattr(block, "text"):
                suggestion_lines.append(block.text)

        return "\n".join(suggestion_lines)
