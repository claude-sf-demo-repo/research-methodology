from research_methodology.storage.event_log import SQLiteEventLog
from research_methodology.storage.maps import FlatMap
from research_methodology.storage import seeds


def _map(tmp_path, stream):
    return FlatMap(SQLiteEventLog(tmp_path / "events.db"), stream)


def test_put_get_latest_writer_wins(tmp_path):
    m = _map(tmp_path, "community_hub_map")
    m.put("plumbing", {"hub": "reddit.com/r/Plumbing"}, "ev1")
    m.put("plumbing", {"hub": "reddit.com/r/plumbers"}, "ev2")
    assert m.get("plumbing") == {"hub": "reddit.com/r/plumbers"}


def test_get_missing_returns_none(tmp_path):
    assert _map(tmp_path, "s").get("absent") is None


def test_seed_volatility_map_classifies_physics_durable(tmp_path):
    log = SQLiteEventLog(tmp_path / "events.db")
    vol = FlatMap(log, "volatility_topic_class")
    seeds.load_seeds(FlatMap(log, "community_hub_map"),
                     FlatMap(log, "domain_authority_profile"),
                     FlatMap(log, "consumer_protection_registry_map"),
                     vol)
    assert vol.get("physics") == {"volatility_class": "durable"}
    assert vol.get("news") == {"volatility_class": "fast"}


def test_seeding_is_idempotent(tmp_path):
    log = SQLiteEventLog(tmp_path / "events.db")
    maps = (FlatMap(log, "community_hub_map"),
            FlatMap(log, "domain_authority_profile"),
            FlatMap(log, "consumer_protection_registry_map"),
            FlatMap(log, "volatility_topic_class"))
    first = seeds.load_seeds(*maps)
    second = seeds.load_seeds(*maps)
    assert first > 0 and second == 0


def test_consumer_protection_seeds_cover_au_nz_us(tmp_path):
    assert {"AU", "NZ", "US"} <= set(seeds.SEED_CONSUMER_PROTECTION)
