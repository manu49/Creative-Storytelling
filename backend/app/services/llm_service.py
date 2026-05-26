from anthropic import AsyncAnthropic
from anthropic.types.message import Message
from anthropic.types.tool_param import ToolParam
from app.config import get_settings
from typing import AsyncIterator, Callable, Awaitable

settings = get_settings()

# Static system prefix with caching for cost/latency reduction
SYSTEM_PREFIX = """You are a creative writing assistant helping writers improve their stories.
Your role is to provide constructive feedback and suggestions that enhance narrative quality.
Always be respectful and encouraging while maintaining high writing standards.
Output only the requested information in the exact format specified."""


class LLMService:
    """Service for LLM interactions via Claude API"""

    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def stream_generate(
        self,
        system_prompt: str,
        messages: list[dict],
        tools: list[ToolParam] | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        """
        Stream-based generation. Yields text deltas.
        System prompt gets cache_control for cost savings.
        """
        if model is None:
            model = settings.SONNET_MODEL

        async with self.client.messages.stream(
            model=model,
            max_tokens=max_tokens,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PREFIX,
                    "cache_control": {"type": "ephemeral"},
                },
                {"type": "text", "text": system_prompt},
            ],
            messages=messages,
            tools=tools or [],
        ) as stream:
            async for text in stream.text_stream:
                yield text

    async def run_tool_loop(
        self,
        system_prompt: str,
        messages: list[dict],
        tools: list[ToolParam],
        tool_handler: Callable[[str, dict], Awaitable[str]],
        model: str | None = None,
        max_iterations: int = 5,
    ) -> Message:
        """
        Agentic tool-use loop.
        Calls Claude with tools, extracts tool_use blocks, calls handler,
        appends results, repeats until end_turn or max_iterations.
        Returns final Message.
        """
        if model is None:
            model = settings.HAIKU_MODEL

        iteration = 0
        while iteration < max_iterations:
            iteration += 1

            response = await self.client.messages.create(
                model=model,
                max_tokens=4096,
                system=[
                    {
                        "type": "text",
                        "text": SYSTEM_PREFIX,
                        "cache_control": {"type": "ephemeral"},
                    },
                    {"type": "text", "text": system_prompt},
                ],
                messages=messages,
                tools=tools,
            )

            # Check stop reason
            if response.stop_reason == "end_turn":
                return response

            # Process tool uses
            tool_uses_found = False
            for content_block in response.content:
                if content_block.type == "tool_use":
                    tool_uses_found = True
                    tool_name = content_block.name
                    tool_input = content_block.input
                    tool_use_id = content_block.id

                    # Call the tool handler
                    tool_result = await tool_handler(tool_name, tool_input)

                    # Append assistant message with tool use
                    messages.append({"role": "assistant", "content": response.content})

                    # Append tool result
                    messages.append(
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": tool_use_id,
                                    "content": tool_result,
                                }
                            ],
                        }
                    )

            if not tool_uses_found:
                # No more tool uses, exit loop
                return response

        # Max iterations reached
        return response
