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
