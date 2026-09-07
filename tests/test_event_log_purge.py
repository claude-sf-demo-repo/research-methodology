from research_methodology.storage.event_log import EventRecord, SQLiteEventLog


def _rec(event_id, stream="s", data_class="raw_content"):
    return EventRecord(event_id, stream, 2, {"k": event_id}, data_class)


def test_purge_tombstones_a_record(tmp_path):
    log = SQLiteEventLog(tmp_path / "events.db")
    log.append(_rec("e1"))
    log.append(_rec("e2"))
    assert log.purge("s", "e1") is True
    assert [r.event_id for r in log.read("s")] == ["e2"]
    log.close()


def test_purged_id_cannot_be_resurrected(tmp_path):
    log = SQLiteEventLog(tmp_path / "events.db")
    log.append(_rec("e1"))
    log.purge("s", "e1")
    assert log.append(_rec("e1")) is False        # id still claimed
    assert log.read("s") == []
    log.close()


def test_purge_missing_record_returns_false(tmp_path):
    log = SQLiteEventLog(tmp_path / "events.db")
    assert log.purge("s", "nope") is False
    log.close()


def test_purge_data_class_bulk_deletes(tmp_path):
    log = SQLiteEventLog(tmp_path / "events.db")
    log.append(_rec("e1", data_class="ephemeral_value"))
    log.append(_rec("e2", data_class="ephemeral_value"))
    log.append(_rec("e3", data_class="raw_content"))
    assert log.purge_data_class("ephemeral_value") == 2
    assert [r.event_id for r in log.read("s")] == ["e3"]
    log.close()
