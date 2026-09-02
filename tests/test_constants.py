# tests/test_constants.py
from research_methodology import constants as C


def test_every_volatility_class_has_a_policy_row():
    assert set(C.VOLATILITY_POLICY) == set(C.VolatilityClass)


def test_durable_is_permanent_and_moderate_is_the_baseline():
    durable = C.VOLATILITY_POLICY[C.VolatilityClass.DURABLE]
    assert durable.half_life_days is None and durable.staleness_days is None
    assert durable.min_evidence_clusters == 1

    moderate = C.VOLATILITY_POLICY[C.VolatilityClass.MODERATE]
    assert moderate.half_life_days == 180.0
    assert moderate.staleness_days == 90.0
    assert moderate.min_evidence_clusters == 4
    assert moderate.min_explicit == 1


def test_explicit_feedback_weighted_triple():
    assert C.EXPLICIT_MULTIPLIER == 3.0


def test_every_tier_has_a_base_weight():
    assert set(C.TIER_BASE_WEIGHT) == set(C.Tier)
    assert all(w > 0 for w in C.TIER_BASE_WEIGHT.values())
