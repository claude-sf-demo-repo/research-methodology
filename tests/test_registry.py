from research_methodology.storage.credibility_store import CredibilityStore
from research_methodology.storage.event_log import SQLiteEventLog
from research_methodology.storage.registry import TrustedSource, TrustedSourceRegistry


def _store(tmp_path):
    return CredibilityStore(SQLiteEventLog(tmp_path / "events.db"))


def _fb(event_id, domain, topic, cluster, vc, ac="canonical", ts=0.0):
    return {
        "event_id": event_id, "schema_version": 2, "domain": domain, "topic": topic,
        "kind": "feedback", "ts_days": ts, "positive": True, "explicit": True,
        "cluster_id": cluster, "volatility_class": vc, "authority_class": ac,
    }


def test_durable_high_confidence_source_is_registered(tmp_path):
    store = _store(tmp_path)
    store.record(_fb("e1", "physics.org", "physics", "c1", "durable"))  # durable: 1 source suffices
    reg = TrustedSourceRegistry(store)
    result = reg.query("physics", now_days=0.0)
    assert result == [TrustedSource("physics.org", "physics", "durable", result[0].score, "high")]
    assert result[0].score > 0


def test_moderate_class_is_excluded(tmp_path):
    store = _store(tmp_path)
    for i in range(4):
        store.record(_fb(f"e{i}", "blog.example", "tech", f"c{i}", "moderate", ac="medium"))
    assert TrustedSourceRegistry(store).query("tech", now_days=0.0) == []  # not durable/slow


def test_slow_below_evidence_bar_is_excluded(tmp_path):
    store = _store(tmp_path)
    # slow/medium needs >=3 clusters incl >=1 explicit; give only 1 cluster -> provisional
    store.record(_fb("e1", "guideline.org", "medical-consensus", "c1", "slow", ac="medium"))
    assert TrustedSourceRegistry(store).query("medical-consensus", now_days=0.0) == []


def test_blocked_durable_source_is_excluded(tmp_path):
    store = _store(tmp_path)
    store.record(_fb("e1", "bad.example", "physics", "c1", "durable"))
    store.record({
        "event_id": "b1", "schema_version": 2, "domain": "bad.example",
        "topic": "physics", "kind": "blocklist", "ts_days": 1.0,
        "volatility_class": "durable", "authority_class": "low",
    })
    assert TrustedSourceRegistry(store).query("physics", now_days=2.0) == []
