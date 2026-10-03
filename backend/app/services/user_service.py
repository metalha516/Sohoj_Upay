"""User service managing profile updates, data rights, and GDPR account deletion."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password
from app.models.goal import FinancialGoal
from app.models.transaction import Transaction
from app.models.user import User
from app.repositories.audit_repo import AuditLogRepository
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserDataExportResponse, UserResponse, UserUpdateRequest


class UserService:
    """Service handling user profile lifecycle and privacy operations per security.md §12."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)
        self.audit_repo = AuditLogRepository(session)

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        """Retrieve user by primary key ID."""
        return await self.user_repo.get_by_id(user_id)

    async def get_user(self, user_id: uuid.UUID) -> User | None:
        """Alias for get_user_by_id."""
        return await self.user_repo.get_by_id(user_id)

    async def get_profile(self, user: User) -> UserResponse:
        """Retrieve the sanitized profile for authenticated user."""
        return UserResponse.model_validate(user)

    async def update_profile(
        self,
        user: User,
        req: UserUpdateRequest,
        client_ip: str | None = None,
    ) -> User:
        """Update allowed profile attributes with strict mass-assignment prevention."""
        updated_fields: dict[str, object] = {}

        if req.name is not None:
            user.name = req.name.strip()
            updated_fields["name"] = user.name

        if req.monthly_income is not None:
            user.monthly_income = req.monthly_income
            updated_fields["monthly_income"] = str(user.monthly_income)

        if req.consent_ai is not None:
            old_consent = user.consent_ai
            user.consent_ai = req.consent_ai
            updated_fields["consent_ai"] = user.consent_ai

            await self.audit_repo.log_event(
                actor=str(user.id),
                action="USER_CONSENT_CHANGE",
                user_id=user.id,
                ip=client_ip,
                metadata={"old_consent": old_consent, "new_consent": user.consent_ai},
            )

        if updated_fields:
            await self.session.flush()
            await self.audit_repo.log_event(
                actor=str(user.id),
                action="USER_PROFILE_UPDATE",
                user_id=user.id,
                ip=client_ip,
                metadata={"updated_fields": list(updated_fields.keys())},
            )

        return user

    async def export_data(
        self,
        user: User,
        client_ip: str | None = None,
    ) -> UserDataExportResponse:
        """Generate comprehensive GDPR / user privacy data export."""
        # Query aggregate summary of transactions and goals
        txn_count_stmt = (
            select(func.count()).select_from(Transaction).where(Transaction.user_id == user.id)
        )
        txn_res = await self.session.execute(txn_count_stmt)
        txns_count = txn_res.scalar() or 0

        goal_stmt = select(FinancialGoal).where(FinancialGoal.user_id == user.id)
        goal_res = await self.session.execute(goal_stmt)
        goals = goal_res.scalars().all()

        goals_summary = [
            {
                "id": str(g.id),
                "name": g.name,
                "target_amount": str(g.target_amount),
                "current_amount": str(g.current_amount),
                "status": g.status,
            }
            for g in goals
        ]

        await self.audit_repo.log_event(
            actor=str(user.id),
            action="USER_DATA_EXPORT",
            user_id=user.id,
            ip=client_ip,
        )

        return UserDataExportResponse(
            user=UserResponse.model_validate(user),
            exported_at=datetime.now(UTC),
            summary={
                "total_transactions": txns_count,
                "goals": goals_summary,
                "consent_ai": user.consent_ai,
            },
        )

    async def delete_account(
        self,
        user: User,
        password: str,
        client_ip: str | None = None,
    ) -> None:
        """Permanently erase user account and all cascaded data upon password re-auth."""
        # 1. Re-authenticate password before destructive action
        if not verify_password(password, user.password_hash):
            await self.audit_repo.log_event(
                actor=str(user.id),
                action="USER_ACCOUNT_DELETE_FAILURE",
                user_id=user.id,
                ip=client_ip,
                metadata={"reason": "password_mismatch"},
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password. Account deletion aborted.",
            )

        user_id = user.id

        # 2. Delete user (foreign key cascade deletes transactions, goals, refresh tokens, chats, etc.)
        await self.session.delete(user)
        await self.session.flush()

        # 3. Log audit trail (actor retains user hash for non-repudiation)
        await self.audit_repo.log_event(
            actor=str(user_id),
            action="USER_ACCOUNT_DELETE",
            user_id=None,
            ip=client_ip,
            metadata={"deleted_user_id": str(user_id)},
        )
