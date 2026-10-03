"""Conversation management package."""

from app.ai.conversation.manager import (
    DEFAULT_MAX_RECENT_TURNS,
    DEFAULT_RETENTION_DAYS,
    ConversationManager,
)

__all__ = [
    "DEFAULT_MAX_RECENT_TURNS",
    "DEFAULT_RETENTION_DAYS",
    "ConversationManager",
]
