"""Consent gate ensuring AI features are only invoked when consent_ai is True."""

from __future__ import annotations

import logging
import uuid

from app.services.user_service import UserService

logger = logging.getLogger(__name__)


class ConsentRequiredError(Exception):
    """Raised when an AI operation is requested without user consent_ai opt-in."""

    def __init__(
        self,
        message: str = (
            "AI financial coaching requires your explicit consent. "
            "You can enable this at any time in your profile settings."
        ),
    ) -> None:
        super().__init__(message)
        self.message = message


class ConsentGate:
    """Verifies user consent_ai opt-in prior to invoking AI models."""

    def __init__(self, user_service: UserService) -> None:
        self.user_service = user_service

    async def verify_consent(self, user_id: uuid.UUID) -> bool:
        """Check if user has consent_ai enabled. Raises ConsentRequiredError if not."""
        user = await self.user_service.get_user(user_id)
        if not user or not user.consent_ai:
            logger.warning(
                "AI request rejected for user %s: consent_ai is disabled or user not found",
                user_id,
            )
            raise ConsentRequiredError()
        return True
