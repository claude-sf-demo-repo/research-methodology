"""Episode validation (§9.2)."""
from __future__ import annotations

from research_methodology.schemas import EPISODE_SCHEMA
from research_methodology.validation import (
    ErrorCode, ValidationError, ValidationResult, validate,
)


def validate_episode(payload: dict) -> ValidationResult:
    base = validate(payload, EPISODE_SCHEMA)
    errors = list(base.errors)

    meta = payload.get("source_metadata")
    if isinstance(meta, dict) and not meta.get("url"):
        errors.append(ValidationError(
            ErrorCode.CONSTRAINT_VIOLATION, "source_metadata.url",
            "every source_citation episode needs a URL-level citation"))

    if payload.get("data_class") == "raw_content" and not payload.get("content"):
        errors.append(ValidationError(
            ErrorCode.CONSTRAINT_VIOLATION, "content",
            "data_class=raw_content requires non-empty content"))

    return ValidationResult(ok=not errors, errors=tuple(errors))
