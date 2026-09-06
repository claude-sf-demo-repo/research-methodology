from research_methodology.repair import repair, is_stagnant
from research_methodology.validation import ValidationError, ErrorCode
from research_methodology.schemas import CREDIBILITY_EVENT_SCHEMA


def _base():
    return {
        "event_id": "e1", "schema_version": 2, "domain": "d", "topic": "t",
        "kind": "feedback", "volatility_class": "moderate", "authority_class": "medium",
    }


def test_already_valid_returns_immediately():
    out = repair(_base(), CREDIBILITY_EVENT_SCHEMA, attempt_fn=lambda p, e: p)
    assert out.ok and out.attempts == 1


def test_successful_single_repair():
    broken = _base()
    broken["schema_version"] = "2"  # wrong type

    def fix(p, errors):
        p = dict(p)
        p["schema_version"] = 2
        return p

    out = repair(broken, CREDIBILITY_EVENT_SCHEMA, attempt_fn=fix)
    assert out.ok and out.payload["schema_version"] == 2


def test_stagnation_short_circuits_to_write_failure():
    broken = _base()
    del broken["domain"]  # MISSING_REQUIRED_FIELD @ domain, repeatedly unfixed

    out = repair(broken, CREDIBILITY_EVENT_SCHEMA, attempt_fn=lambda p, e: dict(p))
    assert not out.ok
    assert "stagnation" in out.write_failure_reason.lower()
    assert out.attempts == 2  # detected on the second identical failure


def test_is_stagnant_same_code_and_locus():
    a = ValidationError(ErrorCode.MISSING_REQUIRED_FIELD, "domain", "x")
    b = ValidationError(ErrorCode.MISSING_REQUIRED_FIELD, "domain", "y")
    c = ValidationError(ErrorCode.MISSING_REQUIRED_FIELD, "topic", "z")
    assert is_stagnant(a, b) is True
    assert is_stagnant(a, c) is False
