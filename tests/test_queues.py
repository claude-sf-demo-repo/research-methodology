from research_methodology.storage.event_log import SQLiteEventLog
from research_methodology.storage.queues import RSSLog, WriteFailureQueue


def test_rss_log_records_every_item(tmp_path):
    rss = RSSLog(SQLiteEventLog(tmp_path / "events.db"))
    assert rss.log_item("i1", {"title": "Quake in region"}) is True
    assert rss.log_item("i2", {"title": "Budget released"}) is True
    assert [it["title"] for it in rss.items()] == ["Quake in region", "Budget released"]


def test_rss_log_is_idempotent(tmp_path):
    rss = RSSLog(SQLiteEventLog(tmp_path / "events.db"))
    rss.log_item("i1", {"title": "x"})
    assert rss.log_item("i1", {"title": "x"}) is False
    assert len(rss.items()) == 1


def test_write_failures_record_and_drain(tmp_path):
    q = WriteFailureQueue(SQLiteEventLog(tmp_path / "events.db"))
    q.record("f1", {"reason": "stagnation", "locus": "domain"})
    q.record("f2", {"reason": "max_attempts"})
    assert {f["reason"] for f in q.pending()} == {"stagnation", "max_attempts"}
    assert q.drain("f1") is True
    assert [f["reason"] for f in q.pending()] == ["max_attempts"]
