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
