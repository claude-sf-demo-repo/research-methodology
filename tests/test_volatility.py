# tests/test_volatility.py
from research_methodology.volatility import policy
from research_methodology.constants import VolatilityClass as V, AuthorityClass as A


def test_durable_stays_infinite_under_any_authority():
    p = policy(V.DURABLE, A.LOW)
    assert p.half_life_days is None and p.staleness_days is None
    assert p.min_evidence_clusters == 1


def test_canonical_authority_lengthens_moderate_half_life():
    base = policy(V.MODERATE, A.MEDIUM)
    high = policy(V.MODERATE, A.CANONICAL)
    assert base.half_life_days == 180.0
    assert high.half_life_days == 360.0  # 180 * 2.0


def test_authority_relaxes_min_evidence_but_never_below_one():
    fast_medium = policy(V.FAST, A.MEDIUM)
    fast_canonical = policy(V.FAST, A.CANONICAL)
    assert fast_medium.min_evidence_clusters == 4
    assert fast_canonical.min_evidence_clusters == 2   # ceil(4 / 2.0)
    assert policy(V.EPHEMERAL, A.CANONICAL).min_evidence_clusters == 1
