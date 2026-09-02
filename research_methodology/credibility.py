"""Credibility-event validation (§9.4)."""
from __future__ import annotations

from research_methodology.schemas import CREDIBILITY_EVENT_SCHEMA
from research_methodology.validation import (
    ErrorCode, ValidationError, ValidationResult, validate,
)

_FEEDBACK_FIELDS = {"positive": bool, "explicit": bool, "cluster_id": str}


def validate_credibility_event(payload: dict) -> ValidationResult:
    base = validate(payload, CREDIBILITY_EVENT_SCHEMA)
    errors = list(base.errors)

    if payload.get("kind") == "feedback":
        for field_name, expected in _FEEDBACK_FIELDS.items():
            if field_name not in payload:
                errors.append(ValidationError(
                    ErrorCode.CONSTRAINT_VIOLATION, field_name,
                    f"feedback event requires '{field_name}'"))
            elif not isinstance(payload[field_name], expected):
                errors.append(ValidationError(
                    ErrorCode.WRONG_TYPE, field_name,
                    f"expected {expected.__name__}"))

    return ValidationResult(ok=not errors, errors=tuple(errors))
