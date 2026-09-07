"""Fold snapshot + compaction trigger (§19.3)."""
from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from research_methodology.storage.encryption import Encryptor, IdentityEncryptor

_SCHEMA = """
CREATE TABLE IF NOT EXISTS snapshots (
    namespace TEXT NOT NULL,
    key       TEXT NOT NULL,
    last_seq  INTEGER NOT NULL,
    state     BLOB NOT NULL,
    PRIMARY KEY (namespace, key)
);
"""


@dataclass(frozen=True)
class Snapshot:
    last_seq: int
    state: dict


class SnapshotStore:
    def __init__(self, path: Path, encryptor: Encryptor | None = None) -> None:
        self._path = Path(path)
        self._encryptor = encryptor or IdentityEncryptor()
        new_file = not self._path.exists()
        self._conn = sqlite3.connect(str(self._path))
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(_SCHEMA)
        self._conn.commit()
        if new_file:
            os.chmod(self._path, 0o600)

    def save(self, namespace: str, key: str, last_seq: int, state: dict) -> None:
        blob = self._encryptor.encrypt(json.dumps(state, sort_keys=True).encode("utf-8"))
        self._conn.execute(
            "INSERT OR REPLACE INTO snapshots (namespace, key, last_seq, state) "
            "VALUES (?, ?, ?, ?)",
            (namespace, key, last_seq, blob),
        )
        self._conn.commit()

    def load(self, namespace: str, key: str) -> Snapshot | None:
        row = self._conn.execute(
            "SELECT last_seq, state FROM snapshots WHERE namespace = ? AND key = ?",
            (namespace, key),
        ).fetchone()
        if row is None:
            return None
        last_seq, blob = row
        state = json.loads(self._encryptor.decrypt(blob).decode("utf-8"))
        return Snapshot(last_seq, state)

    @staticmethod
    def needs_compaction(event_count: int, threshold: int) -> bool:
        return event_count >= threshold

    def close(self) -> None:
        self._conn.close()
