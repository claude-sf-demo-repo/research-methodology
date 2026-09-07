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
