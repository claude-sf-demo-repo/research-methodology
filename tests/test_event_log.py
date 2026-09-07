import os
import sqlite3

from research_methodology.storage.event_log import EventLog, EventRecord, SQLiteEventLog


class _Rot:
    """Reversible non-identity cipher to prove payloads are encrypted at rest."""
    def encrypt(self, b: bytes) -> bytes:
        return bytes((x + 1) % 256 for x in b)
    def decrypt(self, b: bytes) -> bytes:
        return bytes((x - 1) % 256 for x in b)


def _rec(event_id="e1", stream="s", payload=None):
    return EventRecord(event_id, stream, 2, payload or {"k": "v"})


def test_append_then_read_round_trips(tmp_path):
    log = SQLiteEventLog(tmp_path / "events.db")
    assert log.append(_rec(payload={"k": "hello"})) is True
    got = log.read("s")
    assert len(got) == 1
    assert got[0].payload == {"k": "hello"}
    assert got[0].event_id == "e1" and got[0].schema_version == 2
    log.close()


def test_duplicate_event_id_is_idempotent(tmp_path):
    log = SQLiteEventLog(tmp_path / "events.db")
    assert log.append(_rec()) is True
    assert log.append(_rec()) is False   # same (stream, event_id)
    assert len(log.read("s")) == 1
    log.close()


def test_streams_are_isolated_and_ordered(tmp_path):
    log = SQLiteEventLog(tmp_path / "events.db")
    log.append(_rec("a", "s1"))
    log.append(_rec("b", "s1"))
    log.append(_rec("c", "s2"))
    assert [r.event_id for r in log.read("s1")] == ["a", "b"]
    assert [r.event_id for r in log.read("s2")] == ["c"]
    log.close()


def test_new_db_file_is_0600(tmp_path):
    path = tmp_path / "events.db"
    SQLiteEventLog(path).close()
    assert oct(os.stat(path).st_mode & 0o777) == "0o600"


def test_payload_is_encrypted_at_rest(tmp_path):
    path = tmp_path / "events.db"
    log = SQLiteEventLog(path, encryptor=_Rot())
    log.append(_rec(payload={"secret": "MARKER_TOKEN"}))
    log.close()
    raw = sqlite3.connect(str(path)).execute("SELECT payload FROM events").fetchone()[0]
    assert b"MARKER_TOKEN" not in raw            # not stored in clear
    # and it decrypts back through a fresh handle
    log2 = SQLiteEventLog(path, encryptor=_Rot())
    assert log2.read("s")[0].payload == {"secret": "MARKER_TOKEN"}
    log2.close()


def test_sqlite_event_log_is_an_event_log(tmp_path):
    assert isinstance(SQLiteEventLog(tmp_path / "events.db"), EventLog)
