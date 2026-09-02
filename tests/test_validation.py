from research_methodology.validation import validate, ErrorCode
from research_methodology.schemas import CREDIBILITY_EVENT_SCHEMA


def _valid_event():
    return {
        "event_id": "e1", "schema_version": 2, "domain": "example.com",
        "topic": "plumbing", "kind": "feedback",
        "volatility_class": "moderate", "authority_class": "medium",
    }


def test_valid_payload_passes():
    assert validate(_valid_event(), CREDIBILITY_EVENT_SCHEMA).ok


def test_missing_required_field_flagged_with_locus():
    p = _valid_event()
    del p["event_id"]
    res = validate(p, CREDIBILITY_EVENT_SCHEMA)
    assert not res.ok
    assert any(e.code is ErrorCode.MISSING_REQUIRED_FIELD and e.locus == "event_id"
               for e in res.errors)


def test_wrong_type_flagged():
    p = _valid_event()
    p["schema_version"] = "2"  # str, expected int
    res = validate(p, CREDIBILITY_EVENT_SCHEMA)
    assert any(e.code is ErrorCode.WRONG_TYPE and e.locus == "schema_version"
               for e in res.errors)


def test_enum_violation_flagged():
    p = _valid_event()
    p["kind"] = "sabotage"
    res = validate(p, CREDIBILITY_EVENT_SCHEMA)
    assert any(e.code is ErrorCode.ENUM_VIOLATION and e.locus == "kind" for e in res.errors)
