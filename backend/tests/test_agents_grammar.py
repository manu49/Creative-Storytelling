"""Tests for GrammarAgent."""
import json
import pytest
from unittest.mock import MagicMock

from app.agents.grammar_agent import GrammarAgent


pytestmark = pytest.mark.asyncio


@pytest.fixture()
def agent(mock_llm_service, mock_rag_service):
    return GrammarAgent(mock_llm_service, mock_rag_service)


def test_task_type(agent):
    assert agent.task_type == "grammar_fix"


def test_tools_defined(agent):
    assert len(agent.tools) > 0
    tool_names = [t["name"] for t in agent.tools]
    assert "apply_grammar_corrections" in tool_names


async def test_handle_tool_use_known_tool(agent):
    tool_input = {
        "corrections": [
            {"original": "teh", "replacement": "the", "reason": "Typo"}
        ]
    }
    result = await agent._handle_tool_use("apply_grammar_corrections", tool_input)
    parsed = json.loads(result)
    assert parsed["status"] == "success"
    assert parsed["corrections_count"] == 1


async def test_handle_tool_use_unknown_tool(agent):
    result = await agent._handle_tool_use("nonexistent_tool", {})
    parsed = json.loads(result)
    assert parsed["status"] == "error"


async def test_handle_tool_use_empty_corrections(agent):
    result = await agent._handle_tool_use("apply_grammar_corrections", {"corrections": []})
    parsed = json.loads(result)
    assert parsed["corrections_count"] == 0


def test_extract_suggestion_from_text_block(agent):
    block = MagicMock()
    block.text = "### Corrections\nFound 2 issues."
    response = MagicMock()
    response.content = [block]
    assert agent._extract_suggestion(response) == "### Corrections\nFound 2 issues."


def test_extract_suggestion_from_tool_use_block(agent):
    """When no text block exists, format the tool_use block into a markdown suggestion."""
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.name = "apply_grammar_corrections"
    tool_block.input = {
        "corrections": [
            {"original": "He run", "replacement": "He ran", "reason": "Subject-verb agreement"}
        ]
    }
    # Remove .text attribute so hasattr returns False
    del tool_block.text

    response = MagicMock()
    response.content = [tool_block]

    result = agent._extract_suggestion(response)
    assert "Grammar" in result
    assert "He run" in result
    assert "He ran" in result


def test_extract_suggestion_empty_corrections(agent):
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.name = "apply_grammar_corrections"
    tool_block.input = {"corrections": []}
    del tool_block.text

    response = MagicMock()
    response.content = [tool_block]

    result = agent._extract_suggestion(response)
    assert "No significant grammar issues found" in result
