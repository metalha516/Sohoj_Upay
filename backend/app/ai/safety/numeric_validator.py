"""Numeric-grounding validator ensuring every number/percentage in responses is grounded in tool outputs."""

from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# Pattern matching potential numbers, currencies, and percentages
NUMBER_PATTERN = re.compile(
    r"(?:৳|BDT|Tk\.?|\$)?\s*(-?\d{1,3}(?:,\d{3})+(?:\.\d+)?|-?\d+(?:\.\d+)?)\s*(?:%|[km]\b)?",
    re.IGNORECASE,
)


# Common conversational and rule constants that don't require tool grounding
EXEMPT_INTEGERS = {
    0,
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    9,
    10,
    11,
    12,  # Month indices & list bullets
    14,
    15,
    20,
    24,
    30,
    31,
    50,
    60,
    72,
    100,
    365,  # 50/30/20 rule, rule of 72, percentages
}
EXEMPT_YEAR_RANGE = range(2020, 2045)


@dataclass
class GroundingResult:
    """Evaluation result of numeric grounding check."""

    is_grounded: bool
    ungrounded_numbers: list[float] = field(default_factory=list)
    grounded_numbers: list[float] = field(default_factory=list)
    exempt_numbers: list[float] = field(default_factory=list)


class NumericGroundingValidator:
    """Verifies that all numerical values in LLM responses are derived from tool data."""

    def extract_numbers_from_text(self, text: str) -> list[float]:
        """Extract all floating-point numbers and percentages from markdown text."""
        numbers: list[float] = []
        for match in NUMBER_PATTERN.finditer(text):
            num_str = match.group(1).replace(",", "")
            try:
                val = float(num_str)
                # Check suffix for 'k' or 'M'
                full_match = match.group(0).lower()
                if re.search(r"\d\s*k\b", full_match) and not full_match.startswith("tk"):
                    val *= 1000
                elif re.search(r"\d\s*m\b", full_match):
                    val *= 1_000_000
                numbers.append(val)
            except ValueError:
                continue
        return numbers

    def extract_numbers_from_tool_data(self, data: Any) -> set[float]:
        """Recursively collect all numeric scalars from tool outputs."""
        grounding_set: set[float] = set()

        def _traverse(item: Any) -> None:
            if isinstance(item, (int, float)) and not isinstance(item, bool):
                val = float(item)
                grounding_set.add(val)
                # If val is between 0 and 1, add percentage equivalent (e.g. 0.25 -> 25.0)
                if 0.0 < val <= 1.0:
                    grounding_set.add(round(val * 100, 2))
                    grounding_set.add(round(val * 100, 1))
                # If val is between 1 and 100, add fractional equivalent (e.g. 25.0 -> 0.25)
                elif 1.0 <= val <= 100.0:
                    grounding_set.add(round(val / 100, 4))
                    grounding_set.add(round(val / 100, 2))
            elif isinstance(item, str):
                # Extract clean or embedded numbers from strings (e.g. from RAG passages)
                try:
                    val = float(item.replace(",", ""))
                    grounding_set.add(val)
                except ValueError:
                    for num in self.extract_numbers_from_text(item):
                        grounding_set.add(num)
            elif isinstance(item, dict):
                for v in item.values():
                    _traverse(v)
            elif isinstance(item, (list, tuple, set)):
                for v in item:
                    _traverse(v)

        _traverse(data)
        return grounding_set

    def is_number_grounded(
        self,
        candidate: float,
        allowed_set: set[float],
        tolerance: float = 0.02,
    ) -> bool:
        """Check if candidate matches any number in allowed_set within relative or absolute tolerance."""
        # 1. Exempt check
        if candidate.is_integer() and int(candidate) in EXEMPT_INTEGERS:
            return True
        if candidate.is_integer() and int(candidate) in EXEMPT_YEAR_RANGE:
            return True

        # 2. Check matches against allowed_set
        for allowed in allowed_set:
            if math.isclose(candidate, allowed, abs_tol=0.05):
                return True
            if allowed != 0.0 and abs(candidate - allowed) / abs(allowed) <= tolerance:
                return True
            # Also allow approximate thousand rounding (e.g. 367,384 -> 367,000 or 367k)
            if allowed > 1000 and abs(candidate - allowed) <= (0.05 * allowed):
                return True

        return False

    def validate(
        self,
        response_text: str,
        user_query: str,
        context_numbers: set[float],
        tool_results: list[dict[str, Any]],
    ) -> GroundingResult:
        """Validate all numbers in response_text against query, context, and tool data."""
        allowed_set: set[float] = set(context_numbers)

        # 1. Add numbers from user query
        query_numbers = self.extract_numbers_from_text(user_query)
        allowed_set.update(query_numbers)

        # 2. Add numbers from all tool results
        for tool_res in tool_results:
            tool_nums = self.extract_numbers_from_tool_data(tool_res)
            allowed_set.update(tool_nums)

        # 3. Extract numbers in LLM response
        candidate_numbers = self.extract_numbers_from_text(response_text)

        ungrounded: list[float] = []
        grounded: list[float] = []
        exempt: list[float] = []

        for num in candidate_numbers:
            if num.is_integer() and (int(num) in EXEMPT_INTEGERS or int(num) in EXEMPT_YEAR_RANGE):
                exempt.append(num)
            elif self.is_number_grounded(num, allowed_set):
                grounded.append(num)
            else:
                ungrounded.append(num)

        is_valid = len(ungrounded) == 0
        if not is_valid:
            logger.warning(
                "Numeric grounding failure: %s ungrounded numbers found: %s",
                len(ungrounded),
                ungrounded,
            )

        return GroundingResult(
            is_grounded=is_valid,
            ungrounded_numbers=ungrounded,
            grounded_numbers=grounded,
            exempt_numbers=exempt,
        )
