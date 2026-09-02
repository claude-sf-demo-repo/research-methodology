"""Payload schemas expressed as data, so validator and drift-check can both read them."""
from __future__ import annotations

from dataclasses import dataclass, field

from research_methodology import constants as C


@dataclass(frozen=True)
class Schema:
    name: str
    required: dict[str, type]
    enums: dict[str, set[str]] = field(default_factory=dict)
    allow_extra: bool = True


_VOL = {v.value for v in C.VolatilityClass}
_AUTH = {a.value for a in C.AuthorityClass}
_TIER = {t.value for t in C.Tier}
_LABEL = {d.value for d in C.DerivedLabel}

INTENT_SCORE_SCHEMA = Schema(
    name="intent_score",
    required={
        "session_id": str,
        "timestamp": str,
        "schema_version": int,
        "dimensions": dict,
        "derived_label": str,
        "budget": dict,
    },
    enums={"derived_label": _LABEL},
    allow_extra=True,
)

EPISODE_SCHEMA = Schema(
    name="episode",
    required={
        "episode_id": str,
        "session_id": str,
        "timestamp": str,
        "schema_version": int,
        "episode_type": str,
        "data_class": str,
        "content": str,
        "volatility_class": str,
        "authority_class": str,
        "source_metadata": dict,
    },
    enums={"volatility_class": _VOL, "authority_class": _AUTH},
    allow_extra=True,
)

CREDIBILITY_EVENT_SCHEMA = Schema(
    name="credibility_event",
    required={
        "event_id": str,
        "schema_version": int,
        "domain": str,
        "topic": str,
        "kind": str,
        "volatility_class": str,
        "authority_class": str,
    },
    enums={
        "kind": {"feedback", "blocklist", "unblock"},
        "volatility_class": _VOL,
        "authority_class": _AUTH,
    },
    allow_extra=True,
)

ALL_SCHEMAS: dict[str, Schema] = {
    s.name: s for s in (INTENT_SCORE_SCHEMA, EPISODE_SCHEMA, CREDIBILITY_EVENT_SCHEMA)
}
