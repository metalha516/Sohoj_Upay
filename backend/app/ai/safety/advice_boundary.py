"""Advice boundary validator: ensures advice complies with financial regulations and includes disclaimers."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

STANDARD_PROJECTION_DISCLAIMER = (
    "\n\n*Disclaimer: Projections are illustrative estimates based on stated assumptions "
    "and are not guaranteed. Shohoj Upay does not provide licensed investment or tax advice.*"
)

# Prohibited patterns
SECURITIES_PATTERNS = [
    re.compile(r"\b(?:buy|sell|short)\s+(?:shares|stocks?|equity)\s+of\b", re.IGNORECASE),
    re.compile(
        r"\binvest\s+in\s+(?:beximco|square pharma|grameenphone|gp|brac bank)\s+shares\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?:bitcoin|ethereum|crypto(?:currency)?)\s+investment\b", re.IGNORECASE),
]

GUARANTEE_PATTERNS = [
    re.compile(
        r"\b(?:guaranteed|risk-free|100%\s+certain)\s+(?:return|profit|gain)\b", re.IGNORECASE
    ),
    re.compile(r"\byou\s+will\s+definitely\s+(?:double|earn|make)\b", re.IGNORECASE),
]

MONEY_MOVEMENT_PATTERNS = [
    re.compile(
        r"\bi(?:\s+have|\s+'ve)?\s+(?:transferred|sent|moved|paid|withdrawn)\b", re.IGNORECASE
    ),
    re.compile(r"\binitiating\s+(?:transfer|payment|cash-out)\b", re.IGNORECASE),
]

PROJECTION_INDICATORS = [
    re.compile(r"\bin\s+\d+\s+years\b", re.IGNORECASE),
    re.compile(r"\bfuture\s+value\b", re.IGNORECASE),
    re.compile(r"\bdoubling\s+time\b", re.IGNORECASE),
    re.compile(r"\bprojected\s+(?:net\s+worth|savings|balance)\b", re.IGNORECASE),
    re.compile(r"\bgrowth\s+scenario\b", re.IGNORECASE),
]


@dataclass
class BoundaryResult:
    """Evaluation result of advice boundary check."""

    is_compliant: bool
    sanitized_text: str
    violations: list[str]
    disclaimer_added: bool = False


class AdviceBoundaryValidator:
    """Enforces financial advice boundaries, securities restrictions, and disclaimer requirements."""

    def validate(self, text: str) -> BoundaryResult:
        """Check for securities recommendations, guarantees, money movements, and missing disclaimers."""
        violations: list[str] = []

        # 1. Check securities violations
        for pat in SECURITIES_PATTERNS:
            if pat.search(text):
                violations.append(
                    "Specific securities or individual stock recommendation detected."
                )

        # 2. Check guarantee claims
        for pat in GUARANTEE_PATTERNS:
            if pat.search(text):
                violations.append("Unqualified guarantee or risk-free return claim detected.")

        # 3. Check autonomous money movement
        for pat in MONEY_MOVEMENT_PATTERNS:
            if pat.search(text):
                violations.append("Claim of autonomous money movement or fund execution detected.")

        if violations:
            logger.warning("Advice boundary violation(s): %s", violations)
            # Safe refusal replacement
            replacement_text = (
                "I am Shohoj Upay's financial coach. I provide educational guidance, budget analysis, "
                "and scenario planning based on your recorded transactions. I cannot recommend specific stocks, "
                "guarantee investment returns, or execute money transfers on your behalf."
            )
            return BoundaryResult(
                is_compliant=False,
                sanitized_text=replacement_text,
                violations=violations,
                disclaimer_added=False,
            )

        # 4. Check projection disclaimer
        is_projection = any(pat.search(text) for pat in PROJECTION_INDICATORS)
        disclaimer_added = False
        out_text = text

        if is_projection:
            has_disclaimer = (
                "not guaranteed" in text.lower()
                or "disclaimer" in text.lower()
                or "illustrative" in text.lower()
            )
            if not has_disclaimer:
                out_text = text.rstrip() + STANDARD_PROJECTION_DISCLAIMER
                disclaimer_added = True

        return BoundaryResult(
            is_compliant=True,
            sanitized_text=out_text,
            violations=[],
            disclaimer_added=disclaimer_added,
        )
