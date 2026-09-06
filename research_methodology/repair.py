"""Bounded validation/repair loop with stagnation detection (§9.3)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from research_methodology.schemas import Schema
from research_methodology.validation import ValidationError, validate

AttemptFn = Callable[[dict, tuple[ValidationError, ...]], dict]


def is_stagnant(prev: ValidationError, cur: ValidationError) -> bool:
    """Same category iff equal code AND locus (§9.3)."""
    return prev.code is cur.code and prev.locus == cur.locus


@dataclass(frozen=True)
class RepairOutcome:
    ok: bool
    payload: dict | None
    write_failure_reason: str | None
    attempts: int


def repair(payload: dict, schema: Schema, attempt_fn: AttemptFn,
           max_attempts: int = 3) -> RepairOutcome:
    current = payload
    prev_first_error: ValidationError | None = None

    for attempt in range(1, max_attempts + 1):
        result = validate(current, schema)
        if result.ok:
            return RepairOutcome(True, current, None, attempt)

        first = result.errors[0]
        if prev_first_error is not None and is_stagnant(prev_first_error, first):
            return RepairOutcome(
                False, None,
                f"stagnation: repeated {first.code.value} at '{first.locus}'",
                attempt)
        prev_first_error = first
        current = attempt_fn(current, result.errors)

    final = validate(current, schema)
    if final.ok:
        return RepairOutcome(True, current, None, max_attempts)
    return RepairOutcome(
        False, None, f"max_attempts ({max_attempts}) exhausted", max_attempts)
