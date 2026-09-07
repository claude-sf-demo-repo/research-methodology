"""Cold-start seed data (AU/NZ/US) so no category starts with <2 entries (§8)."""
from __future__ import annotations

from research_methodology.storage.maps import FlatMap

SEED_COMMUNITY_HUBS: dict[str, dict] = {
    "plumbing": {"hub": "reddit.com/r/Plumbing"},
    "python": {"hub": "stackoverflow.com"},
    "caravanning-nz": {"hub": "nzmca.org.nz"},
    "home-renovation-au": {"hub": "whirlpool.net.au/wiki/Renovating"},
}

SEED_DOMAIN_AUTHORITY: dict[str, dict] = {
    "mayoclinic.org": {"authority_class": "canonical", "primary_source_definition": "clinical-consensus"},
    "standards.org.au": {"authority_class": "canonical", "primary_source_definition": "standard"},
    "legislation.govt.nz": {"authority_class": "canonical", "primary_source_definition": "statute"},
    "law.cornell.edu": {"authority_class": "high", "primary_source_definition": "statute"},
}

SEED_CONSUMER_PROTECTION: dict[str, dict] = {
    "AU": {"registry": "accc.gov.au"},
    "NZ": {"registry": "comcom.govt.nz"},
    "US": {"registry": "ftc.gov"},
}

SEED_VOLATILITY_TOPICS: dict[str, dict] = {
    "physics": {"volatility_class": "durable"},
    "mathematics": {"volatility_class": "durable"},
    "iso-standards": {"volatility_class": "durable"},
    "medical-consensus": {"volatility_class": "slow"},
    "regulatory-code": {"volatility_class": "slow"},
    "tech-best-practice": {"volatility_class": "moderate"},
    "product-category": {"volatility_class": "moderate"},
    "news": {"volatility_class": "fast"},
    "prices": {"volatility_class": "fast"},
    "weather": {"volatility_class": "ephemeral"},
}


def _seed_one(m: FlatMap, prefix: str, data: dict[str, dict]) -> int:
    inserted = 0
    for key, value in data.items():
        if m.put(key, value, event_id=f"seed:{prefix}:{key}"):
            inserted += 1
    return inserted


def load_seeds(community: FlatMap, authority: FlatMap,
               consumer: FlatMap, volatility: FlatMap) -> int:
    return (
        _seed_one(community, "community", SEED_COMMUNITY_HUBS)
        + _seed_one(authority, "authority", SEED_DOMAIN_AUTHORITY)
        + _seed_one(consumer, "consumer", SEED_CONSUMER_PROTECTION)
        + _seed_one(volatility, "volatility", SEED_VOLATILITY_TOPICS)
    )
