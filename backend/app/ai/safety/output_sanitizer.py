"""Output sanitizer: safe markdown rendering and UI action allowlisting."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

ALLOWED_UI_ACTIONS = {
    "navigate_to_goals",
    "open_simulator",
    "view_budget",
    "view_transactions",
    "view_dashboard",
    "view_anomalies",
}

# Regex to strip dangerous HTML tags
DANGEROUS_HTML_PATTERN = re.compile(
    r"<(?:script|iframe|object|embed|style|meta|form|input|button)[\s\S]*?>[\s\S]*?<\/(?:script|iframe|object|embed|style|meta|form|input|button)>|"
    r"<(?:script|iframe|object|embed|style|meta|form|input|button)[\s\S]*?>",
    re.IGNORECASE,
)

# Regex to remove javascript: pseudo-protocol in links
JAVASCRIPT_LINK_PATTERN = re.compile(
    r"\[([^\]]+)\]\((?:javascript|data|vbscript):[^\)]+\)", re.IGNORECASE
)


@dataclass
class SanitizedOutput:
    """Cleaned, safe output ready for client consumption."""

    content: str
    ui_action: str | None
    ui_action_payload: dict[str, Any] | None


class OutputSanitizer:
    """Sanitizes generated agent outputs and enforces UI action allowlists."""

    def sanitize(
        self,
        text: str,
        ui_action: str | None = None,
        ui_action_payload: dict[str, Any] | None = None,
    ) -> SanitizedOutput:
        """Sanitize markdown text and validate UI actions against the allowed whitelist."""
        # 1. Strip dangerous HTML
        clean_text = DANGEROUS_HTML_PATTERN.sub("", text)

        # 2. Strip javascript/data links
        clean_text = JAVASCRIPT_LINK_PATTERN.sub(r"[\1](#)", clean_text)

        # 3. Validate ui_action
        validated_action = None
        if ui_action and ui_action.lower() in ALLOWED_UI_ACTIONS:
            validated_action = ui_action.lower()
        elif ui_action:
            logger.warning("Rejected unpermitted ui_action: '%s'", ui_action)

        return SanitizedOutput(
            content=clean_text.strip(),
            ui_action=validated_action,
            ui_action_payload=ui_action_payload if validated_action else None,
        )
