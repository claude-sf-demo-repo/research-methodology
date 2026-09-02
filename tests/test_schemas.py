from research_methodology import schemas as S
from research_methodology import constants as C


def test_all_schemas_registered():
    assert set(S.ALL_SCHEMAS) == {"intent_score", "episode", "credibility_event"}


def test_episode_schema_enumerates_volatility_and_authority_from_ssot():
    ep = S.EPISODE_SCHEMA
    assert ep.enums["volatility_class"] == {v.value for v in C.VolatilityClass}
    assert ep.enums["authority_class"] == {a.value for a in C.AuthorityClass}
    assert "schema_version" in ep.required and "episode_id" in ep.required


def test_credibility_event_requires_event_id_for_idempotency():
    assert "event_id" in S.CREDIBILITY_EVENT_SCHEMA.required
