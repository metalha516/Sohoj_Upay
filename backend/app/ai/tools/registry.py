"""Tool registry, argument validation, per-turn budget, and user_id injection."""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

MAX_TOOL_BUDGET_PER_TURN = 6
TOOL_TIMEOUT_SECONDS = 5.0


class ToolBudgetExceededError(RuntimeError):
    """Raised when the LLM attempts more tool calls than permitted per turn."""


class ToolExecutionError(RuntimeError):
    """Raised when tool execution fails or encounters a timeout."""


@dataclass
class ToolDefinition:
    """Metadata and execution specification for a registered agent tool."""

    name: str
    description: str
    schema_model: type[BaseModel]
    handler: Callable[..., Coroutine[Any, Any, Any]]
    requires_user_id: bool = False

    def to_openapi_tool(self) -> dict[str, Any]:
        """Convert definition to OpenAI tool schema format."""
        schema = self.schema_model.model_json_schema()
        # Clean up unwanted internal titles
        schema.pop("title", None)
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": schema,
            },
        }


class ToolManager:
    """Registry managing tool lifecycle, validation, budget, and context injection."""

    def __init__(self, max_budget: int = MAX_TOOL_BUDGET_PER_TURN) -> None:
        self.max_budget = max_budget
        self._tools: dict[str, ToolDefinition] = {}

    def register(
        self,
        name: str,
        description: str,
        schema_model: type[BaseModel],
        handler: Callable[..., Coroutine[Any, Any, Any]],
        requires_user_id: bool = False,
    ) -> None:
        """Register a new tool definition."""
        self._tools[name] = ToolDefinition(
            name=name,
            description=description,
            schema_model=schema_model,
            handler=handler,
            requires_user_id=requires_user_id,
        )

    def get_tool_schemas(self) -> list[dict[str, Any]]:
        """Return all registered tool schemas formatted for LLM consumption."""
        return [tool.to_openapi_tool() for tool in self._tools.values()]

    async def execute_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        user_id: uuid.UUID,
        call_count: int,
    ) -> dict[str, Any]:
        """Validate arguments, inject user_id, enforce budget, and execute tool.

        Security guarantees:
        - Rejects unauthorized or unknown tool names.
        - Enforces strict per-turn budget (<= 6 calls).
        - Injects user_id strictly from the authenticated JWT principal.
        - extra='forbid' prevents callers from overriding user_id.
        - Enforces execution timeout.
        """
        if call_count > self.max_budget:
            raise ToolBudgetExceededError(
                f"Per-turn tool budget exceeded: {call_count} > {self.max_budget}"
            )

        if tool_name not in self._tools:
            return {
                "error": f"Tool '{tool_name}' is not recognized. Available tools: {list(self._tools.keys())}",
                "success": False,
            }

        tool = self._tools[tool_name]

        # 1. Validate arguments using Pydantic model
        try:
            validated_args = tool.schema_model.model_validate(arguments).model_dump()
        except ValidationError as e:
            logger.warning("Tool argument validation failed for '%s': %s", tool_name, e)
            return {
                "error": f"Invalid arguments for tool '{tool_name}': {e.errors()}",
                "success": False,
            }

        # 2. Inject authenticated user_id server-side
        kwargs = dict(validated_args)
        if tool.requires_user_id:
            kwargs["user_id"] = user_id

        # 3. Execute with timeout
        try:
            result = await asyncio.wait_for(
                tool.handler(**kwargs),
                timeout=TOOL_TIMEOUT_SECONDS,
            )
            return {
                "result": result,
                "success": True,
            }
        except TimeoutError:
            logger.error("Tool '%s' timed out after %.1f seconds", tool_name, TOOL_TIMEOUT_SECONDS)
            return {
                "error": f"Tool '{tool_name}' timed out.",
                "success": False,
            }
        except Exception as e:
            logger.exception("Error executing tool '%s': %s", tool_name, e)
            return {
                "error": f"Tool execution failed: {e!s}",
                "success": False,
            }
