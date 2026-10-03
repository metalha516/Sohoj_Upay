"""OpenAI client adapter with structured function calling."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from app.ai.llm.client import LLMClient, LLMMessage, LLMResponse, ToolCall

logger = logging.getLogger(__name__)


class OpenAILLMClient(LLMClient):
    """OpenAI API client adapter implementing LLMClient."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o-mini",
    ) -> None:
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model = model

    async def complete(
        self,
        messages: list[LLMMessage],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        """Call OpenAI chat completion API with function calling schemas."""
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not configured.")

        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self.api_key)

        formatted_messages = [m.to_dict() for m in messages]
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = await client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        msg = choice.message

        tool_calls: list[ToolCall] = []
        if msg.tool_calls:
            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except Exception:
                    args = {}
                tool_calls.append(ToolCall(id=tc.id, name=tc.function.name, arguments=args))

        usage = response.usage
        tokens_in = usage.prompt_tokens if usage else 0
        tokens_out = usage.completion_tokens if usage else 0

        return LLMResponse(
            content=msg.content or "",
            tool_calls=tool_calls,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            model=response.model or self.model,
        )
