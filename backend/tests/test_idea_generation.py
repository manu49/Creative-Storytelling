"""Regression tests for idea → scene generation (the "dump a raw idea" flow).

These guard the bug where a writer's dumped idea (e.g. a scene about Mehfil &
Sartaj) was stored on the AgentTask but never surfaced in the prompt sent to
Claude, so the SceneExpandAgent generated content unrelated to the input.
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.agents.scene_expand_agent import SceneExpandAgent
from app.models import AgentTask


pytestmark = pytest.mark.asyncio


MEHFIL_SARTAJ_SCENE = (
    "Many years passed since Mehfil and Sartaj separated. One day Mehfil was "
    "sitting among a group of old friends and they were playing never have I "
    'ever. Mehfil said "I have never been in love." People mocked her saying '
    "it's impossible for a person of her age. Mehfil replied, \"There's "
    'difference between love and madness." The room went silent.'
)


def _idea_task(input_context):
    task = MagicMock(spec=AgentTask)
    task.task_type = "idea_generate"
    task.story_id = "story-1"
    task.scene_id = None
    task.input_context = input_context
    return task


# ---------------------------------------------------------------------------
# The writer's idea text must reach the model prompt
# ---------------------------------------------------------------------------

def test_dumped_idea_appears_in_prompt(mock_llm_service, mock_rag_service):
    """The raw scene the user typed must be in the prompt sent to Claude."""
    agent = SceneExpandAgent(mock_llm_service, mock_rag_service)
    # Matches what routers/ideas.py stores (json.dumps of the request body).
    task = _idea_task(json.dumps({"raw_text": MEHFIL_SARTAJ_SCENE, "source_type": "text"}))
    context = {"story_id": "story-1", "scenes": [], "rag_results": []}

    prompt = agent._build_user_prompt(task, context)

    assert "Mehfil" in prompt
    assert "Sartaj" in prompt
    assert "never have I ever" in prompt


def test_dumped_idea_legacy_repr_format(mock_llm_service, mock_rag_service):
    """Older rows stored input_context via str(dict) — must still be parsed."""
    agent = SceneExpandAgent(mock_llm_service, mock_rag_service)
    task = _idea_task(str({"raw_text": MEHFIL_SARTAJ_SCENE, "source_type": "text"}))
    context = {"story_id": "story-1", "scenes": [], "rag_results": []}

    prompt = agent._build_user_prompt(task, context)

    assert "Mehfil" in prompt and "Sartaj" in prompt


def test_plain_string_input_context(mock_llm_service, mock_rag_service):
    """A bare (non-dict) input_context should be passed through as-is."""
    agent = SceneExpandAgent(mock_llm_service, mock_rag_service)
    task = _idea_task("A lone lighthouse keeper hears knocking from the sea.")
    context = {"story_id": "story-1", "scenes": [], "rag_results": []}

    prompt = agent._build_user_prompt(task, context)

    assert "lighthouse keeper" in prompt


def test_no_input_context_is_safe(mock_llm_service, mock_rag_service):
    """Tasks without input_context (grammar/coherence) must not break."""
    agent = SceneExpandAgent(mock_llm_service, mock_rag_service)
    task = _idea_task(None)
    context = {"story_id": "story-1", "scenes": [], "rag_results": []}

    prompt = agent._build_user_prompt(task, context)

    assert "idea_generate" in prompt  # builds without raising


# ---------------------------------------------------------------------------
# _extract_suggestion prefers the structured scene over a text preamble
# ---------------------------------------------------------------------------

def test_extract_suggestion_prefers_tool_output(mock_llm_service, mock_rag_service):
    """A leading text preamble must not shadow the expand_scene tool output."""
    agent = SceneExpandAgent(mock_llm_service, mock_rag_service)

    preamble = MagicMock()
    preamble.type = "text"
    preamble.text = "Sure! Here is the expanded scene:"

    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.name = "expand_scene"
    tool_block.input = {
        "expanded_content": "Mehfil set down her glass as the room fell silent.",
        "suggested_dialogue": ["There's a difference between love and madness."],
        "scene_notes": "Bittersweet, reflective tone.",
    }

    response = MagicMock()
    response.content = [preamble, tool_block]

    result = agent._extract_suggestion(response)

    assert "Mehfil set down her glass" in result
    assert "Key Dialogue" in result
    assert "love and madness" in result
    assert "Sure! Here is" not in result


def test_extract_suggestion_text_fallback(mock_llm_service, mock_rag_service):
    """If the model returns only text (no tool call), use that text."""
    agent = SceneExpandAgent(mock_llm_service, mock_rag_service)
    block = MagicMock()
    block.type = "text"
    block.text = "A fully written scene about Mehfil and Sartaj."
    response = MagicMock()
    response.content = [block]

    assert agent._extract_suggestion(response) == "A fully written scene about Mehfil and Sartaj."


# ---------------------------------------------------------------------------
# End-to-end through the ideas router → an idea_generate task is enqueued
# ---------------------------------------------------------------------------

async def test_dump_idea_route_persists_scene_text(client):
    """POSTing the scene creates an idea_generate task whose stored context
    round-trips back to the original Mehfil & Sartaj text."""
    story_resp = await client.post("/stories", json={"title": "Mehfil & Sartaj"})
    assert story_resp.status_code == 201
    story_id = story_resp.json()["id"]

    resp = await client.post(
        f"/stories/{story_id}/ideas",
        json={"raw_text": MEHFIL_SARTAJ_SCENE, "source_type": "text"},
    )
    assert resp.status_code == 201
    task = resp.json()
    assert task["task_type"] == "idea_generate"
    assert task["status"] == "pending"

    # The stored input_context must round-trip to the original scene text,
    # which is what the agent now reads when building the prompt.
    recovered = SceneExpandAgent._extract_idea_text(task.get("input_context"))
    assert "Mehfil" in recovered and "Sartaj" in recovered
