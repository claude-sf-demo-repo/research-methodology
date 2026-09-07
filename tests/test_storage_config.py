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
