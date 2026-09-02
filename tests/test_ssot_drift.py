# tests/test_ssot_drift.py
from research_methodology import constants as C
from research_methodology import schemas as S


def test_episode_enums_track_ssot_exactly():
    assert S.EPISODE_SCHEMA.enums["volatility_class"] == {v.value for v in C.VolatilityClass}
    assert S.EPISODE_SCHEMA.enums["authority_class"] == {a.value for a in C.AuthorityClass}


def test_intent_label_enum_tracks_ssot_exactly():
    assert S.INTENT_SCORE_SCHEMA.enums["derived_label"] == {d.value for d in C.DerivedLabel}


def test_every_volatility_and_authority_member_is_covered_by_policy_tables():
    assert set(C.VOLATILITY_POLICY) == set(C.VolatilityClass)
    assert set(C.AUTHORITY_MULTIPLIER) == set(C.AuthorityClass)


def test_every_tier_member_has_a_base_weight():
    assert set(C.TIER_BASE_WEIGHT) == set(C.Tier)
