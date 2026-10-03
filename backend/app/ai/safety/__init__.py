"""Safety modules for AI financial agent."""

from app.ai.safety.advice_boundary import (
    STANDARD_PROJECTION_DISCLAIMER,
    AdviceBoundaryValidator,
    BoundaryResult,
)
from app.ai.safety.consent_gate import ConsentGate, ConsentRequiredError
from app.ai.safety.input_guard import GuardResult, InputGuard
from app.ai.safety.numeric_validator import GroundingResult, NumericGroundingValidator
from app.ai.safety.output_sanitizer import OutputSanitizer, SanitizedOutput

__all__ = [
    "STANDARD_PROJECTION_DISCLAIMER",
    "AdviceBoundaryValidator",
    "BoundaryResult",
    "ConsentGate",
    "ConsentRequiredError",
    "GroundingResult",
    "GuardResult",
    "InputGuard",
    "NumericGroundingValidator",
    "OutputSanitizer",
    "SanitizedOutput",
]
