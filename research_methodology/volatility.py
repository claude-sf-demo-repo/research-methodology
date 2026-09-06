"""Authority-scaled volatility policy lookup (§5.3)."""
from __future__ import annotations

import math
from dataclasses import dataclass

from research_methodology.constants import (
    AUTHORITY_MULTIPLIER, VOLATILITY_POLICY, AuthorityClass, VolatilityClass,
)


@dataclass(frozen=True)
class ResolvedPolicy:
    half_life_days: float | None
    staleness_days: float | None
    min_evidence_clusters: int
    min_explicit: int
    retention: str


def policy(vc: VolatilityClass, ac: AuthorityClass) -> ResolvedPolicy:
    row = VOLATILITY_POLICY[vc]
    mult = AUTHORITY_MULTIPLIER[ac]

    half_life = None if row.half_life_days is None else row.half_life_days * mult
    staleness = None if row.staleness_days is None else row.staleness_days * mult
    # Higher authority -> fewer independent clusters needed, floored at 1.
    # If half-life or staleness are infinite (None), min_evidence_clusters stays unchanged.
    if row.half_life_days is None or row.staleness_days is None:
        min_clusters = row.min_evidence_clusters
    else:
        min_clusters = max(1, math.ceil(row.min_evidence_clusters / mult))

    return ResolvedPolicy(
        half_life_days=half_life,
        staleness_days=staleness,
        min_evidence_clusters=min_clusters,
        min_explicit=row.min_explicit,
        retention=row.retention,
    )
