"""Pydantic V2 schemas for AI chat dialogue, streaming events, and message feedback."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    """Payload to submit a user message to the AI coach."""

    model_config = ConfigDict(extra="forbid")

    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User financial query or question",
    )
    conversation_id: uuid.UUID | None = Field(
        default=None,
        description="Optional active conversation thread UUID; generates a new thread if omitted",
    )
    stream: bool = Field(
        default=True,
        description="Whether to deliver response via Server-Sent Events (SSE) streaming",
    )


class ChatResponse(BaseModel):
    """Non-streaming response from the AI coach."""

    model_config = ConfigDict(from_attributes=True)

    message_id: uuid.UUID
    conversation_id: uuid.UUID
    role: str = "assistant"
    content: str
    ui_action: str | None = None
    ui_action_payload: dict[str, Any] | None = None
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: int = 0
    prompt_version: str
    is_fallback: bool = False
    is_grounded: bool = True


class ChatMessageResponse(BaseModel):
    """Individual dialogue message item for conversation history."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: str
    feedback: int | None = None
    created_at: datetime
    tool_calls: dict[str, Any] | None = None


class ConversationResponse(BaseModel):
    """Conversational thread summary."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str | None = None
    created_at: datetime
    message_count: int = 0
    messages: list[ChatMessageResponse] = Field(default_factory=list)


class ConversationHistoryResponse(BaseModel):
    """List of user conversation threads."""

    conversations: list[ConversationResponse]


class ChatFeedbackRequest(BaseModel):
    """Payload to record user sentiment or rating for an assistant message."""

    model_config = ConfigDict(extra="forbid")

    feedback: int = Field(
        ...,
        ge=-1,
        le=5,
        description="Rating or sentiment: -1 for unhelpful, 1 for helpful, or 1 to 5 star scale",
    )


class ChatFeedbackResponse(BaseModel):
    """Acknowledgment of recorded feedback."""

    message_id: uuid.UUID
    feedback: int
    status: str = "recorded"
