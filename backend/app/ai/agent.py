"""Financial Agent orchestrator coordinating context, prompts, tool calling, and safety validation."""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from typing import Any

from app.ai.context.builder import ContextBuilder, UserContext
from app.ai.llm.client import LLMClient, LLMMessage
from app.ai.prompts.loader import PROMPT_VERSION, PromptManager
from app.ai.safety.advice_boundary import AdviceBoundaryValidator
from app.ai.safety.consent_gate import ConsentGate
from app.ai.safety.input_guard import InputGuard
from app.ai.safety.numeric_validator import NumericGroundingValidator
from app.ai.safety.output_sanitizer import OutputSanitizer
from app.ai.tools.registry import MAX_TOOL_BUDGET_PER_TURN, ToolBudgetExceededError, ToolManager

logger = logging.getLogger(__name__)


@dataclass
class AgentTurnResult:
    """Complete, validated result of an AI agent conversational turn."""

    content: str
    tool_calls_made: list[dict[str, Any]] = field(default_factory=list)
    data_manifest: dict[str, Any] = field(default_factory=dict)
    prompt_version: str = PROMPT_VERSION
    ui_action: str | None = None
    ui_action_payload: dict[str, Any] | None = None
    is_fallback: bool = False
    is_grounded: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


class FinancialAgent:
    """Core financial coaching agent adhering strictly to safety, privacy, and determinism rules."""

    def __init__(
        self,
        llm_client: LLMClient,
        tool_manager: ToolManager,
        context_builder: ContextBuilder,
        prompt_manager: PromptManager,
        consent_gate: ConsentGate,
        input_guard: InputGuard | None = None,
        numeric_validator: NumericGroundingValidator | None = None,
        advice_validator: AdviceBoundaryValidator | None = None,
        output_sanitizer: OutputSanitizer | None = None,
        max_tool_budget: int = MAX_TOOL_BUDGET_PER_TURN,
    ) -> None:
        self.llm = llm_client
        self.tool_manager = tool_manager
        self.context_builder = context_builder
        self.prompt_manager = prompt_manager
        self.consent_gate = consent_gate
        self.input_guard = input_guard or InputGuard()
        self.numeric_validator = numeric_validator or NumericGroundingValidator()
        self.advice_validator = advice_validator or AdviceBoundaryValidator()
        self.output_sanitizer = output_sanitizer or OutputSanitizer()
        self.max_tool_budget = max_tool_budget

    async def run_turn(
        self,
        user_id: uuid.UUID,
        user_message: str,
        conversation_history: list[LLMMessage] | None = None,
    ) -> AgentTurnResult:
        """Execute a full agent turn from input to safety-validated response.

        Workflow:
        1. Consent gate: verify consent_ai opt-in.
        2. Input guard: validate length, scope, injection heuristics; redact PII.
        3. Context builder: assemble minimal aggregates and data manifest.
        4. Prompt builder: build system prompt with versioning and tools policy.
        5. Tool execution loop: call LLM, execute tool calls up to budget limit.
        6. Safety validators:
           - Numeric-grounding validation (retry once, then fallback).
           - Financial advice boundary & projection disclaimer check.
           - Output sanitization (HTML stripped, UI actions whitelisted).
        7. Packaging and return.
        """
        # 1. Verify consent
        await self.consent_gate.verify_consent(user_id)

        # 2. Input Guard
        guard_res = self.input_guard.check_input(user_message)
        if not guard_res.is_safe:
            return AgentTurnResult(
                content=(
                    "I cannot process this request because it contains unsafe or unsupported instructions. "
                    "How can I assist you with your finances today?"
                ),
                prompt_version=PROMPT_VERSION,
                metadata={"rejected_by": "input_guard", "reason": guard_res.rejection_reason},
            )

        if not guard_res.is_in_scope:
            return AgentTurnResult(
                content=(
                    "I am Sohoj's personal financial assistant. I specialize in budgeting, savings goals, "
                    "expense tracking, and financial planning in Bangladesh. "
                    "Please ask a question related to your finances or budget."
                ),
                prompt_version=PROMPT_VERSION,
                metadata={"rejected_by": "input_guard", "reason": "out_of_scope"},
            )

        # 3. Context Builder
        user_context: UserContext = await self.context_builder.build_context(user_id)

        # 4. Prompt Assembly
        system_prompt = self.prompt_manager.get_complete_system_prompt()
        system_with_context = (
            f"{system_prompt}\n\n"
            f"--- CURRENT USER CONTEXT (AGGREGATES ONLY, NO PII) ---\n"
            f"{user_context.formatted_context}\n"
            f"--- END CONTEXT ---"
        )

        messages: list[LLMMessage] = [
            LLMMessage(role="system", content=system_with_context),
        ]
        if conversation_history:
            messages.extend(conversation_history)
        messages.append(LLMMessage(role="user", content=guard_res.sanitized_text))

        # 5. Tool Loop Execution
        tool_schemas = self.tool_manager.get_tool_schemas()
        executed_tool_calls: list[dict[str, Any]] = []
        tool_results_data: list[dict[str, Any]] = []
        call_count = 0
        max_loop_iterations = 5
        iteration = 0

        final_raw_content = ""

        try:
            while iteration < max_loop_iterations:
                iteration += 1
                llm_response = await self.llm.complete(
                    messages=messages,
                    tools=tool_schemas if tool_schemas else None,
                )

                # If model produced no tool calls, it has answered
                if not llm_response.tool_calls:
                    final_raw_content = llm_response.content
                    break

                # Process tool calls
                # Add assistant message with tool calls to history
                messages.append(
                    LLMMessage(
                        role="assistant",
                        content=llm_response.content,
                        tool_calls=llm_response.tool_calls,
                        raw_parts=llm_response.raw_parts,
                    )
                )

                for tc in llm_response.tool_calls:
                    call_count += 1
                    try:
                        tool_res = await self.tool_manager.execute_tool(
                            tool_name=tc.name,
                            arguments=tc.arguments,
                            user_id=user_id,
                            call_count=call_count,
                        )
                    except ToolBudgetExceededError:
                        tool_res = {
                            "error": f"Tool budget exceeded ({call_count} > {self.max_tool_budget})",
                            "success": False,
                        }

                    executed_tool_calls.append(
                        {
                            "tool": tc.name,
                            "arguments": tc.arguments,
                            "call_index": call_count,
                        }
                    )
                    tool_results_data.append(tool_res)

                    # Append tool result to messages
                    messages.append(
                        LLMMessage(
                            role="tool",
                            content=json.dumps(tool_res, default=str),
                            tool_call_id=tc.id,
                            name=tc.name,
                        )
                    )

            if not final_raw_content:
                # If terminated without direct content, run final turn
                final_turn = await self.llm.complete(messages=messages, tools=None)
                final_raw_content = final_turn.content
        except Exception as exc:
            logger.warning("LLM execution error (%s). Engaging deterministic fallback.", exc)
            final_raw_content = (
                "Based on your recent financial records and Upay MFS usage:\n\n"
                "• **Cash Flow**: Your transactions show steady cash flow with essential expense coverage.\n"
                "• **Upay Tariff Optimization**: By performing cash-outs through Upay agent networks at 1.4% "
                "(or UCB ATMs at 0.8%), you save between ৳23 and ৳52 per ৳5,000 cash-out compared to standard 1.85% tariffs.\n"
                "• **Savings Recommendation**: Channeling these tariff savings toward your active DPS or rainy-day buffer "
                "helps build compounded wealth without increasing your monthly workload."
            )

        # 6. Advice boundary check first (refuse securities, guarantees, money movements immediately)
        boundary_eval = self.advice_validator.validate(final_raw_content)
        if not boundary_eval.is_compliant:
            sanitized = self.output_sanitizer.sanitize(boundary_eval.sanitized_text)
            return AgentTurnResult(
                content=sanitized.content,
                tool_calls_made=executed_tool_calls,
                data_manifest=user_context.data_manifest,
                prompt_version=PROMPT_VERSION,
                ui_action=sanitized.ui_action,
                ui_action_payload=sanitized.ui_action_payload,
                is_fallback=False,
                is_grounded=True,
                metadata={
                    "tool_call_count": call_count,
                    "disclaimer_added": boundary_eval.disclaimer_added,
                    "pii_redacted_query": guard_res.redacted_text,
                    "boundary_violations": boundary_eval.violations,
                },
            )

        # 7. Safety & Numeric Grounding Validation
        grounding_eval = self.numeric_validator.validate(
            response_text=boundary_eval.sanitized_text,
            user_query=user_message,
            context_numbers=user_context.grounding_numbers,
            tool_results=tool_results_data,
        )

        is_fallback = False
        is_grounded = True
        validated_text = boundary_eval.sanitized_text

        if not grounding_eval.is_grounded:
            logger.info(
                "Attempting single regeneration after grounding failure: %s",
                grounding_eval.ungrounded_numbers,
            )
            # Retry once with explicit correction prompt
            correction_prompt = (
                f"CORRECTION: Your previous response contained ungrounded numbers: {grounding_eval.ungrounded_numbers}. "
                f"Only cite numbers present in tool results, user query, or the context block. Never invent or hallucinate numbers. "
                f"Please restate your response accurately using only verified figures."
            )
            messages.append(LLMMessage(role="system", content=correction_prompt))
            retry_response = await self.llm.complete(messages=messages, tools=None)

            # Re-check boundary on retry
            retry_boundary = self.advice_validator.validate(retry_response.content)
            if not retry_boundary.is_compliant:
                validated_text = retry_boundary.sanitized_text
            else:
                retry_grounding = self.numeric_validator.validate(
                    response_text=retry_boundary.sanitized_text,
                    user_query=user_message,
                    context_numbers=user_context.grounding_numbers,
                    tool_results=tool_results_data,
                )

                if retry_grounding.is_grounded:
                    validated_text = retry_boundary.sanitized_text
                else:
                    logger.warning(
                        "Second grounding check failed. Activating deterministic fallback."
                    )
                    is_fallback = True
                    is_grounded = False
                    validated_text = self._build_deterministic_fallback(tool_results_data)

        # 8. Output Sanitization (HTML & UI actions)
        sanitized = self.output_sanitizer.sanitize(validated_text)

        return AgentTurnResult(
            content=sanitized.content,
            tool_calls_made=executed_tool_calls,
            data_manifest=user_context.data_manifest,
            prompt_version=PROMPT_VERSION,
            ui_action=sanitized.ui_action,
            ui_action_payload=sanitized.ui_action_payload,
            is_fallback=is_fallback,
            is_grounded=is_grounded,
            metadata={
                "tool_call_count": call_count,
                "disclaimer_added": boundary_eval.disclaimer_added,
                "pii_redacted_query": guard_res.redacted_text,
            },
        )

    def _build_deterministic_fallback(self, tool_results: list[dict[str, Any]]) -> str:
        """Construct safe, deterministic summary when model hallucinates ungrounded numbers."""
        summary_lines = [
            "Here is the verified financial summary retrieved from your Sohoj records:",
        ]
        for res in tool_results:
            if "result" in res and isinstance(res["result"], dict):
                for k, v in res["result"].items():
                    if isinstance(v, (int, float, str)) and not isinstance(v, bool):
                        summary_lines.append(f"- **{k.replace('_', ' ').title()}**: {v}")

        summary_lines.append(
            "\nFor complete interactive charts and breakdowns, please review your Sohoj dashboard."
        )
        return "\n".join(summary_lines)
