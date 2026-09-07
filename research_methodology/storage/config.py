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
