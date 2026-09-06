from research_methodology.weighting import recency_fit, weight
from research_methodology.constants import Tier, TIER_BASE_WEIGHT


def test_recency_fit_penalizes_stale_source_when_freshness_required():
    assert recency_fit("0.9-1.0", source_age_days=10) == 0.5   # breaking news, 10d old
    assert recency_fit("0.9-1.0", source_age_days=0.5) == 1.0
    assert recency_fit("0.0-0.2", source_age_days=3650) == 1.0  # timeless: age irrelevant


def test_weight_is_product_of_factors():
    w = weight(Tier.THEORETICAL, trust_score=0.8, recency_band="0.0-0.2",
               source_age_days=100, independence_factor=0.5)
    assert w == TIER_BASE_WEIGHT[Tier.THEORETICAL] * 0.8 * 1.0 * 0.5


def test_empirical_tier_weighs_less_than_theoretical_all_else_equal():
    args = dict(trust_score=1.0, recency_band="0.0-0.2", source_age_days=0, independence_factor=1.0)
    assert weight(Tier.EMPIRICAL, **args) < weight(Tier.THEORETICAL, **args)
