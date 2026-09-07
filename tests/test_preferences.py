from research_methodology.storage.preferences import PreferenceEdge, PreferenceMemory


def test_active_returns_preferences_valid_at_date():
    pm = PreferenceMemory()
    pm.add("prefers-copper", "plumbing", "2026-01-01", "2026-12-01")
    assert pm.active("plumbing", "2026-06-01") == ["prefers-copper"]
    assert pm.active("electrical", "2026-06-01") == []


def test_stale_detects_edges_past_recheck():
    pm = PreferenceMemory()
    pm.add("near-ocean", "site", "2026-01-01", "2026-03-01")
    assert [e.preference for e in pm.stale("2026-04-01")] == ["near-ocean"]
    assert pm.stale("2026-02-01") == []


def test_invalidate_removes_from_active():
    pm = PreferenceMemory()
    pm.add("prefers-copper", "plumbing", "2026-01-01", "2026-12-01")
    assert pm.invalidate("prefers-copper", "plumbing", "2026-06-15") == 1
    assert pm.active("plumbing", "2026-07-01") == []


def test_reinforce_extends_validity_with_fresh_edge():
    pm = PreferenceMemory()
    pm.add("prefers-copper", "plumbing", "2026-01-01", "2026-03-01")
    pm.invalidate("prefers-copper", "plumbing", "2026-03-01")
    pm.reinforce("prefers-copper", "plumbing", "2026-03-01", "2026-09-01")
    assert pm.active("plumbing", "2026-05-01") == ["prefers-copper"]


def test_bias_guard_no_evidential_weighting_api():
    pm = PreferenceMemory()
    assert not any("weight" in attr.lower() for attr in dir(pm))
