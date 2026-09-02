"""Generic schema validator implementing the §9.3 error taxonomy."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from research_methodology.schemas import Schema


class ErrorCode(str, Enum):
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    WRONG_TYPE = "WRONG_TYPE"
    ENUM_VIOLATION = "ENUM_VIOLATION"
    EXTRA_FIELD = "EXTRA_FIELD"
    MALFORMED_JSON = "MALFORMED_JSON"
    CONSTRAINT_VIOLATION = "CONSTRAINT_VIOLATION"


@dataclass(frozen=True)
class ValidationError:
    code: ErrorCode
    locus: str  # field name or rule name
    message: str


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: tuple[ValidationError, ...]


def validate(payload: dict, schema: Schema) -> ValidationResult:
    errors: list[ValidationError] = []

    if not isinstance(payload, dict):
        return ValidationResult(
            False,
            (ValidationError(ErrorCode.MALFORMED_JSON, "<root>", "payload is not an object"),),
        )

    for field_name, expected_type in schema.required.items():
        if field_name not in payload:
            errors.append(ValidationError(
                ErrorCode.MISSING_REQUIRED_FIELD, field_name,
                f"required field '{field_name}' is missing"))
            continue
        value = payload[field_name]
        # bool is a subclass of int; reject the mismatch explicitly.
        if expected_type is int and isinstance(value, bool):
            errors.append(ValidationError(
                ErrorCode.WRONG_TYPE, field_name, "expected int, got bool"))
        elif not isinstance(value, expected_type):
            errors.append(ValidationError(
                ErrorCode.WRONG_TYPE, field_name,
                f"expected {expected_type.__name__}, got {type(value).__name__}"))

    for field_name, allowed in schema.enums.items():
        if field_name in payload and payload[field_name] not in allowed:
            errors.append(ValidationError(
                ErrorCode.ENUM_VIOLATION, field_name,
                f"'{payload[field_name]}' not in {sorted(allowed)}"))

    if not schema.allow_extra:
        for key in payload:
            if key not in schema.required:
                errors.append(ValidationError(
                    ErrorCode.EXTRA_FIELD, key, f"unexpected field '{key}'"))

    return ValidationResult(ok=not errors, errors=tuple(errors))
