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
    @abstractmethod
    def beliefs_as_of(self, as_of: str, *, session_id: str | None = None) -> list[dict]:
        """Episodes believed at ISO-8601 `as_of`: valid_at <= as_of < invalid_at (§9.9)."""


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
