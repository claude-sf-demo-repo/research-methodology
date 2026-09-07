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
