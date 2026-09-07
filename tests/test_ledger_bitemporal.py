from research_methodology.storage.ledger import InMemoryLedger


def _episode(episode_id, valid_at, invalid_at=None, session_id="s1"):
    return {
        "episode_id": episode_id, "session_id": session_id,
        "timestamp": valid_at, "schema_version": 2,
        "episode_type": "source_citation", "data_class": "raw_content",
        "content": "belief text", "volatility_class": "slow", "authority_class": "high",
        "source_metadata": {"url": "https://example.org/x", "title": "x"},
        "valid_at": valid_at, "invalid_at": invalid_at,
    }


def test_belief_held_within_validity_window():
    led = InMemoryLedger()
    led.write_episode(_episode("ep1", "2026-01-01T00:00:00Z", "2026-06-01T00:00:00Z"))
    assert [e["episode_id"] for e in led.beliefs_as_of("2026-03-01T00:00:00Z")] == ["ep1"]


def test_belief_expired_after_invalid_at():
    led = InMemoryLedger()
    led.write_episode(_episode("ep1", "2026-01-01T00:00:00Z", "2026-06-01T00:00:00Z"))
    assert led.beliefs_as_of("2026-09-01T00:00:00Z") == []


def test_belief_before_valid_at_excluded():
    led = InMemoryLedger()
    led.write_episode(_episode("ep1", "2026-05-01T00:00:00Z"))
    assert led.beliefs_as_of("2026-01-01T00:00:00Z") == []


def test_open_ended_belief_still_held():
    led = InMemoryLedger()
    led.write_episode(_episode("ep1", "2026-01-01T00:00:00Z", None))
    assert [e["episode_id"] for e in led.beliefs_as_of("2030-01-01T00:00:00Z")] == ["ep1"]


def test_beliefs_filter_by_session():
    led = InMemoryLedger()
    led.write_episode(_episode("ep1", "2026-01-01T00:00:00Z", None, "s1"))
    led.write_episode(_episode("ep2", "2026-01-01T00:00:00Z", None, "s2"))
    assert [e["episode_id"] for e in led.beliefs_as_of("2026-02-01T00:00:00Z", session_id="s2")] == ["ep2"]
