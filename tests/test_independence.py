from research_methodology.independence import Source, cluster, independence_factor


def test_same_domain_sources_cluster_together():
    srcs = [
        Source("a", domain="news.example", content="water scarcity worsens in region"),
        Source("b", domain="news.example", content="unrelated sports recap tonight"),
        Source("c", domain="other.example", content="fresh independent coverage here"),
    ]
    clusters = cluster(srcs)
    assert ["a", "b"] in clusters
    assert ["c"] in clusters


def test_near_duplicate_content_across_domains_clusters():
    body = "the council approved the new water restrictions effective monday morning"
    srcs = [
        Source("a", domain="one.example", content=body),
        Source("b", domain="two.example", content=body + " today"),
    ]
    assert cluster(srcs) == [["a", "b"]]


def test_independence_factor_is_inverse_cluster_size():
    clusters = [["a", "b"], ["c"]]
    assert independence_factor("a", clusters) == 0.5
    assert independence_factor("c", clusters) == 1.0
