"""Deterministic source weighting (§5.1)."""
from __future__ import annotations

from research_methodology.constants import Tier, TIER_BASE_WEIGHT

# Freshness-required bands and the max source age (days) tolerated before penalizing.
_FRESHNESS_THRESHOLD_DAYS = {"0.9-1.0": 2.0, "0.6-0.8": 30.0}


def recency_fit(recency_band: str, source_age_days: float) -> float:
    threshold = _FRESHNESS_THRESHOLD_DAYS.get(recency_band)
    if threshold is None:
        return 1.0  # band does not demand freshness
    return 1.0 if source_age_days <= threshold else 0.5


def weight(tier: Tier, trust_score: float, recency_band: str,
           source_age_days: float, independence_factor: float) -> float:
    return (
        TIER_BASE_WEIGHT[tier]
        * trust_score
        * recency_fit(recency_band, source_age_days)
        * independence_factor
    )
