"""Two-phase intent-score validation (§9.1)."""
from __future__ import annotations

from research_methodology.schemas import INTENT_SCORE_SCHEMA
from research_methodology.validation import (
    ErrorCode, ValidationError, ValidationResult, validate,
)

_REQUIRED_BUDGET_KEYS = ("soft_max_calls", "breadth", "depth")


def validate_intent_score(payload: dict) -> ValidationResult:
    base = validate(payload, INTENT_SCORE_SCHEMA)
    errors = list(base.errors)

    dims = payload.get("dimensions")
    if isinstance(dims, dict):
        for dim_name, dim in dims.items():
            if not isinstance(dim, dict) or "intended_band" not in dim:
                errors.append(ValidationError(
                    ErrorCode.CONSTRAINT_VIOLATION,
                    f"dimensions.{dim_name}.intended_band",
                    f"dimension '{dim_name}' must carry an intended_band"))

    budget = payload.get("budget")
    if isinstance(budget, dict):
        for key in _REQUIRED_BUDGET_KEYS:
            if key not in budget:
                errors.append(ValidationError(
                    ErrorCode.CONSTRAINT_VIOLATION, f"budget.{key}",
                    f"budget must derive '{key}' from the provisional score"))

    return ValidationResult(ok=not errors, errors=tuple(errors))
