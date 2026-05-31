"""Tests for LLMService — tool loop logic with mocked Anthropic client."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


pytestmark = pytest.mark.asyncio


def _make_llm_service():
    from app.services.llm_service import LLMService
    with patch("app.services.llm_service.AsyncAnthropic"):
        return LLMService()


def _make_message(stop_reason: str, tool_uses=None):
    """Build a fake Anthropic Message-like object."""
    msg = MagicMock()
    msg.stop_reason = stop_reason
    blocks = []
    if tool_uses:
        for name, input_data, use_id in tool_uses:
            block = MagicMock()
            block.type = "tool_use"
            block.name = name
            block.input = input_data
            block.id = use_id
            blocks.append(block)
    msg.content = blocks
    return msg


async def test_run_tool_loop_end_turn_immediately():
    """If the first response is end_turn, return it immediately."""
    service = _make_llm_service()
    end_msg = _make_message("end_turn")
    service.client.messages.create = AsyncMock(return_value=end_msg)

    tool_handler = AsyncMock(return_value='{"status": "ok"}')
    result = await service.run_tool_loop(
        system_prompt="sys",
        messages=[{"role": "user", "content": "Hello"}],
        tools=[],
        tool_handler=tool_handler,
    )
    assert result is end_msg
    tool_handler.assert_not_called()


async def test_run_tool_loop_calls_tool_handler():
    """A tool_use response triggers tool_handler, then loop continues."""
    service = _make_llm_service()

    tool_msg = _make_message("tool_use", [("my_tool", {"key": "val"}, "tool-use-1")])
    end_msg = _make_message("end_turn")
    service.client.messages.create = AsyncMock(side_effect=[tool_msg, end_msg])

    tool_handler = AsyncMock(return_value='{"result": "done"}')

    messages = [{"role": "user", "content": "Do the tool"}]
    result = await service.run_tool_loop(
        system_prompt="sys",
        messages=messages,
        tools=[],
        tool_handler=tool_handler,
    )

    tool_handler.assert_called_once_with("my_tool", {"key": "val"})
    # messages should have grown: original + assistant + tool_result
    assert len(messages) == 3
    assert result is end_msg


async def test_run_tool_loop_max_iterations():
    """Loop exits after max_iterations even without end_turn."""
    service = _make_llm_service()

    # Always respond with a tool_use
    tool_msg = _make_message("tool_use", [("t", {}, "id-1")])
    service.client.messages.create = AsyncMock(return_value=tool_msg)
    tool_handler = AsyncMock(return_value='{}')

    result = await service.run_tool_loop(
        system_prompt="sys",
        messages=[{"role": "user", "content": "loop"}],
        tools=[],
        tool_handler=tool_handler,
        max_iterations=3,
    )
    # Should have been called exactly max_iterations times
    assert service.client.messages.create.call_count == 3
    assert result is tool_msg


async def test_run_tool_loop_no_tool_uses_exits():
    """If stop_reason is not end_turn but there are no tool_use blocks, exit."""
    service = _make_llm_service()

    empty_msg = _make_message("stop_sequence")  # no tool_use blocks
    service.client.messages.create = AsyncMock(return_value=empty_msg)
    tool_handler = AsyncMock()

    result = await service.run_tool_loop(
        system_prompt="sys",
        messages=[{"role": "user", "content": "x"}],
        tools=[],
        tool_handler=tool_handler,
    )
    assert result is empty_msg
    tool_handler.assert_not_called()
    assert service.client.messages.create.call_count == 1
