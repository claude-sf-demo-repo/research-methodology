from research_methodology.intent import validate_intent_score
from research_methodology.validation import ErrorCode


def _valid_intent():
    return {
        "session_id": "s1", "timestamp": "2026-09-02T00:00:00Z", "schema_version": 2,
        "derived_label": "deep-research",
        "dimensions": {
            "depth": {"intended_band": "0.6-0.8"},
            "rigor": {"intended_band": "0.9-1.0"},
        },
        "budget": {"soft_max_calls": 20, "breadth": 5, "depth": 2},
    }


def test_valid_intent_passes():
    assert validate_intent_score(_valid_intent()).ok


def test_dimension_without_intended_band_is_constraint_violation():
    p = _valid_intent()
    p["dimensions"]["depth"] = {}  # no intended_band
    res = validate_intent_score(p)
    assert not res.ok
    assert any(e.code is ErrorCode.CONSTRAINT_VIOLATION and e.locus == "dimensions.depth.intended_band"
               for e in res.errors)


def test_missing_budget_key_is_constraint_violation():
    p = _valid_intent()
    del p["budget"]["breadth"]
    res = validate_intent_score(p)
    assert any(e.code is ErrorCode.CONSTRAINT_VIOLATION and e.locus == "budget.breadth"
               for e in res.errors)
