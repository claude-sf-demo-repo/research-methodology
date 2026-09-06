# tests/test_credibility_event.py
from research_methodology.credibility import validate_credibility_event
from research_methodology.validation import ErrorCode


def _feedback():
    return {
        "event_id": "e1", "schema_version": 2, "domain": "example.com", "topic": "plumbing",
        "kind": "feedback", "positive": True, "explicit": True, "cluster_id": "c1",
        "volatility_class": "moderate", "authority_class": "medium",
    }


def test_valid_feedback_passes():
    assert validate_credibility_event(_feedback()).ok


def test_feedback_missing_cluster_id_is_constraint_violation():
    p = _feedback()
    del p["cluster_id"]
    res = validate_credibility_event(p)
    assert any(e.code is ErrorCode.CONSTRAINT_VIOLATION and e.locus == "cluster_id"
               for e in res.errors)


def test_blocklist_needs_no_feedback_fields():
    p = {
        "event_id": "e2", "schema_version": 2, "domain": "spam.example", "topic": "plumbing",
        "kind": "blocklist", "volatility_class": "moderate", "authority_class": "low",
    }
    assert validate_credibility_event(p).ok
