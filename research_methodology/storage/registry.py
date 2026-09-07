"""Trusted-source registry: a view over the credibility store (§5.3)."""
from __future__ import annotations

from dataclasses import dataclass

from research_methodology.constants import VolatilityClass
from research_methodology.storage.credibility_store import CredibilityStore

_DURABLE_CLASSES = {VolatilityClass.DURABLE.value, VolatilityClass.SLOW.value}


@dataclass(frozen=True)
class TrustedSource:
    domain: str
    topic: str
    volatility_class: str
    score: float
    confidence: str


class TrustedSourceRegistry:
    def __init__(self, credibility_store: CredibilityStore, trust_bar: float = 0.0) -> None:
        self._store = credibility_store
        self._trust_bar = trust_bar

    def query(self, topic: str, now_days: float) -> list[TrustedSource]:
        out: list[TrustedSource] = []
        for domain, key_topic, volatility_class in self._store.keys():
            if key_topic != topic or volatility_class not in _DURABLE_CLASSES:
                continue
            st = self._store.state(domain, key_topic, now_days)
            if st.blocked or st.confidence != "high" or st.score < self._trust_bar:
                continue
            out.append(TrustedSource(domain, key_topic, volatility_class, st.score, st.confidence))
        return out
