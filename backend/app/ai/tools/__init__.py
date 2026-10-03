"""Tool manager and tool definitions for AI agent."""

from app.ai.tools.implementations import (
    CalculateDoublingTimeSchema,
    CalculateFutureValueSchema,
    CalculateGoalPlanSchema,
    CalculateSavingsRateSchema,
    CheckAffordabilitySchema,
    EmptyArgsSchema,
    FinancialToolSet,
    GetAnomaliesSchema,
    GetMonthlySummarySchema,
    GetTransactionsSchema,
    RunFinancialScenarioSchema,
    SearchKnowledgeSchema,
    register_financial_tools,
)
from app.ai.tools.registry import (
    MAX_TOOL_BUDGET_PER_TURN,
    TOOL_TIMEOUT_SECONDS,
    ToolBudgetExceededError,
    ToolDefinition,
    ToolExecutionError,
    ToolManager,
)

__all__ = [
    "MAX_TOOL_BUDGET_PER_TURN",
    "TOOL_TIMEOUT_SECONDS",
    "CalculateDoublingTimeSchema",
    "CalculateFutureValueSchema",
    "CalculateGoalPlanSchema",
    "CalculateSavingsRateSchema",
    "CheckAffordabilitySchema",
    "EmptyArgsSchema",
    "FinancialToolSet",
    "GetAnomaliesSchema",
    "GetMonthlySummarySchema",
    "GetTransactionsSchema",
    "RunFinancialScenarioSchema",
    "SearchKnowledgeSchema",
    "ToolBudgetExceededError",
    "ToolDefinition",
    "ToolExecutionError",
    "ToolManager",
    "register_financial_tools",
]
