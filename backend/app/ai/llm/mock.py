"""Mock language model client for deterministic testing and adversarial fuzzing."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any

from app.ai.llm.client import LLMClient, LLMMessage, LLMResponse, ToolCall


class MockLLM(LLMClient):
    """Deterministic LLM client for tests that replays pre-scripted responses."""

    def __init__(
        self,
        scripted_responses: list[
            LLMResponse | Exception | Callable[[list[LLMMessage]], LLMResponse]
        ]
        | None = None,
    ) -> None:
        self.scripted_responses: list[
            LLMResponse | Exception | Callable[[list[LLMMessage]], LLMResponse]
        ] = list(scripted_responses) if scripted_responses is not None else []
        self.call_history: list[dict[str, Any]] = []
        self._current_index = 0

    @property
    def recorded_calls(self) -> list[dict[str, Any]]:
        """Alias for call_history for test ergonomics."""
        return self.call_history

    @classmethod
    def with_tool_then_answer(
        cls,
        tool_name: str,
        tool_args: dict[str, Any],
        answer: str = "",
        final_answer: str = "",
    ) -> MockLLM:
        """Helper to create a 2-turn sequence: first calls a tool, then generates final answer."""
        actual_answer = final_answer if final_answer else answer
        tool_call_id = f"call_{uuid.uuid4().hex[:8]}"
        step1 = LLMResponse(
            content="",
            tool_calls=[ToolCall(id=tool_call_id, name=tool_name, arguments=tool_args)],
            tokens_in=100,
            tokens_out=25,
            model="mock-gpt4o",
        )
        step2 = LLMResponse(
            content=actual_answer,
            tool_calls=[],
            tokens_in=200,
            tokens_out=60,
            model="mock-gpt4o",
        )
        return cls([step1, step2])

    @classmethod
    def single_answer(cls, answer: str) -> MockLLM:
        """Helper to create a single direct answer without tool calls."""
        return cls([LLMResponse(content=answer, tool_calls=[], tokens_in=50, tokens_out=30)])

    async def chat_completion(
        self,
        messages: list[LLMMessage],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        """Alias for complete."""
        return await self.complete(messages, tools, temperature, max_tokens)

    async def complete(
        self,
        messages: list[LLMMessage],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        """Return the next scripted response in the sequence."""
        self.call_history.append(
            {
                "messages": [m.to_dict() for m in messages],
                "tools": tools,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
        )

        if self._current_index >= len(self.scripted_responses):
            # Default response when script is exhausted
            return LLMResponse(
                content="I have processed your request based on the verified records.",
                tool_calls=[],
                tokens_in=10,
                tokens_out=10,
                model="mock-exhausted",
            )

        item = self.scripted_responses[self._current_index]
        self._current_index += 1

        if isinstance(item, Exception):
            raise item

        if callable(item):
            return item(messages)

        return item
