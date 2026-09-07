# Research Methodology Harness — Implementation Plan 2 of 5: Layer 1 (Storage)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the storage layer — configuration, an encrypted append-only SQLite event log, the credibility store, flat maps + seeds, RSS/write-failure queues, an interface-backed temporal ledger with an in-memory fake, the trusted-source registry, and preference memory — so every store is reachable behind a stable interface and Layers 2–4 can be built and tested against fakes.

**Architecture:** A new `research_methodology/storage/` subpackage. Every store is an **interface + adapter**. Two adapter families: (1) *real, tested-in-CI now* — the stdlib `sqlite3` (WAL) `EventLog` and everything built over it; (2) *interface + fully-tested fake now, real backend deferred* — the graph `Ledger` (real Neo4j+Graphiti deferred) and the `Encryptor` (real Fernet/SQLCipher deferred). All logic (folds, bi-temporal reconstruction, registry, preferences, tombstone-purge) is real and tested against the fake/identity implementations. No third-party runtime dependency is introduced; Layer 1 CI stays hermetic and stdlib-only, preserving the spec's "each layer testable with fakes for the layer above" thesis (spec Part III, lines 402/441).

**Tech Stack:** Python 3.11+, `pytest`, standard library only (`sqlite3`, `json`, `os`, `pathlib`, `dataclasses`, `enum`, `abc`, `typing`). No third-party runtime dependencies in this layer. (`neo4j` / `graphiti-core` and a real crypto library enter only when the deferred adapters are wired, a later task/layer.)

**Spec:** `docs/superpowers/specs/2026-09-02-research-methodology-design-v2.md` (in this repo). Part II is the spec; Part III's **Layer 1** bullets are the scope of this plan. Executors read the spec alongside this plan — every task cites the spec section it implements.

## Global Constraints

Every task's requirements implicitly include this section. Values are copied verbatim from the spec unless noted.

- **Python 3.11+**; Layer 1 uses the standard library only — no third-party runtime imports in any `research_methodology/` module in this plan. `sqlite3` is stdlib and is the only new I/O primitive.
- **Purity boundary (shifted from Layer 0):** disk I/O via `sqlite3` and `pathlib` is now allowed. Still **no network, no LLM calls, and no real clock reads** — time enters as an injected `now_days: float` (folds) or as caller-supplied ISO-8601 strings (`valid_at`/`invalid_at`/`timestamp`). No module calls `datetime.now()`.
- **Portability & configuration (load-bearing):** all storage locations come from a single `StorageConfig` rooted at one data directory (`RM_DATA_DIR`); **no module hard-codes a path**. Backends are interfaces (`EventLog`, `Ledger`, `Encryptor`, and a future `VectorStore`), so SQLite→Postgres, in-memory→Neo4j, and identity→real-crypto are config/wiring swaps, not rewrites. This is what makes the agent lift-and-shift / containerizable. Docker/compose itself is deferred to Layer 4 ops (§19.5).
- **Deferred behind interfaces + fakes (this layer stays hermetic):** the real Neo4j-backed Graphiti `Ledger` (needs a running DB + the Layer-3 `graph_extraction` model role, §9.2/§21) and real at-rest encryption (Fernet/SQLCipher, §9.9). Layer 1 ships the `InMemoryLedger` and `IdentityEncryptor`, both fully tested, plus a `Neo4jGraphitiLedger` **skeleton** that reserves the seam.
- **Every persisted record carries `schema_version` and a stable `event_id`/`episode_id`** (§9.2, §9.4, §19.2). `SCHEMA_VERSION = 2` (imported from `research_methodology`).
- **Append-only by discipline** (§19.2): inserts only. The single exception is the §9.9 tombstone-and-purge erasure path. Idempotency is by id via `INSERT OR IGNORE` (§19.4) — a retried append never double-counts.
- **At-rest posture** (§9.9, §6b): SQLite files are created `0600`, the data dir `0700`; every payload is written through the `Encryptor` (identity in this layer); no secret-shaped string is ever placed in a payload.
- **Reuse Layer 0, do not re-implement it.** `credibility.fold` / `CredEvent` / `CredState` (Task 0.12), `volatility.policy` / `ResolvedPolicy` (Task 0.11, **as merged** — see note below), and `episode.validate_episode` (Task 0.6) are consumed as-is.
- **Naming:** the persona is `research-analyst`; the core library package is `research_methodology`; the storage subpackage is `research_methodology.storage`.
- **Commit after every task** with a Conventional Commit message; each task ends green (`python -m pytest -v`). One branch + one PR per task: `task/1.<n>-<slug>`.

> **As-merged Layer 0 caveat (read before Task 1.6/1.11).** PR #24 fixed a bug in the plan-01 text for `volatility.policy()`: `min_evidence_clusters` is **left unscaled** when the class's `half_life_days`/`staleness_days` are infinite (`None`) — so `policy(DURABLE, LOW).min_evidence_clusters == 1`, and `durable` has `min_explicit == 0` (a single source may suffice). Tasks that reason about which sources reach high confidence must use this merged behavior, not the plan-01 prose.

---

## Plan Map — Layer 1 (this file)

This file fully expands **Layer 1**. It follows Plan 1 (`...-01-foundation.md`, merged) and precedes Plan 3 (`...-03-tools.md`).

- 1.1 `StorageConfig` — single data dir + config-driven paths (portability foundation)
- 1.2 `Encryptor` protocol + `IdentityEncryptor` (dev/test; real crypto deferred, §9.9/§6b)
- 1.3 `EventLog` interface + `SQLiteEventLog` — WAL, atomic append, `UNIQUE(event_id)`, `0600`, encrypted values (§19.2/§19.4)
- 1.4 Tombstone-and-purge hard-delete path (§9.9)
- 1.5 Fold snapshot/compaction store (§19.3)
- 1.6 Credibility store over `EventLog` — read-time fold via Task 0.12 (§9.4)
- 1.7 Flat maps + AU/NZ/US seeds (§9.5–9.7, §8 cold-start)
- 1.8 RSS log + `write_failures` queue (§11, §9.3, §19.5)
- 1.9 `Ledger` interface + `InMemoryLedger` fake — pre-structured payload write path (§9.2)
- 1.10 Bi-temporal query + point-in-time belief reconstruction (§9.9)
- 1.11 Trusted-source registry view (§5.3)
- 1.12 Preference memory — `valid_at`/`recheck_after`, bias-guard invariant (§9.8)
- 1.13 `Neo4jGraphitiLedger` adapter skeleton — reserves the seam, deferred integration (§19.2/§21)

---

## File Structure

- `research_methodology/storage/__init__.py` — subpackage marker (Task 1.1).
- `research_methodology/storage/config.py` — `StorageConfig` (1.1).
- `research_methodology/storage/encryption.py` — `Encryptor`, `IdentityEncryptor` (1.2).
- `research_methodology/storage/event_log.py` — `EventRecord`, `EventLog`, `SQLiteEventLog`, tombstone-purge (1.3, 1.4).
- `research_methodology/storage/snapshot.py` — `Snapshot`, `SnapshotStore` (1.5).
- `research_methodology/storage/credibility_store.py` — `CredibilityStore` (1.6).
- `research_methodology/storage/maps.py` — `FlatMap` (1.7).
- `research_methodology/storage/seeds.py` — seed data + `load_seeds` (1.7).
- `research_methodology/storage/queues.py` — `RSSLog`, `WriteFailureQueue` (1.8).
- `research_methodology/storage/ledger.py` — `Ledger`, `InMemoryLedger`, `LedgerWriteError` (1.9, 1.10).
- `research_methodology/storage/registry.py` — `TrustedSource`, `TrustedSourceRegistry` (1.11).
- `research_methodology/storage/preferences.py` — `PreferenceEdge`, `PreferenceMemory` (1.12).
- `research_methodology/storage/neo4j_ledger.py` — `Neo4jGraphitiLedger` skeleton (1.13).
- Tests: `tests/test_storage_config.py`, `test_encryption.py`, `test_event_log.py`, `test_event_log_purge.py`, `test_snapshot.py`, `test_credibility_store.py`, `test_flat_maps.py`, `test_queues.py`, `test_ledger.py`, `test_ledger_bitemporal.py`, `test_registry.py`, `test_preferences.py`, `test_neo4j_ledger_skeleton.py`.

---

# Layer 1 tasks

### Task 1.1: StorageConfig — single data dir + config-driven paths

Establishes the portability foundation: every later store gets its location from this object. Locations root at one `RM_DATA_DIR` so lift-and-shift = move/mount one directory (§19.2, portability constraint).

**Files:**
- Create: `research_methodology/storage/__init__.py`
- Create: `research_methodology/storage/config.py`
- Test: `tests/test_storage_config.py`

**Interfaces:**
- Consumes: nothing (stdlib `os`, `pathlib`).
- Produces:
  - `@dataclass(frozen=True) StorageConfig(data_dir: Path, event_log_filename: str = "events.db", snapshot_filename: str = "snapshots.db", neo4j_uri: str | None = None, neo4j_user: str | None = None)`.
  - `StorageConfig.from_env(env: dict[str, str] | None = None) -> StorageConfig` (reads `RM_DATA_DIR`, `RM_NEO4J_URI`, `RM_NEO4J_USER`; `env` injectable for tests).
  - `StorageConfig.path_for(filename: str) -> Path`, `.event_log_path -> Path`, `.snapshot_path -> Path`.
  - `StorageConfig.ensure_data_dir() -> Path` (creates the dir `0700`, idempotent).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_storage_config.py
import os
from pathlib import Path

from research_methodology.storage.config import StorageConfig


def test_from_env_reads_injected_data_dir():
    cfg = StorageConfig.from_env({"RM_DATA_DIR": "/tmp/rm-data"})
    assert cfg.data_dir == Path("/tmp/rm-data")


def test_from_env_default_expands_user_home():
    cfg = StorageConfig.from_env({})
    assert cfg.data_dir.is_absolute()
    assert "~" not in str(cfg.data_dir)


def test_paths_root_at_the_single_data_dir():
    cfg = StorageConfig(data_dir=Path("/tmp/rm-data"))
    assert cfg.event_log_path == Path("/tmp/rm-data/events.db")
    assert cfg.snapshot_path == Path("/tmp/rm-data/snapshots.db")
    assert cfg.path_for("x.db") == Path("/tmp/rm-data/x.db")


def test_ensure_data_dir_creates_it_0700(tmp_path):
    cfg = StorageConfig(data_dir=tmp_path / "nested" / "data")
    made = cfg.ensure_data_dir()
    assert made.is_dir()
    assert oct(os.stat(made).st_mode & 0o777) == "0o700"
    cfg.ensure_data_dir()  # idempotent, no raise
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_storage_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'research_methodology.storage'`.

- [ ] **Step 3: Write minimal implementation**

```python
# research_methodology/storage/__init__.py
"""Research Methodology Harness — Layer 1 storage adapters (interfaces + fakes + SQLite)."""
```

```python
# research_methodology/storage/config.py
"""Storage configuration: one data directory, config-driven paths (portability, §19.2)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

_ENV_DATA_DIR = "RM_DATA_DIR"
_DEFAULT_DATA_DIR = "~/.research_methodology/data"


@dataclass(frozen=True)
class StorageConfig:
    data_dir: Path
    event_log_filename: str = "events.db"
    snapshot_filename: str = "snapshots.db"
    neo4j_uri: str | None = None
    neo4j_user: str | None = None

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "StorageConfig":
        env = os.environ if env is None else env
        data_dir = Path(env.get(_ENV_DATA_DIR, _DEFAULT_DATA_DIR)).expanduser()
        return cls(
            data_dir=data_dir,
            neo4j_uri=env.get("RM_NEO4J_URI"),
            neo4j_user=env.get("RM_NEO4J_USER"),
        )

    def path_for(self, filename: str) -> Path:
        return self.data_dir / filename

    @property
    def event_log_path(self) -> Path:
        return self.path_for(self.event_log_filename)

    @property
    def snapshot_path(self) -> Path:
        return self.path_for(self.snapshot_filename)

    def ensure_data_dir(self) -> Path:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(self.data_dir, 0o700)  # single-user, portable
        return self.data_dir
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_storage_config.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add research_methodology/storage/__init__.py research_methodology/storage/config.py tests/test_storage_config.py
git commit -m "feat: StorageConfig — single data dir + config-driven paths (§19.2)"
```

---

### Task 1.2: Encryptor protocol + IdentityEncryptor (§9.9, §6b)

Defines the at-rest encryption seam. Layer 1 ships the passthrough `IdentityEncryptor`; the real Fernet/SQLCipher implementation is a deferred later task. Everything that writes to disk routes bytes through this protocol so swapping in real crypto never touches store code.

**Files:**
- Create: `research_methodology/storage/encryption.py`
- Test: `tests/test_encryption.py`

**Interfaces:**
- Consumes: nothing (stdlib `typing`).
- Produces:
  - `@runtime_checkable class Encryptor(Protocol)` with `encrypt(self, plaintext: bytes) -> bytes` and `decrypt(self, ciphertext: bytes) -> bytes`.
  - `class IdentityEncryptor` implementing `Encryptor` as passthrough.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_encryption.py
from research_methodology.storage.encryption import Encryptor, IdentityEncryptor


def test_identity_round_trips():
    enc = IdentityEncryptor()
    assert enc.decrypt(enc.encrypt(b"hello")) == b"hello"


def test_identity_is_passthrough():
    enc = IdentityEncryptor()
    assert enc.encrypt(b"payload") == b"payload"


def test_identity_satisfies_the_protocol():
    assert isinstance(IdentityEncryptor(), Encryptor)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_encryption.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'research_methodology.storage.encryption'`.

- [ ] **Step 3: Write minimal implementation**

```python
# research_methodology/storage/encryption.py
"""At-rest encryption seam (§9.9/§6b).

Layer 1 provides the passthrough IdentityEncryptor. A real Fernet/SQLCipher
Encryptor is a deferred later task; because callers depend only on this
protocol, swapping it in never touches store code.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Encryptor(Protocol):
    def encrypt(self, plaintext: bytes) -> bytes: ...
    def decrypt(self, ciphertext: bytes) -> bytes: ...


class IdentityEncryptor:
    """Dev/test passthrough. NOT for production data at rest."""

    def encrypt(self, plaintext: bytes) -> bytes:
        return plaintext

    def decrypt(self, ciphertext: bytes) -> bytes:
        return ciphertext
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_encryption.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add research_methodology/storage/encryption.py tests/test_encryption.py
git commit -m "feat: Encryptor protocol + IdentityEncryptor (§9.9)"
```

---

### Task 1.3: EventLog interface + SQLiteEventLog (§19.2/§19.4)

The append-only substrate under the credibility store, flat maps, RSS log, and write-failures. SQLite in WAL mode gives ACID appends (no torn writes), `UNIQUE(stream, event_id)` idempotency, indexed reads, and a single `0600` file. Payloads are written through the `Encryptor`.

**Files:**
- Create: `research_methodology/storage/event_log.py`
- Test: `tests/test_event_log.py`

**Interfaces:**
- Consumes: `storage.encryption.Encryptor`, `storage.encryption.IdentityEncryptor`.
- Produces:
  - `@dataclass(frozen=True) EventRecord(event_id: str, stream: str, schema_version: int, payload: dict, data_class: str = "unclassified")`.
  - `class EventLog(ABC)` with `append(record: EventRecord) -> bool` (True if newly inserted, False if `event_id` already present in that stream — idempotent), `read(stream: str) -> list[EventRecord]` (insertion order), `close() -> None`.
  - `class SQLiteEventLog(EventLog)` with `__init__(self, path: Path, encryptor: Encryptor | None = None)`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_event_log.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_event_log.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'research_methodology.storage.event_log'`.

- [ ] **Step 3: Write minimal implementation**

```python
# research_methodology/storage/event_log.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_event_log.py -v`
Expected: PASS (6 tests).

- [ ] **Step 5: Commit**

```bash
git add research_methodology/storage/event_log.py tests/test_event_log.py
git commit -m "feat: EventLog interface + SQLite(WAL) adapter (§19.2)"
```

---

### Task 1.4: Tombstone-and-purge hard-delete path (§9.9)

The erasure path §9.9 requires day-one, distinct from `valid_at`/`invalid_at`. A **tombstone** replaces a record's payload with an empty marker and flags its `data_class` so it disappears from `read()` while its `event_id` stays claimed (a re-append of the same id can never resurrect the data). A **bulk purge by data_class** supports retention aging.

**Files:**
- Modify: `research_methodology/storage/event_log.py` (add `purge` and `purge_data_class` to `SQLiteEventLog`)
- Test: `tests/test_event_log_purge.py`

**Interfaces:**
- Consumes: the Task 1.3 `SQLiteEventLog`, `TOMBSTONE_DATA_CLASS`.
- Produces:
  - `SQLiteEventLog.purge(self, stream: str, event_id: str) -> bool` (tombstones the record; True if a live record matched).
  - `SQLiteEventLog.purge_data_class(self, data_class: str) -> int` (hard-DELETEs all matching rows; returns count).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_event_log_purge.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_event_log_purge.py -v`
Expected: FAIL — `AttributeError: 'SQLiteEventLog' object has no attribute 'purge'`.

- [ ] **Step 3: Write minimal implementation** (append the two methods to `SQLiteEventLog`)

```python
# --- append inside class SQLiteEventLog in research_methodology/storage/event_log.py ---
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_event_log_purge.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add research_methodology/storage/event_log.py tests/test_event_log_purge.py
git commit -m "feat: tombstone-and-purge hard-delete path (§9.9)"
```

---

### Task 1.5: Fold snapshot/compaction store (§19.3)

Folds are pure over events; a snapshot (folded state + last-folded `seq`) lets a read do `snapshot + tail` instead of a full scan. This task ships the snapshot store and the compaction trigger predicate; wiring it into read paths is a later optimization.

**Files:**
- Create: `research_methodology/storage/snapshot.py`
- Test: `tests/test_snapshot.py`

**Interfaces:**
- Consumes: `storage.encryption.Encryptor`, `storage.encryption.IdentityEncryptor`.
- Produces:
  - `@dataclass(frozen=True) Snapshot(last_seq: int, state: dict)`.
  - `class SnapshotStore` with `__init__(self, path: Path, encryptor: Encryptor | None = None)`, `save(namespace: str, key: str, last_seq: int, state: dict) -> None` (last-writer-wins), `load(namespace: str, key: str) -> Snapshot | None`, and `@staticmethod needs_compaction(event_count: int, threshold: int) -> bool`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_snapshot.py
from research_methodology.storage.snapshot import Snapshot, SnapshotStore


def test_save_then_load_round_trips(tmp_path):
    s = SnapshotStore(tmp_path / "snap.db")
    s.save("credibility", "example.com|plumbing", last_seq=42, state={"score": 1.5})
    assert s.load("credibility", "example.com|plumbing") == Snapshot(42, {"score": 1.5})


def test_load_missing_returns_none(tmp_path):
    assert SnapshotStore(tmp_path / "snap.db").load("ns", "missing") is None


def test_save_is_last_writer_wins(tmp_path):
    s = SnapshotStore(tmp_path / "snap.db")
    s.save("ns", "k", 1, {"score": 1.0})
    s.save("ns", "k", 9, {"score": 9.0})
    assert s.load("ns", "k") == Snapshot(9, {"score": 9.0})


def test_needs_compaction_at_threshold():
    assert SnapshotStore.needs_compaction(99, 100) is False
    assert SnapshotStore.needs_compaction(100, 100) is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_snapshot.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'research_methodology.storage.snapshot'`.

- [ ] **Step 3: Write minimal implementation**

```python
# research_methodology/storage/snapshot.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_snapshot.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add research_methodology/storage/snapshot.py tests/test_snapshot.py
git commit -m "feat: fold snapshot/compaction store (§19.3)"
```

---

### Task 1.6: Credibility store over EventLog (§9.4)

Persists credibility events on the `EventLog` and computes current state by reconstructing `CredEvent`s and calling the merged Layer-0 `fold()` at read time. Also exposes the distinct `(domain, topic, volatility_class)` keys the trusted-source registry (Task 1.11) iterates.

**Files:**
- Create: `research_methodology/storage/credibility_store.py`
- Test: `tests/test_credibility_store.py`

**Interfaces:**
- Consumes: `storage.event_log.EventLog`/`EventRecord`; `research_methodology.credibility.CredEvent`/`CredState`/`fold` (Task 0.12); `research_methodology.constants.VolatilityClass`/`AuthorityClass`/`SCHEMA_VERSION`.
- Produces:
  - `class CredibilityStore` with `__init__(self, event_log: EventLog)`.
  - `record(self, event: dict) -> bool` — appends a credibility-event payload (must carry `event_id`, `domain`, `topic`, `kind`, `ts_days`, `volatility_class`, `authority_class`; feedback also `positive`/`explicit`/`cluster_id`). Idempotent by `event_id`.
  - `state(self, domain: str, topic: str, now_days: float) -> CredState`.
  - `keys(self) -> list[tuple[str, str, str]]` — distinct `(domain, topic, volatility_class)`, volatility taken from the latest event per `(domain, topic)`.

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_credibility_store.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'research_methodology.storage.credibility_store'`.

- [ ] **Step 3: Write minimal implementation**

```python
# research_methodology/storage/credibility_store.py
"""Credibility store: append events, fold to current state at read time (§9.4)."""
from __future__ import annotations

from research_methodology import SCHEMA_VERSION
from research_methodology.constants import AuthorityClass, VolatilityClass
from research_methodology.credibility import CredEvent, CredState, fold
from research_methodology.storage.event_log import EventLog, EventRecord

_STREAM = "credibility"


def _to_cred_event(p: dict) -> CredEvent:
    return CredEvent(
        event_id=p["event_id"],
        ts_days=p["ts_days"],
        kind=p["kind"],
        positive=p.get("positive", True),
        explicit=p.get("explicit", True),
        volatility_class=VolatilityClass(p["volatility_class"]),
        authority_class=AuthorityClass(p["authority_class"]),
        cluster_id=p.get("cluster_id", ""),
    )


class CredibilityStore:
    def __init__(self, event_log: EventLog) -> None:
        self._log = event_log

    def record(self, event: dict) -> bool:
        return self._log.append(EventRecord(
            event_id=event["event_id"],
            stream=_STREAM,
            schema_version=event.get("schema_version", SCHEMA_VERSION),
            payload=event,
            data_class="credibility_event",
        ))

    def state(self, domain: str, topic: str, now_days: float) -> CredState:
        events = [
            _to_cred_event(r.payload)
            for r in self._log.read(_STREAM)
            if r.payload.get("domain") == domain and r.payload.get("topic") == topic
        ]
        return fold(events, now_days)

    def keys(self) -> list[tuple[str, str, str]]:
        latest: dict[tuple[str, str], str] = {}
        for r in self._log.read(_STREAM):  # insertion order -> later events overwrite
            p = r.payload
            latest[(p["domain"], p["topic"])] = p["volatility_class"]
        return [(d, t, vc) for (d, t), vc in latest.items()]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_credibility_store.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add research_methodology/storage/credibility_store.py tests/test_credibility_store.py
git commit -m "feat: credibility store over EventLog with read-time fold (§9.4)"
```

---

### Task 1.7: Flat maps + AU/NZ/US seeds (§9.5–9.7, §8 cold-start)

A generic `FlatMap` (discovery-and-cache, latest-writer-wins per key over the `EventLog`) backs `community_hub_map`, `domain_authority_profile`, `consumer_protection_registry_map`, and the volatility topic→class seed map. Seeds ship AU/NZ/US so no category starts with <2 entries (§8). Seeding is idempotent (deterministic `event_id`s).

**Files:**
- Create: `research_methodology/storage/maps.py`
- Create: `research_methodology/storage/seeds.py`
- Test: `tests/test_flat_maps.py`

**Interfaces:**
- Consumes: `storage.event_log.EventLog`/`EventRecord`.
- Produces:
  - `class FlatMap` with `__init__(self, event_log: EventLog, stream: str)`, `put(self, key: str, value: dict, event_id: str) -> bool`, `get(self, key: str) -> dict | None` (latest), `all(self) -> dict[str, dict]`.
  - In `seeds.py`: dicts `SEED_COMMUNITY_HUBS`, `SEED_DOMAIN_AUTHORITY`, `SEED_CONSUMER_PROTECTION`, `SEED_VOLATILITY_TOPICS` and `def load_seeds(community: FlatMap, authority: FlatMap, consumer: FlatMap, volatility: FlatMap) -> int` (returns count newly inserted; idempotent).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_flat_maps.py
from research_methodology.storage.event_log import SQLiteEventLog
from research_methodology.storage.maps import FlatMap
from research_methodology.storage import seeds


def _map(tmp_path, stream):
    return FlatMap(SQLiteEventLog(tmp_path / "events.db"), stream)


def test_put_get_latest_writer_wins(tmp_path):
    m = _map(tmp_path, "community_hub_map")
    m.put("plumbing", {"hub": "reddit.com/r/Plumbing"}, "ev1")
    m.put("plumbing", {"hub": "reddit.com/r/plumbers"}, "ev2")
    assert m.get("plumbing") == {"hub": "reddit.com/r/plumbers"}


def test_get_missing_returns_none(tmp_path):
    assert _map(tmp_path, "s").get("absent") is None


def test_seed_volatility_map_classifies_physics_durable(tmp_path):
    log = SQLiteEventLog(tmp_path / "events.db")
    vol = FlatMap(log, "volatility_topic_class")
    seeds.load_seeds(FlatMap(log, "community_hub_map"),
                     FlatMap(log, "domain_authority_profile"),
                     FlatMap(log, "consumer_protection_registry_map"),
                     vol)
    assert vol.get("physics") == {"volatility_class": "durable"}
    assert vol.get("news") == {"volatility_class": "fast"}


def test_seeding_is_idempotent(tmp_path):
    log = SQLiteEventLog(tmp_path / "events.db")
    maps = (FlatMap(log, "community_hub_map"),
            FlatMap(log, "domain_authority_profile"),
            FlatMap(log, "consumer_protection_registry_map"),
            FlatMap(log, "volatility_topic_class"))
    first = seeds.load_seeds(*maps)
    second = seeds.load_seeds(*maps)
    assert first > 0 and second == 0


def test_consumer_protection_seeds_cover_au_nz_us(tmp_path):
    assert {"AU", "NZ", "US"} <= set(seeds.SEED_CONSUMER_PROTECTION)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_flat_maps.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'research_methodology.storage.maps'`.

- [ ] **Step 3: Write minimal implementation**

```python
# research_methodology/storage/maps.py
"""Generic flat map over the EventLog: discovery-and-cache, latest-writer-wins (§9.5-9.7)."""
from __future__ import annotations

from research_methodology import SCHEMA_VERSION
from research_methodology.storage.event_log import EventLog, EventRecord


class FlatMap:
    def __init__(self, event_log: EventLog, stream: str) -> None:
        self._log = event_log
        self._stream = stream

    def put(self, key: str, value: dict, event_id: str) -> bool:
        return self._log.append(EventRecord(
            event_id=event_id,
            stream=self._stream,
            schema_version=SCHEMA_VERSION,
            payload={"key": key, "value": value},
            data_class="flat_map",
        ))

    def get(self, key: str) -> dict | None:
        result: dict | None = None
        for r in self._log.read(self._stream):  # insertion order -> latest wins
            if r.payload.get("key") == key:
                result = r.payload.get("value")
        return result

    def all(self) -> dict[str, dict]:
        out: dict[str, dict] = {}
        for r in self._log.read(self._stream):
            out[r.payload["key"]] = r.payload["value"]
        return out
```

```python
# research_methodology/storage/seeds.py
"""Cold-start seed data (AU/NZ/US) so no category starts with <2 entries (§8)."""
from __future__ import annotations

from research_methodology.storage.maps import FlatMap

SEED_COMMUNITY_HUBS: dict[str, dict] = {
    "plumbing": {"hub": "reddit.com/r/Plumbing"},
    "python": {"hub": "stackoverflow.com"},
    "caravanning-nz": {"hub": "nzmca.org.nz"},
    "home-renovation-au": {"hub": "whirlpool.net.au/wiki/Renovating"},
}

SEED_DOMAIN_AUTHORITY: dict[str, dict] = {
    "mayoclinic.org": {"authority_class": "canonical", "primary_source_definition": "clinical-consensus"},
    "standards.org.au": {"authority_class": "canonical", "primary_source_definition": "standard"},
    "legislation.govt.nz": {"authority_class": "canonical", "primary_source_definition": "statute"},
    "law.cornell.edu": {"authority_class": "high", "primary_source_definition": "statute"},
}

SEED_CONSUMER_PROTECTION: dict[str, dict] = {
    "AU": {"registry": "accc.gov.au"},
    "NZ": {"registry": "comcom.govt.nz"},
    "US": {"registry": "ftc.gov"},
}

SEED_VOLATILITY_TOPICS: dict[str, dict] = {
    "physics": {"volatility_class": "durable"},
    "mathematics": {"volatility_class": "durable"},
    "iso-standards": {"volatility_class": "durable"},
    "medical-consensus": {"volatility_class": "slow"},
    "regulatory-code": {"volatility_class": "slow"},
    "tech-best-practice": {"volatility_class": "moderate"},
    "product-category": {"volatility_class": "moderate"},
    "news": {"volatility_class": "fast"},
    "prices": {"volatility_class": "fast"},
    "weather": {"volatility_class": "ephemeral"},
}


def _seed_one(m: FlatMap, prefix: str, data: dict[str, dict]) -> int:
    inserted = 0
    for key, value in data.items():
        if m.put(key, value, event_id=f"seed:{prefix}:{key}"):
            inserted += 1
    return inserted


def load_seeds(community: FlatMap, authority: FlatMap,
               consumer: FlatMap, volatility: FlatMap) -> int:
    return (
        _seed_one(community, "community", SEED_COMMUNITY_HUBS)
        + _seed_one(authority, "authority", SEED_DOMAIN_AUTHORITY)
        + _seed_one(consumer, "consumer", SEED_CONSUMER_PROTECTION)
        + _seed_one(volatility, "volatility", SEED_VOLATILITY_TOPICS)
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_flat_maps.py -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add research_methodology/storage/maps.py research_methodology/storage/seeds.py tests/test_flat_maps.py
git commit -m "feat: flat maps + AU/NZ/US cold-start seeds (§9.5-9.7, §8)"
```

---

### Task 1.8: RSS log + write_failures queue (§11, §9.3, §19.5)

Two thin append-only logs over the `EventLog`. The RSS log records every polled item (title-only triage logs everything, §11). The write-failures queue captures persistent validation/repair failures (§9.3) and supports the monitored drain policy (§19.5).

**Files:**
- Create: `research_methodology/storage/queues.py`
- Test: `tests/test_queues.py`

**Interfaces:**
- Consumes: `storage.event_log.EventLog`/`EventRecord`.
- Produces:
  - `class RSSLog` with `__init__(self, event_log: EventLog)`, `log_item(self, item_id: str, item: dict) -> bool`, `items(self) -> list[dict]`.
  - `class WriteFailureQueue` with `__init__(self, event_log: EventLog)`, `record(self, failure_id: str, failure: dict) -> bool`, `pending(self) -> list[dict]`, `drain(self, failure_id: str) -> bool`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_queues.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_queues.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'research_methodology.storage.queues'`.

- [ ] **Step 3: Write minimal implementation**

```python
# research_methodology/storage/queues.py
"""RSS log (§11) and write-failures queue (§9.3/§19.5) over the EventLog."""
from __future__ import annotations

from research_methodology import SCHEMA_VERSION
from research_methodology.storage.event_log import EventLog, EventRecord

_RSS_STREAM = "rss_log"
_WF_STREAM = "write_failures"


class RSSLog:
    def __init__(self, event_log: EventLog) -> None:
        self._log = event_log

    def log_item(self, item_id: str, item: dict) -> bool:
        return self._log.append(EventRecord(
            event_id=item_id, stream=_RSS_STREAM,
            schema_version=SCHEMA_VERSION, payload=item, data_class="rss_item"))

    def items(self) -> list[dict]:
        return [r.payload for r in self._log.read(_RSS_STREAM)]


class WriteFailureQueue:
    def __init__(self, event_log: EventLog) -> None:
        self._log = event_log

    def record(self, failure_id: str, failure: dict) -> bool:
        return self._log.append(EventRecord(
            event_id=failure_id, stream=_WF_STREAM,
            schema_version=SCHEMA_VERSION, payload=failure, data_class="write_failure"))

    def pending(self) -> list[dict]:
        return [r.payload for r in self._log.read(_WF_STREAM)]

    def drain(self, failure_id: str) -> bool:
        return self._log.purge(_WF_STREAM, failure_id)
```

> **Note:** `WriteFailureQueue.drain` relies on `SQLiteEventLog.purge` (Task 1.4). Pass a `SQLiteEventLog` (the only `EventLog` in this layer) — a future in-memory `EventLog` fake must also implement `purge` to back this queue.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_queues.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add research_methodology/storage/queues.py tests/test_queues.py
git commit -m "feat: RSS log + write_failures queue (§11, §9.3)"
```

---

### Task 1.9: Ledger interface + InMemoryLedger fake (§9.2)

The graph ledger behind an interface, with a fully-tested in-memory fake. The write path is **pre-structured payloads** validated by the Layer-0 `validate_episode` (Task 0.6) — mirroring the real Graphiti contract (§9.2). The real Neo4j+Graphiti adapter is deferred (Task 1.13).

**Files:**
- Create: `research_methodology/storage/ledger.py`
- Test: `tests/test_ledger.py`

**Interfaces:**
- Consumes: `research_methodology.episode.validate_episode` (Task 0.6).
- Produces:
  - `class LedgerWriteError(Exception)` carrying `.errors`.
  - `class Ledger(ABC)` with `write_episode(self, payload: dict) -> str` (returns `episode_id`; raises `LedgerWriteError` if invalid; idempotent by `episode_id`), `get(self, episode_id: str) -> dict | None`, `episodes(self, *, session_id: str | None = None) -> list[dict]`.
  - `class InMemoryLedger(Ledger)`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_ledger.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_ledger.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'research_methodology.storage.ledger'`.

- [ ] **Step 3: Write minimal implementation**

```python
# research_methodology/storage/ledger.py
"""Temporal ledger behind an interface, with an in-memory fake (§9.2).

Write path = pre-structured payloads validated by validate_episode (mirrors
Graphiti's contract). The real Neo4j+Graphiti adapter is deferred (neo4j_ledger.py).
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from research_methodology.episode import validate_episode
from research_methodology.validation import ValidationError


class LedgerWriteError(Exception):
    def __init__(self, errors: tuple[ValidationError, ...]) -> None:
        self.errors = errors
        super().__init__(f"invalid episode: {[e.locus for e in errors]}")


class Ledger(ABC):
    @abstractmethod
    def write_episode(self, payload: dict) -> str: ...
    @abstractmethod
    def get(self, episode_id: str) -> dict | None: ...
    @abstractmethod
    def episodes(self, *, session_id: str | None = None) -> list[dict]: ...


class InMemoryLedger(Ledger):
    def __init__(self) -> None:
        self._episodes: dict[str, dict] = {}

    def write_episode(self, payload: dict) -> str:
        res = validate_episode(payload)
        if not res.ok:
            raise LedgerWriteError(res.errors)
        episode_id = payload["episode_id"]
        self._episodes.setdefault(episode_id, dict(payload))  # idempotent: keep first
        return episode_id

    def get(self, episode_id: str) -> dict | None:
        found = self._episodes.get(episode_id)
        return dict(found) if found is not None else None

    def episodes(self, *, session_id: str | None = None) -> list[dict]:
        vals = [dict(e) for e in self._episodes.values()]
        if session_id is not None:
            vals = [e for e in vals if e.get("session_id") == session_id]
        return vals
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_ledger.py -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add research_methodology/storage/ledger.py tests/test_ledger.py
git commit -m "feat: Ledger interface + InMemoryLedger fake (§9.2)"
```

---

### Task 1.10: Bi-temporal query + point-in-time belief reconstruction (§9.9)

Adds the bi-temporal query that makes "what did we believe on date X" a first-class operation. Episodes carry `valid_at`/`invalid_at` (ISO-8601 strings, which sort lexicographically). An episode is believed at `as_of` iff `valid_at <= as_of` and (`invalid_at is None` or `as_of < invalid_at`).

**Files:**
- Modify: `research_methodology/storage/ledger.py` (add abstract `beliefs_as_of` to `Ledger`; implement on `InMemoryLedger`)
- Test: `tests/test_ledger_bitemporal.py`

**Interfaces:**
- Consumes: the Task 1.9 `Ledger`/`InMemoryLedger`.
- Produces: `Ledger.beliefs_as_of(self, as_of: str, *, session_id: str | None = None) -> list[dict]`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_ledger_bitemporal.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_ledger_bitemporal.py -v`
Expected: FAIL — `AttributeError: 'InMemoryLedger' object has no attribute 'beliefs_as_of'`.

- [ ] **Step 3: Write minimal implementation**

Add the abstract method to `Ledger`:

```python
# --- add inside class Ledger(ABC) in research_methodology/storage/ledger.py ---
    @abstractmethod
    def beliefs_as_of(self, as_of: str, *, session_id: str | None = None) -> list[dict]:
        """Episodes believed at ISO-8601 `as_of`: valid_at <= as_of < invalid_at (§9.9)."""
```

Implement it on `InMemoryLedger`:

```python
# --- add inside class InMemoryLedger(Ledger) in research_methodology/storage/ledger.py ---
    def beliefs_as_of(self, as_of: str, *, session_id: str | None = None) -> list[dict]:
        out: list[dict] = []
        for e in self.episodes(session_id=session_id):
            valid_at = e.get("valid_at")
            invalid_at = e.get("invalid_at")
            if valid_at is None or valid_at > as_of:
                continue
            if invalid_at is not None and as_of >= invalid_at:
                continue
            out.append(e)
        return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_ledger_bitemporal.py -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add research_methodology/storage/ledger.py tests/test_ledger_bitemporal.py
git commit -m "feat: bi-temporal point-in-time belief reconstruction (§9.9)"
```

---

### Task 1.11: Trusted-source registry view (§5.3)

A view over the credibility store: sources whose `volatility_class ∈ {durable, slow}` that have cleared the class evidence bar (fold `confidence == "high"`, using the merged Layer-0 policy) and sit at or above a trust bar. This is what lets the planner reuse durable knowledge instead of re-researching (§5.3, §6c step 0).

**Files:**
- Create: `research_methodology/storage/registry.py`
- Test: `tests/test_registry.py`

**Interfaces:**
- Consumes: `storage.credibility_store.CredibilityStore` (its `keys()` and `state()`); `research_methodology.constants.VolatilityClass`.
- Produces:
  - `@dataclass(frozen=True) TrustedSource(domain: str, topic: str, volatility_class: str, score: float, confidence: str)`.
  - `class TrustedSourceRegistry` with `__init__(self, credibility_store: CredibilityStore, trust_bar: float = 0.0)` and `query(self, topic: str, now_days: float) -> list[TrustedSource]`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_registry.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_registry.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'research_methodology.storage.registry'`.

- [ ] **Step 3: Write minimal implementation**

```python
# research_methodology/storage/registry.py
"""Trusted-source registry: a view over the credibility store (§5.3)."""
from __future__ import annotations

from dataclasses import dataclass

from research_methodology.constants import VolatilityClass
from research_methodology.storage.credibility_store import CredibilityStore

_DURABLE_CLASSES = {VolatilityClass.DURABLE.value, VolatilityClass.SLOW.value}


@dataclass(frozen=True)
class TrustedSource:
    domain: str
    topic: str
    volatility_class: str
    score: float
    confidence: str


class TrustedSourceRegistry:
    def __init__(self, credibility_store: CredibilityStore, trust_bar: float = 0.0) -> None:
        self._store = credibility_store
        self._trust_bar = trust_bar

    def query(self, topic: str, now_days: float) -> list[TrustedSource]:
        out: list[TrustedSource] = []
        for domain, key_topic, volatility_class in self._store.keys():
            if key_topic != topic or volatility_class not in _DURABLE_CLASSES:
                continue
            st = self._store.state(domain, key_topic, now_days)
            if st.blocked or st.confidence != "high" or st.score < self._trust_bar:
                continue
            out.append(TrustedSource(domain, key_topic, volatility_class, st.score, st.confidence))
        return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_registry.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add research_methodology/storage/registry.py tests/test_registry.py
git commit -m "feat: trusted-source registry view (§5.3)"
```

---

### Task 1.12: Preference memory — valid_at/recheck_after + bias guard (§9.8)

Graph-native preference memory: a `Preference` linked to context tags by edges carrying `valid_at`/`recheck_after`; staleness sets `invalid_at` and flags a re-ask; reinforcement adds a fresh edge. The **bias guard** (§9.8) is a structural invariant: this store exposes *no* API to alter evidential weighting — a test asserts that.

**Files:**
- Create: `research_methodology/storage/preferences.py`
- Test: `tests/test_preferences.py`

**Interfaces:**
- Consumes: nothing (stdlib `dataclasses`).
- Produces:
  - `@dataclass(frozen=True) PreferenceEdge(preference: str, context_tag: str, valid_at: str, recheck_after: str, invalid_at: str | None = None)`.
  - `class PreferenceMemory` with `add(preference, context_tag, valid_at, recheck_after) -> None`, `active(context_tag: str, as_of: str) -> list[str]`, `stale(as_of: str) -> list[PreferenceEdge]`, `invalidate(preference, context_tag, invalid_at) -> int`, `reinforce(preference, context_tag, valid_at, recheck_after) -> None`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_preferences.py
from research_methodology.storage.preferences import PreferenceEdge, PreferenceMemory


def test_active_returns_preferences_valid_at_date():
    pm = PreferenceMemory()
    pm.add("prefers-copper", "plumbing", "2026-01-01", "2026-12-01")
    assert pm.active("plumbing", "2026-06-01") == ["prefers-copper"]
    assert pm.active("electrical", "2026-06-01") == []


def test_stale_detects_edges_past_recheck():
    pm = PreferenceMemory()
    pm.add("near-ocean", "site", "2026-01-01", "2026-03-01")
    assert [e.preference for e in pm.stale("2026-04-01")] == ["near-ocean"]
    assert pm.stale("2026-02-01") == []


def test_invalidate_removes_from_active():
    pm = PreferenceMemory()
    pm.add("prefers-copper", "plumbing", "2026-01-01", "2026-12-01")
    assert pm.invalidate("prefers-copper", "plumbing", "2026-06-15") == 1
    assert pm.active("plumbing", "2026-07-01") == []


def test_reinforce_extends_validity_with_fresh_edge():
    pm = PreferenceMemory()
    pm.add("prefers-copper", "plumbing", "2026-01-01", "2026-03-01")
    pm.invalidate("prefers-copper", "plumbing", "2026-03-01")
    pm.reinforce("prefers-copper", "plumbing", "2026-03-01", "2026-09-01")
    assert pm.active("plumbing", "2026-05-01") == ["prefers-copper"]


def test_bias_guard_no_evidential_weighting_api():
    pm = PreferenceMemory()
    assert not any("weight" in attr.lower() for attr in dir(pm))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_preferences.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'research_methodology.storage.preferences'`.

- [ ] **Step 3: Write minimal implementation**

```python
# research_methodology/storage/preferences.py
"""Preference memory: context-scoped, staleness-aware, bias-guarded (§9.8).

Bias guard (structural): preferences may shape relevance/framing/which options
surface, never evidential weighting. This module therefore exposes NO weighting
API — enforced by test_bias_guard_no_evidential_weighting_api.
"""
from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class PreferenceEdge:
    preference: str
    context_tag: str
    valid_at: str
    recheck_after: str
    invalid_at: str | None = None


class PreferenceMemory:
    def __init__(self) -> None:
        self._edges: list[PreferenceEdge] = []

    def add(self, preference: str, context_tag: str, valid_at: str, recheck_after: str) -> None:
        self._edges.append(PreferenceEdge(preference, context_tag, valid_at, recheck_after))

    def _is_active(self, edge: PreferenceEdge, as_of: str) -> bool:
        if edge.valid_at > as_of:
            return False
        if edge.invalid_at is not None and as_of >= edge.invalid_at:
            return False
        return True

    def active(self, context_tag: str, as_of: str) -> list[str]:
        seen: list[str] = []
        for e in self._edges:
            if e.context_tag == context_tag and self._is_active(e, as_of):
                if e.preference not in seen:
                    seen.append(e.preference)
        return seen

    def stale(self, as_of: str) -> list[PreferenceEdge]:
        return [
            e for e in self._edges
            if e.invalid_at is None and as_of >= e.recheck_after
        ]

    def invalidate(self, preference: str, context_tag: str, invalid_at: str) -> int:
        count = 0
        for i, e in enumerate(self._edges):
            if (e.preference == preference and e.context_tag == context_tag
                    and e.invalid_at is None):
                self._edges[i] = replace(e, invalid_at=invalid_at)
                count += 1
        return count

    def reinforce(self, preference: str, context_tag: str,
                  valid_at: str, recheck_after: str) -> None:
        self.add(preference, context_tag, valid_at, recheck_after)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_preferences.py -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add research_methodology/storage/preferences.py tests/test_preferences.py
git commit -m "feat: preference memory with bias guard (§9.8)"
```

---

### Task 1.13: Neo4jGraphitiLedger adapter skeleton — deferred integration (§19.2/§21)

Reserves the real-backend seam without pulling `neo4j`/`graphiti-core` into Layer 1 or CI. The skeleton implements the `Ledger` interface, takes its connection from `StorageConfig` (no connection at construction, no top-level `neo4j` import), and raises a clear `NotImplementedError` documenting the deferred real write path (§9.2 pre-structured payloads) and its dependency on the `graph_extraction` model role (§21).

**Files:**
- Create: `research_methodology/storage/neo4j_ledger.py`
- Test: `tests/test_neo4j_ledger_skeleton.py`

**Interfaces:**
- Consumes: `storage.ledger.Ledger`; `storage.config.StorageConfig`; `storage.encryption.Encryptor`.
- Produces: `class Neo4jGraphitiLedger(Ledger)` with `__init__(self, config: StorageConfig, encryptor: Encryptor | None = None)`; all `Ledger` methods raise `NotImplementedError`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_neo4j_ledger_skeleton.py
from pathlib import Path

import pytest

from research_methodology.storage.config import StorageConfig
from research_methodology.storage.ledger import Ledger
from research_methodology.storage.neo4j_ledger import Neo4jGraphitiLedger


def _adapter():
    return Neo4jGraphitiLedger(StorageConfig(data_dir=Path("/tmp/x"),
                                             neo4j_uri="bolt://localhost:7687"))


def test_construction_needs_no_backend():
    # No neo4j import, no connection at construction -> instantiating never raises.
    assert isinstance(_adapter(), Ledger)


def test_every_method_is_deferred_with_a_clear_message():
    adapter = _adapter()
    for call in (
        lambda: adapter.write_episode({}),
        lambda: adapter.get("ep1"),
        lambda: adapter.episodes(),
        lambda: adapter.beliefs_as_of("2026-01-01T00:00:00Z"),
    ):
        with pytest.raises(NotImplementedError) as exc:
            call()
        assert "deferred" in str(exc.value).lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_neo4j_ledger_skeleton.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'research_methodology.storage.neo4j_ledger'`.

- [ ] **Step 3: Write minimal implementation**

```python
# research_methodology/storage/neo4j_ledger.py
"""Deferred real Ledger adapter (§19.2/§21).

Reserves the interface seam. The real write path (§9.2: pre-structured payloads
resolved/deduped by Graphiti using the graph_extraction model role, §21) requires
a running Neo4j and a Layer-3 model client, so it is NOT wired or tested in Layer 1.
Layer 1 uses InMemoryLedger. No top-level neo4j/graphiti import: constructing this
adapter must never require the backend to be installed.
"""
from __future__ import annotations

from research_methodology.storage.config import StorageConfig
from research_methodology.storage.encryption import Encryptor
from research_methodology.storage.ledger import Ledger

_DEFERRED = (
    "Neo4jGraphitiLedger is a deferred integration; Layer 1 uses InMemoryLedger. "
    "The real write path (§9.2 pre-structured payloads via Graphiti) requires a "
    "running Neo4j and the graph_extraction model role (§21)."
)


class Neo4jGraphitiLedger(Ledger):
    def __init__(self, config: StorageConfig, encryptor: Encryptor | None = None) -> None:
        self._config = config
        self._encryptor = encryptor  # stored for the future real adapter; unused here

    def write_episode(self, payload: dict) -> str:
        raise NotImplementedError(_DEFERRED)

    def get(self, episode_id: str) -> dict | None:
        raise NotImplementedError(_DEFERRED)

    def episodes(self, *, session_id: str | None = None) -> list[dict]:
        raise NotImplementedError(_DEFERRED)

    def beliefs_as_of(self, as_of: str, *, session_id: str | None = None) -> list[dict]:
        raise NotImplementedError(_DEFERRED)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_neo4j_ledger_skeleton.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Run the full suite**

Run: `python -m pytest -v`
Expected: PASS — all Layer 0 tests (51) plus the Layer 1 tests added across 1.1–1.13 (~52), green.

- [ ] **Step 6: Commit**

```bash
git add research_methodology/storage/neo4j_ledger.py tests/test_neo4j_ledger_skeleton.py
git commit -m "feat: Neo4jGraphitiLedger adapter skeleton — deferred integration (§19.2/§21)"
```

---

## Non-Goals / Explicitly Deferred (Layer 1)

- **Real Neo4j+Graphiti wiring** — the live write path, entity/edge resolution via the `graph_extraction` model role (§21), and a running Neo4j. Deferred; the `Neo4jGraphitiLedger` skeleton (1.13) reserves the seam. Enters when Layer 3 provides the `ModelClient`.
- **Real at-rest encryption** — Fernet or SQLCipher behind the `Encryptor` protocol (1.2). Deferred; `IdentityEncryptor` is the Layer-1 default. Introduces the first third-party crypto dependency when wired.
- **Docker / docker-compose / deployment** — containerization of the agent + Neo4j (+ a future vector DB). Deferred to **Layer 4 ops (§19.5)**; Layer 1's `StorageConfig` + interface seams are what make it a config exercise, not a rewrite.
- **`VectorStore` interface for embeddings / unstructured data** — a *future* storage family for semantic search / RAG. It will be a new interface alongside `EventLog`/`Ledger`, not a change to them; the embedded (`sqlite-vec`, single-file, most portable) vs. containerized (`pgvector`/Qdrant) choice is made in a later layer. Named here only to reserve the seam.
- **Snapshot-accelerated reads** — Task 1.5 ships the snapshot store + compaction trigger; wiring folds to read `snapshot + tail` is a later optimization (§19.3).
- **Postgres `EventLog` adapter** — the scale-up target; kept a swap-in behind the `EventLog` interface, not built now.

---

## Self-Review (against the spec, Layer 1 scope)

**1. Spec coverage (Part III, Layer 1 bullets):**
- `EventLog` = SQLite(WAL): atomic append, `UNIQUE(event_id)`, snapshot/compaction, `0600` + encryption, tombstone-purge → Tasks 1.2 (encryptor), 1.3 (append/unique/0600/encrypt), 1.4 (tombstone-purge), 1.5 (snapshot/compaction). ✔
- Credibility store, flat maps, RSS log, `write_failures` over it → 1.6, 1.7, 1.8. ✔
- Trusted-source registry = query/view over credibility store (+ ledger) → 1.11. ✔ (Registry is keyed on the credibility store per §5.3's definition; ledger source metadata is available via 1.9 for consumers that need URLs.)
- `Ledger` = Neo4j-backed Graphiti behind an interface with an in-memory fake; pre-structured payload write path; bi-temporal query incl. point-in-time reconstruction → 1.9 (interface + fake + pre-structured/validated write), 1.10 (bi-temporal), 1.13 (real adapter skeleton, deferred per the approved decision). ✔
- Preference memory (§9.8) → 1.12. ✔
- Portability/config foundation (§19.2 + approved portability constraint) → 1.1. ✔

**2. Placeholder scan:** No "TBD"/"handle edge cases"/"similar to Task N". Every code step is complete, runnable Python; every test asserts concrete values. The one `NotImplementedError` (Task 1.13) is the *deliverable* of a deliberately-deferred adapter, tested to raise with a specific message — not a placeholder.

**3. Type consistency (cross-task):** `EventRecord`/`EventLog`/`SQLiteEventLog` (1.3) reused verbatim by 1.4 (adds `purge`/`purge_data_class`), 1.6, 1.7, 1.8. `Encryptor`/`IdentityEncryptor` (1.2) consumed by 1.3 and 1.5. `StorageConfig` (1.1) consumed by 1.13. `CredibilityStore.keys()`/`.state()` (1.6) consumed by 1.11. `Ledger`/`InMemoryLedger`/`LedgerWriteError` (1.9) extended by 1.10 (`beliefs_as_of` added to both the ABC and the fake) and implemented by 1.13's skeleton. `fold`/`CredEvent`/`CredState` (Task 0.12), `validate_episode` (0.6), and `VolatilityClass`/`AuthorityClass`/`SCHEMA_VERSION` are consumed by name with their merged signatures. `WriteFailureQueue.drain` (1.8) depends on `SQLiteEventLog.purge` (1.4) — flagged in-task.

**4. As-merged Layer 0 dependency:** Tasks 1.6/1.11 reason about high-confidence eligibility using the merged `policy()` (durable: `min_evidence_clusters == 1`, `min_explicit == 0`), not the plan-01 prose. The durable/slow registry tests are written to that behavior.

No gaps found; no fixes required.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-09-07-research-methodology-plan-02-storage.md`. Do not begin implementation yet — Layer 1 GitHub artifacts (a `layer-1` label, a `Layer 1 — Storage` milestone, an epic mirroring #17, and one task issue per 1.1–1.13) are created next, then execution proceeds task-by-task per CONTRIBUTING.md (one branch + PR each, TDD, Conventional Commits).
