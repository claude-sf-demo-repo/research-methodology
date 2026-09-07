# tests/test_credibility_store.py
from research_methodology.storage.credibility_store import CredibilityStore
from research_methodology.storage.event_log import SQLiteEventLog


def _store(tmp_path):
    return CredibilityStore(SQLiteEventLog(tmp_path / "events.db"))


def _fb(event_id, domain, topic, cluster, ts=0.0, positive=True, explicit=True,
        vc="moderate", ac="medium"):
    return {
        "event_id": event_id, "schema_version": 2, "domain": domain, "topic": topic,
        "kind": "feedback", "ts_days": ts, "positive": positive, "explicit": explicit,
        "cluster_id": cluster, "volatility_class": vc, "authority_class": ac,
    }


def test_records_fold_into_state(tmp_path):
    store = _store(tmp_path)
    for i in range(4):
        store.record(_fb(f"e{i}", "example.com", "plumbing", f"c{i}"))
    st = store.state("example.com", "plumbing", now_days=0.0)
    assert st.confidence == "high"      # MODERATE needs >=4 clusters incl >=1 explicit
    assert st.score > 0


def test_record_is_idempotent(tmp_path):
    store = _store(tmp_path)
    assert store.record(_fb("e1", "d", "t", "c1")) is True
    assert store.record(_fb("e1", "d", "t", "c1")) is False
    assert store.state("d", "t", now_days=0.0).evidence_clusters == 1


def test_blocklist_event_blocks(tmp_path):
    store = _store(tmp_path)
    store.record(_fb("e1", "spam.example", "plumbing", "c1"))
    store.record({
        "event_id": "b1", "schema_version": 2, "domain": "spam.example",
        "topic": "plumbing", "kind": "blocklist", "ts_days": 1.0,
        "volatility_class": "moderate", "authority_class": "low",
    })
    assert store.state("spam.example", "plumbing", now_days=2.0).blocked is True


def test_keys_reports_domain_topic_volatility(tmp_path):
    store = _store(tmp_path)
    store.record(_fb("e1", "d1", "physics", "c1", vc="durable"))
    store.record(_fb("e2", "d2", "news", "c1", vc="fast"))
    assert set(store.keys()) == {("d1", "physics", "durable"), ("d2", "news", "fast")}
