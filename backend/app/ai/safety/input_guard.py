"""Input guard: prompt injection heuristics, scope check, length limits, and PII redaction."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

MAX_INPUT_LENGTH = 2000

# Prompt injection heuristics
INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(?:all\s+)?(?:previous|prior|above)\s+instructions", re.IGNORECASE),
    re.compile(r"disregard\s+(?:all\s+)?(?:previous|prior|above)\s+rules", re.IGNORECASE),
    re.compile(
        r"(?:print|reveal|show|display|output)\s+(?:your\s+)?(?:system\s+prompt|developer\s+instructions|initial\s+prompt)",
        re.IGNORECASE,
    ),
    re.compile(r"(?:dan\s+mode|jailbreak|developer\s+mode\s+enabled)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(?:unrestricted|free\s+from|an\s+evil)", re.IGNORECASE),
    re.compile(r"system\s*:\s*(?:override|bypass|admin)", re.IGNORECASE),
    re.compile(r"fetch\s+(?:all\s+)?data\s+for\s+user(?:_id)?\s*=\s*", re.IGNORECASE),
    re.compile(r"<script[\s>]|<!--\s*#exec|\bunion\s+select\b", re.IGNORECASE),
]

# Relevant financial keywords indicating valid scope
FINANCIAL_KEYWORDS = [
    "৳",
    "taka",
    "tk",
    "bdt",
    "money",
    "budget",
    "save",
    "saving",
    "spend",
    "spending",
    "expense",
    "cost",
    "income",
    "salary",
    "balance",
    "goal",
    "emergency",
    "fund",
    "dps",
    "fdr",
    "bank",
    "deposit",
    "account",
    "charge",
    "charges",
    "double",
    "doubling",
    "growth",
    "future",
    "value",
    "return",
    "returns",
    "invest",
    "interest",
    "inflation",
    "afford",
    "purchase",
    "buy",
    "surplus",
    "debt",
    "loan",
    "forecast",
    "cash",
    "transaction",
    "anomal",
    "shopping",
    "food",
    "rent",
    "bill",
    "grocer",
    "lifestyle",
    "sohoj",
    "shohoj",
    "upay",
    "wallet",
    "financial",
    "finance",
    "rate",
    "percent",
    "pct",
    "earn",
    "rich",
    "wealth",
    "worth",
    "bkash",
    "nagad",
    "rocket",
    "upay",
    "mfs",
    "credit",
    "debit",
    "stock",
    "share",
    "crypto",
    "bitcoin",
    "dse",
    "calculate",
    "plan",
    "planning",
]


# PII patterns
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
BD_PHONE_PATTERN = re.compile(r"(?:\+8801|01)[3-9]\d{8}\b")
CARD_PATTERN = re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b")
NID_PATTERN = re.compile(r"\b(?:NID\s*:?\s*)?\d{10,17}\b", re.IGNORECASE)


@dataclass
class GuardResult:
    """Result of running input guard checks."""

    is_safe: bool
    is_in_scope: bool
    sanitized_text: str
    redacted_text: str
    rejection_reason: str | None = None


class InputGuard:
    """Validates and sanitizes incoming user input prior to LLM processing."""

    def __init__(self, max_length: int = MAX_INPUT_LENGTH) -> None:
        self.max_length = max_length

    def redact_pii(self, text: str) -> str:
        """Mask emails, phone numbers, and payment cards for secure logging."""
        out = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", text)
        out = BD_PHONE_PATTERN.sub("[REDACTED_PHONE]", out)
        out = CARD_PATTERN.sub("[REDACTED_CARD]", out)
        return out

    def check_input(self, user_query: str) -> GuardResult:
        """Perform length, injection, and financial scope checks."""
        # 1. Length check
        if len(user_query) > self.max_length:
            return GuardResult(
                is_safe=False,
                is_in_scope=True,
                sanitized_text=user_query[: self.max_length],
                redacted_text=self.redact_pii(user_query[: self.max_length]),
                rejection_reason=f"Message exceeds maximum allowed length of {self.max_length} characters.",
            )

        # 2. Prompt injection heuristics
        for pattern in INJECTION_PATTERNS:
            if pattern.search(user_query):
                logger.warning("Prompt injection pattern detected: %s", pattern.pattern)
                return GuardResult(
                    is_safe=False,
                    is_in_scope=False,
                    sanitized_text=user_query,
                    redacted_text=self.redact_pii(user_query),
                    rejection_reason="Query contains prohibited or adversarial prompt manipulation patterns.",
                )

        # 3. Financial scope check
        # Short common greetings are allowed (e.g., "hi", "hello", "help")
        normalized = user_query.lower()
        is_greeting = normalized.strip() in {
            "hi",
            "hello",
            "hey",
            "help",
            "salam",
            "assalamualaikum",
            "start",
        }

        is_finance_scoped = is_greeting or any(kw in normalized for kw in FINANCIAL_KEYWORDS)

        redacted = self.redact_pii(user_query)

        return GuardResult(
            is_safe=True,
            is_in_scope=is_finance_scoped,
            sanitized_text=user_query.strip(),
            redacted_text=redacted.strip(),
            rejection_reason=None if is_finance_scoped else "OUT_OF_SCOPE",
        )
