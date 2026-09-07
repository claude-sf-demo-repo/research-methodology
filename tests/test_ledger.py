import pytest

from research_methodology.storage.ledger import InMemoryLedger, Ledger, LedgerWriteError


def _episode(episode_id="ep1", session_id="s1"):
    return {
        "episode_id": episode_id, "session_id": session_id,
        "timestamp": "2026-09-02T00:00:00Z", "schema_version": 2,
        "episode_type": "source_citation", "data_class": "raw_content",
        "content": "1/2-inch NPT fitting complies with UPC 605.",
        "volatility_class": "durable", "authority_class": "canonical",
        "source_metadata": {"url": "https://example.gov/upc605", "title": "UPC 605"},
    }


def test_write_then_get(tmp_path):
    led = InMemoryLedger()
    assert led.write_episode(_episode()) == "ep1"
    assert led.get("ep1")["content"].startswith("1/2-inch")


def test_invalid_episode_raises(tmp_path):
    led = InMemoryLedger()
    bad = _episode()
    bad["source_metadata"] = {"title": "no url"}   # fails validate_episode
    with pytest.raises(LedgerWriteError):
        led.write_episode(bad)


def test_write_is_idempotent_by_episode_id():
    led = InMemoryLedger()
    led.write_episode(_episode())
    led.write_episode(_episode())          # same id, no duplicate
    assert len(led.episodes()) == 1


def test_episodes_filter_by_session():
    led = InMemoryLedger()
    led.write_episode(_episode("ep1", "s1"))
    led.write_episode(_episode("ep2", "s2"))
    assert [e["episode_id"] for e in led.episodes(session_id="s2")] == ["ep2"]


def test_in_memory_ledger_is_a_ledger():
    assert isinstance(InMemoryLedger(), Ledger)
