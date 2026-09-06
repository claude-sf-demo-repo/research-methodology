"""Source independence clustering (§5.2)."""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Source:
    id: str
    domain: str = ""
    author: str = ""
    content: str = ""
    cited_primary: str = ""


def _shingles(text: str, n: int = 3) -> set[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    if len(tokens) < n:
        return {" ".join(tokens)} if tokens else set()
    return {" ".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def _shares_signal(s1: Source, s2: Source, threshold: float) -> bool:
    if s1.domain and s1.domain == s2.domain:
        return True
    if s1.author and s1.author == s2.author:
        return True
    if s1.cited_primary and s1.cited_primary == s2.cited_primary:
        return True
    if s1.content and s2.content:
        if _jaccard(_shingles(s1.content), _shingles(s2.content)) >= threshold:
            return True
    return False


def cluster(sources: list[Source], jaccard_threshold: float = 0.8) -> list[list[str]]:
    parent: dict[str, str] = {s.id: s.id for s in sources}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: str, y: str) -> None:
        parent[find(x)] = find(y)

    for i, s1 in enumerate(sources):
        for s2 in sources[i + 1:]:
            if _shares_signal(s1, s2, jaccard_threshold):
                union(s1.id, s2.id)

    groups: dict[str, list[str]] = {}
    for s in sources:
        groups.setdefault(find(s.id), []).append(s.id)
    result = [sorted(ids) for ids in groups.values()]
    result.sort(key=lambda ids: ids[0])
    return result


def independence_factor(source_id: str, clusters: list[list[str]]) -> float:
    for c in clusters:
        if source_id in c:
            return 1.0 / len(c)
    return 1.0
