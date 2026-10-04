"""Unit tests for MFS Provider enum, Upay support, and transaction payloads."""

from decimal import Decimal
import pytest
from app.ai.safety.input_guard import FINANCIAL_KEYWORDS, GuardResult, InputGuard
from app.schemas.transaction import (
    CashoutCreateRequest,
    MFSProvider,
    TransactionCreateRequest,
    TransactionResponse,
    TxnPurpose,
    TxnType,
)


def test_mfs_provider_enum_members():
    """Verify all supported Bangladeshi MFS channels are defined in MFSProvider."""
    assert MFSProvider.BKASH == "bkash"
    assert MFSProvider.NAGAD == "nagad"
    assert MFSProvider.ROCKET == "rocket"
    assert MFSProvider.UPAY == "upay"
    assert MFSProvider.BANK == "bank"
    assert MFSProvider.OTHER == "other"


def test_transaction_create_with_upay():
    """Verify TransactionCreateRequest accepts Upay as mfs_provider."""
    req = TransactionCreateRequest(
        amount=Decimal("1500.00"),
        transaction_type=TxnType.EXPENSE,
        purpose=TxnPurpose.NECESSITY,
        category="utilities",
        merchant="Upay BillPay - DESCO",
        mfs_provider=MFSProvider.UPAY,
        description="Electricity bill payment via Upay",
    )
    assert req.mfs_provider == MFSProvider.UPAY
    assert req.merchant == "Upay BillPay - DESCO"


def test_cashout_create_with_upay():
    """Verify CashoutCreateRequest accepts Upay with mandatory purpose."""
    req = CashoutCreateRequest(
        amount=Decimal("5000.00"),
        purpose=TxnPurpose.NECESSITY,
        category="rent",
        merchant="Upay Agent",
        mfs_provider=MFSProvider.UPAY,
        description="Upay Agent Cash-Out (1.4% Tariff)",
    )
    assert req.mfs_provider == MFSProvider.UPAY
    assert req.purpose == TxnPurpose.NECESSITY


def test_input_guard_recognizes_upay():
    """Verify input guard recognizes Upay as a valid financial keyword."""
    assert "upay" in FINANCIAL_KEYWORDS
    guard = InputGuard()
    res = guard.check_input("Can you show my Upay cash out transactions this month?")
    assert res.is_safe is True
    assert res.is_in_scope is True
