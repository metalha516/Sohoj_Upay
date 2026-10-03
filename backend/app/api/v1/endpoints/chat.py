"""Chat API endpoints for conversational coaching, SSE streaming, and message feedback."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse

from app.api.deps import get_chat_service, get_current_user
from app.models.user import User
from app.schemas.chat import (
    ChatFeedbackRequest,
    ChatFeedbackResponse,
    ChatRequest,
    ChatResponse,
    ConversationHistoryResponse,
)
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post(
    "",
    summary="Submit message to conversational financial coach (SSE or JSON)",
    response_model=None,
    responses={
        200: {
            "description": "JSON response or text/event-stream SSE stream depending on stream parameter",
            "content": {
                "application/json": {"schema": ChatResponse.model_json_schema()},
                "text/event-stream": {},
            },
        },
    },
)
async def post_chat(
    request: Request,
    req: ChatRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
) -> Any:
    """Send a message to the AI coach."""
    from app.core.config import get_settings

    settings = get_settings()
    if not settings.ai_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Conversational AI services are currently disabled by administrator.",
        )

    if req.stream:
        return StreamingResponse(
            chat_service.stream_chat(user_id=current_user.id, req=req),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    return await chat_service.process_chat(user_id=current_user.id, req=req)


@router.get(
    "/history",
    response_model=ConversationHistoryResponse,
    summary="Get user conversation history and message transcripts",
)
async def get_chat_history(
    current_user: Annotated[User, Depends(get_current_user)],
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
    conversation_id: Annotated[
        uuid.UUID | None, Query(description="Filter by specific conversation thread UUID")
    ] = None,
    limit: Annotated[int, Query(ge=1, le=50, description="Max conversation threads")] = 20,
) -> ConversationHistoryResponse:
    """Retrieve user conversation threads, message histories, and tool call metadata."""
    return await chat_service.get_history(
        user_id=current_user.id,
        conversation_id=conversation_id,
        limit=limit,
    )


@router.post(
    "/{message_id}/feedback",
    response_model=ChatFeedbackResponse,
    summary="Record sentiment feedback on an assistant message",
)
async def post_chat_feedback(
    message_id: uuid.UUID,
    req: ChatFeedbackRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
) -> ChatFeedbackResponse:
    """Submit user feedback (+1 / -1 rating) on an assistant message."""
    try:
        return await chat_service.submit_feedback(
            user_id=current_user.id,
            message_id=message_id,
            feedback=req.feedback,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
