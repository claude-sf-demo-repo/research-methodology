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
