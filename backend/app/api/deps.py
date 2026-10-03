"""FastAPI request dependencies for authentication, database session, and RLS context."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator, Callable
from typing import Annotated, Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.agent import FinancialAgent
from app.ai.context.builder import ContextBuilder
from app.ai.llm.client import LLMClient
from app.ai.llm.gemini_client import GeminiLLMClient
from app.ai.llm.mock import MockLLM
from app.ai.llm.openai_client import OpenAILLMClient
from app.ai.prompts.loader import PromptManager
from app.ai.safety.circuit_breaker import (
    default_circuit_breaker,
    default_token_budget_manager,
)
from app.ai.safety.consent_gate import ConsentGate
from app.ai.tools.implementations import FinancialToolSet, register_financial_tools
from app.ai.tools.registry import ToolManager
from app.core.config import get_settings
from app.core.rate_limit import rate_limiter
from app.core.security import decode_access_token
from app.db.session import get_db as _get_db
from app.db.session import set_session_rls_user
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.services.auth_service import AuthService
from app.services.chat_service import ChatService
from app.services.dashboard_service import DashboardService
from app.services.goal_service import GoalService
from app.services.ml_service import MLService
from app.services.rag_service import RAGService
from app.services.simulation_service import SimulationService
from app.services.transaction_service import TransactionService
from app.services.user_service import UserService

# HTTP Bearer scheme
security_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield request-scoped AsyncSession."""
    async for session in _get_db():
        yield session


async def get_current_user(
    request: Request,
    auth: Annotated[HTTPAuthorizationCredentials | None, Depends(security_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Validate JWT access token, inject PostgreSQL RLS session context, and return User.

    Executes `SET LOCAL app.user_id = :user_id` on the database session per security.md §4.
    """
    if not auth or not auth.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth.credentials

    # 1. Decode & validate token claims (sub, exp, iss, aud, jti, pinned alg)
    try:
        payload = decode_access_token(token)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired authentication token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject identifier.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = uuid.UUID(sub)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid subject UUID format.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    # 2. Fetch user from repository
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id_for_user(user_id, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account does not exist or has been terminated.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Inject PostgreSQL Row-Level Security (RLS) context
    await set_session_rls_user(db, user_id)

    # Store user in request state for downstream logging/middleware
    request.state.user = user

    return user


async def get_current_user_optional(
    request: Request,
    auth: Annotated[HTTPAuthorizationCredentials | None, Depends(security_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User | None:
    """Optional user dependency for routes that allow guest or authenticated access."""
    if not auth or not auth.credentials:
        return None
    try:
        return await get_current_user(request, auth, db)
    except HTTPException:
        return None


def get_auth_service(db: Annotated[AsyncSession, Depends(get_db)]) -> AuthService:
    """Dependency for AuthService."""
    return AuthService(db)


def get_user_service(db: Annotated[AsyncSession, Depends(get_db)]) -> UserService:
    """Dependency for UserService."""
    return UserService(db)


def get_transaction_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TransactionService:
    """Dependency for TransactionService."""
    return TransactionService(db)


def get_goal_service(db: Annotated[AsyncSession, Depends(get_db)]) -> GoalService:
    """Dependency for GoalService."""
    return GoalService(db)


def get_dashboard_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DashboardService:
    """Dependency for DashboardService."""
    return DashboardService(db)


def get_ml_service(db: Annotated[AsyncSession, Depends(get_db)]) -> MLService:
    """Dependency for MLService."""
    return MLService(db)


def get_simulation_service() -> SimulationService:
    """Dependency for SimulationService (pure deterministic)."""
    return SimulationService()


def get_rag_service(db: Annotated[AsyncSession, Depends(get_db)]) -> RAGService:
    """Dependency for RAGService."""
    return RAGService(db_session=db)


def get_chat_service(db: Annotated[AsyncSession, Depends(get_db)]) -> ChatService:
    """Dependency factory for ChatService with tool registration and safety guards."""
    user_service = UserService(db)
    transaction_service = TransactionService(db)
    dashboard_service = DashboardService(db)
    goal_service = GoalService(db)
    ml_service = MLService(db)
    rag_service = RAGService(db_session=db)

    toolset = FinancialToolSet(
        user_service=user_service,
        transaction_service=transaction_service,
        dashboard_service=dashboard_service,
        goal_service=goal_service,
        ml_service=ml_service,
        rag_service=rag_service,
    )
    tool_manager = ToolManager()
    register_financial_tools(tool_manager, toolset)

    context_builder = ContextBuilder(
        dashboard_service=dashboard_service,
        goal_service=goal_service,
        ml_service=ml_service,
    )

    settings = get_settings()
    llm_client: LLMClient
    if settings.llm_provider == "gemini" and (settings.gemini_api_key or settings.llm_api_key):
        llm_client = GeminiLLMClient(
            api_key=settings.gemini_api_key or settings.llm_api_key,
            model=settings.gemini_model,
        )
    elif settings.llm_provider == "openai" and settings.llm_api_key:
        llm_client = OpenAILLMClient(
            api_key=settings.llm_api_key,
            model=settings.llm_model,
        )
    else:
        llm_client = MockLLM()

    agent = FinancialAgent(
        llm_client=llm_client,
        tool_manager=tool_manager,
        context_builder=context_builder,
        prompt_manager=PromptManager(),
        consent_gate=ConsentGate(user_service),
    )

    return ChatService(
        session=db,
        agent=agent,
        user_service=user_service,
        token_budget_mgr=default_token_budget_manager,
        circuit_breaker=default_circuit_breaker,
    )


def rate_limit_dependency(max_requests: int, window_seconds: int = 60) -> Callable[..., Any]:
    """Factory creating route-specific rate limiting dependency."""

    async def _check_rate_limit(request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        key = f"rate_limit:{client_ip}:{path}"

        allowed, count, retry_after = await rate_limiter.is_allowed(
            key, max_requests=max_requests, window_seconds=window_seconds
        )
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded ({count}/{max_requests}). Please retry in {retry_after}s.",
                headers={"Retry-After": str(retry_after)},
            )

    return _check_rate_limit
