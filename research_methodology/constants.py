"""Single source of truth for tiers, the volatility policy table, and fold constants.

No other module may hard-code these values. Task 0.15 enforces SSOT<->schema agreement.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

SCHEMA_VERSION = 2
EXPLICIT_MULTIPLIER = 3.0  # §9.4: explicit feedback weighted 3x implicit


class VolatilityClass(str, Enum):
    DURABLE = "durable"
    SLOW = "slow"
    MODERATE = "moderate"
    FAST = "fast"
    EPHEMERAL = "ephemeral"


class AuthorityClass(str, Enum):
    CANONICAL = "canonical"   # canonical textbook, ISO/ASTM, Mayo/AMA
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"               # blog / influencer


class Tier(str, Enum):
    THEORETICAL = "theoretical"
    REGULATORY = "regulatory"
    EMPIRICAL = "empirical"


class DerivedLabel(str, Enum):
    QUICK_LOOKUP = "quick-lookup"
    DEEP_RESEARCH = "deep-research"
    ACADEMIC = "academic"
    PURCHASE_DECISION = "purchase-decision"
    PLANNING = "planning"


# §5.1 tier base weights (documented constants; tunable).
TIER_BASE_WEIGHT: dict[Tier, float] = {
    Tier.THEORETICAL: 1.0,
    Tier.REGULATORY: 1.0,
    Tier.EMPIRICAL: 0.6,
}


@dataclass(frozen=True)
class PolicyRow:
    """One row of the §5.3 policy table. None = infinite (no decay / never stale)."""
    half_life_days: float | None
    staleness_days: float | None
    min_evidence_clusters: int
    min_explicit: int
    retention: str  # "permanent" | "long" | "claim+provenance" | "provenance-only" | "observation-only"


# §5.3 / §9.4 class-keyed policy table. The MODERATE row IS the recommended baseline defaults.
VOLATILITY_POLICY: dict[VolatilityClass, PolicyRow] = {
    VolatilityClass.DURABLE:   PolicyRow(None, None, 1, 0, "permanent"),
    VolatilityClass.SLOW:      PolicyRow(1095.0, 1095.0, 3, 1, "long"),
    VolatilityClass.MODERATE:  PolicyRow(180.0, 90.0, 4, 1, "claim+provenance"),
    VolatilityClass.FAST:      PolicyRow(60.0, 21.0, 4, 1, "provenance-only"),
    VolatilityClass.EPHEMERAL: PolicyRow(1.0, 1.0, 1, 0, "observation-only"),
}

# §5.3: authority scales the row — higher authority lengthens half-life and relaxes min-evidence.
AUTHORITY_MULTIPLIER: dict[AuthorityClass, float] = {
    AuthorityClass.CANONICAL: 2.0,
    AuthorityClass.HIGH: 1.5,
    AuthorityClass.MEDIUM: 1.0,
    AuthorityClass.LOW: 0.5,
}
