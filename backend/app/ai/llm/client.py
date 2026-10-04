"""LLM client interface, data structures, and protocol definition."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol, runtime_checkable


@dataclass
class ToolCall:
    """A tool invocation emitted by the language model."""

    id: str
    name: str = ""
    arguments: dict[str, Any] = field(default_factory=dict)
    function_name: str | None = None
    thought_signature: str | None = None
    raw_part: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.function_name and not self.name:
            self.name = self.function_name
        elif self.name and not self.function_name:
            self.function_name = self.name


@dataclass
class LLMMessage:
    """A message in the conversational transcript."""

    role: Literal["system", "user", "assistant", "tool"]
    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_call_id: str | None = None
    name: str | None = None
    raw_parts: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert message to a dictionary for API consumption."""
        res: dict[str, Any] = {"role": self.role, "content": self.content}
        if self.tool_calls:
            res["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.name, "arguments": json.dumps(tc.arguments)},
                }
                for tc in self.tool_calls
            ]
        if self.tool_call_id:
            res["tool_call_id"] = self.tool_call_id
        if self.name:
            res["name"] = self.name
        return res


@dataclass(frozen=True)
class LLMResponse:
    """The generated response from the language model."""

    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    tokens_in: int = 0
    tokens_out: int = 0
    model: str = "mock-model"
    raw_parts: list[dict[str, Any]] = field(default_factory=list)


@runtime_checkable
class LLMClient(Protocol):
    """Protocol for language model client adapters."""

    async def complete(
        self,
        messages: list[LLMMessage],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        """Generate a response given conversational context and tool schemas."""
        ...
