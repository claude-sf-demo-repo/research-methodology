"""Append-only SQLite (WAL) event log behind an interface (§19.2/§19.4)."""
from __future__ import annotations

import json
import os
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from research_methodology.storage.encryption import Encryptor, IdentityEncryptor

TOMBSTONE_DATA_CLASS = "tombstone"


@dataclass(frozen=True)
class EventRecord:
    event_id: str
    stream: str
    schema_version: int
    payload: dict
    data_class: str = "unclassified"


class EventLog(ABC):
    @abstractmethod
    def append(self, record: EventRecord) -> bool:
        """Append. True if newly inserted, False if (stream, event_id) already present."""

    @abstractmethod
    def read(self, stream: str) -> list[EventRecord]:
        """All non-tombstoned records for a stream, in insertion order."""

    @abstractmethod
    def close(self) -> None: ...


_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    seq            INTEGER PRIMARY KEY AUTOINCREMENT,
    stream         TEXT NOT NULL,
    event_id       TEXT NOT NULL,
    schema_version INTEGER NOT NULL,
    data_class     TEXT NOT NULL,
    payload        BLOB NOT NULL,
    UNIQUE(stream, event_id)
);
CREATE INDEX IF NOT EXISTS idx_events_stream ON events(stream, seq);
"""


class SQLiteEventLog(EventLog):
    def __init__(self, path: Path, encryptor: Encryptor | None = None) -> None:
        self._path = Path(path)
        self._encryptor = encryptor or IdentityEncryptor()
        new_file = not self._path.exists()
        self._conn = sqlite3.connect(str(self._path))
        self._conn.execute("PRAGMA journal_mode=WAL")     # readers never block the one writer
        self._conn.execute("PRAGMA busy_timeout=5000")    # absorb rare concurrent-writer collisions
        self._conn.executescript(_SCHEMA)
        self._conn.commit()
        if new_file:
            os.chmod(self._path, 0o600)

    def append(self, record: EventRecord) -> bool:
        blob = self._encryptor.encrypt(
            json.dumps(record.payload, sort_keys=True).encode("utf-8"))
        cur = self._conn.execute(
            "INSERT OR IGNORE INTO events "
            "(stream, event_id, schema_version, data_class, payload) VALUES (?, ?, ?, ?, ?)",
            (record.stream, record.event_id, record.schema_version, record.data_class, blob),
        )
        self._conn.commit()
        return cur.rowcount == 1

    def read(self, stream: str) -> list[EventRecord]:
        rows = self._conn.execute(
            "SELECT stream, event_id, schema_version, data_class, payload "
            "FROM events WHERE stream = ? AND data_class != ? ORDER BY seq",
            (stream, TOMBSTONE_DATA_CLASS),
        ).fetchall()
        out: list[EventRecord] = []
        for stream_, event_id, sv, data_class, blob in rows:
            payload = json.loads(self._encryptor.decrypt(blob).decode("utf-8"))
            out.append(EventRecord(event_id, stream_, sv, payload, data_class))
        return out

    def close(self) -> None:
        self._conn.close()

    def purge(self, stream: str, event_id: str) -> bool:
        """Tombstone a record (§9.9 erasure): empty the payload, flag it out of reads,
        keep the event_id claimed so it can never be re-added."""
        cur = self._conn.execute(
            "UPDATE events SET payload = ?, data_class = ? "
            "WHERE stream = ? AND event_id = ? AND data_class != ?",
            (self._encryptor.encrypt(b"{}"), TOMBSTONE_DATA_CLASS,
             stream, event_id, TOMBSTONE_DATA_CLASS),
        )
        self._conn.commit()
        return cur.rowcount == 1

    def purge_data_class(self, data_class: str) -> int:
        """Hard-DELETE every record of a data_class (retention aging §9.9)."""
        cur = self._conn.execute(
            "DELETE FROM events WHERE data_class = ?", (data_class,))
        self._conn.commit()
        return cur.rowcount
