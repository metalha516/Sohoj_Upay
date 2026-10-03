"""AI Agent package: prompts, tools, context builder, safety layer, and orchestrator."""

from app.ai.agent import AgentTurnResult, FinancialAgent
from app.ai.context.builder import ContextBuilder, UserContext
from app.ai.llm.client import LLMClient, LLMMessage, LLMResponse, ToolCall
from app.ai.llm.gemini_client import GeminiLLMClient
from app.ai.llm.mock import MockLLM
from app.ai.prompts.loader import PROMPT_VERSION, PromptManager
from app.ai.safety import (
    AdviceBoundaryValidator,
    ConsentGate,
    ConsentRequiredError,
    InputGuard,
    NumericGroundingValidator,
    OutputSanitizer,
)
from app.ai.tools.implementations import FinancialToolSet, register_financial_tools
from app.ai.tools.registry import ToolBudgetExceededError, ToolDefinition, ToolManager

__all__ = [
    "PROMPT_VERSION",
    "AdviceBoundaryValidator",
    "AgentTurnResult",
    "ConsentGate",
    "ConsentRequiredError",
    "ContextBuilder",
    "FinancialAgent",
    "FinancialToolSet",
    "GeminiLLMClient",
    "InputGuard",
    "LLMClient",
    "LLMMessage",
    "LLMResponse",
    "MockLLM",
    "NumericGroundingValidator",
    "OutputSanitizer",
    "PromptManager",
    "ToolBudgetExceededError",
    "ToolCall",
    "ToolDefinition",
    "ToolManager",
    "UserContext",
    "register_financial_tools",
]
