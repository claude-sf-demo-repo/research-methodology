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


# --- append to research_methodology/credibility.py ---
from dataclasses import dataclass

from research_methodology.constants import (
    EXPLICIT_MULTIPLIER, AuthorityClass, VolatilityClass,
)
from research_methodology.volatility import policy


@dataclass(frozen=True)
class CredEvent:
    event_id: str
    ts_days: float
    kind: str            # "feedback" | "blocklist" | "unblock"
    positive: bool
    explicit: bool
    volatility_class: VolatilityClass
    authority_class: AuthorityClass
    cluster_id: str


@dataclass(frozen=True)
class CredState:
    score: float
    confidence: str      # "high" | "provisional"
    blocked: bool
    evidence_clusters: int


def _dedupe(events: list[CredEvent]) -> list[CredEvent]:
    seen: set[str] = set()
    out: list[CredEvent] = []
    for e in events:
        if e.event_id in seen:
            continue
        seen.add(e.event_id)
        out.append(e)
    return out


def fold(events: list[CredEvent], now_days: float) -> CredState:
    uniq = _dedupe(events)

    block_events = [e for e in uniq if e.kind in ("blocklist", "unblock")]
    blocked = bool(block_events) and max(
        block_events, key=lambda e: e.ts_days).kind == "blocklist"

    feedback = [e for e in uniq if e.kind == "feedback"]
    score = 0.0
    all_clusters: set[str] = set()
    explicit_clusters: set[str] = set()
    # Use the strictest (max) min-evidence among classes present.
    min_clusters, min_explicit = 1, 0

    for e in feedback:
        pol = policy(e.volatility_class, e.authority_class)
        if pol.half_life_days is None:
            decay = 1.0
        else:
            decay = 0.5 ** ((now_days - e.ts_days) / pol.half_life_days)
        magnitude = (EXPLICIT_MULTIPLIER if e.explicit else 1.0) * decay
        score += magnitude if e.positive else -magnitude
        all_clusters.add(e.cluster_id)
        if e.explicit:
            explicit_clusters.add(e.cluster_id)
        min_clusters = max(min_clusters, pol.min_evidence_clusters)
        min_explicit = max(min_explicit, pol.min_explicit)

    meets_evidence = (
        not blocked
        and score > 0
        and len(all_clusters) >= min_clusters
        and len(explicit_clusters) >= min_explicit
    )
    confidence = "high" if meets_evidence else "provisional"
    return CredState(score, confidence, blocked, len(all_clusters))
