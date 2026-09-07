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
