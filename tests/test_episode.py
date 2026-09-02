from research_methodology.episode import validate_episode
from research_methodology.validation import ErrorCode


def _valid_episode():
    return {
        "episode_id": "ep1", "session_id": "s1", "timestamp": "2026-09-02T00:00:00Z",
        "schema_version": 2, "episode_type": "source_citation", "data_class": "raw_content",
        "content": "1/2-inch NPT fitting complies with UPC 605.",
        "volatility_class": "durable", "authority_class": "canonical",
        "source_metadata": {"url": "https://example.gov/upc605", "title": "UPC 605"},
    }


def test_valid_episode_passes():
    assert validate_episode(_valid_episode()).ok


def test_source_metadata_without_url_is_constraint_violation():
    p = _valid_episode()
    p["source_metadata"] = {"title": "no url"}
    res = validate_episode(p)
    assert any(e.code is ErrorCode.CONSTRAINT_VIOLATION and e.locus == "source_metadata.url"
               for e in res.errors)


def test_raw_content_requires_nonempty_content():
    p = _valid_episode()
    p["content"] = ""
    res = validate_episode(p)
    assert any(e.code is ErrorCode.CONSTRAINT_VIOLATION and e.locus == "content"
               for e in res.errors)
