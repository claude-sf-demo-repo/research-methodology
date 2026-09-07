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
