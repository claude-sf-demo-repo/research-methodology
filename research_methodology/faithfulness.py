"""Deterministic part of the faithfulness gate (§16).

(a) span is unaltered from the cited source, (c) no claim-specifics (numbers/dates) absent
from the span, and a heuristic (b) content-token containment. The true semantic entailment
for (b) is the Layer-3 `faithfulness` role, which may override b_entails_candidate.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "of", "for", "to", "at", "in", "on",
    "and", "or", "has", "have", "had", "with", "as", "by", "that", "this", "it",
}
_SPECIFIC = re.compile(r"\d[\d,\.:/\-]*")  # numbers, dates, versions


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _content_tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in _STOPWORDS}


@dataclass(frozen=True)
class ClaimCheck:
    a_span_unaltered: bool
    b_entails_candidate: bool
    c_no_unsupported_specifics: bool
    verdict: bool


def check(claim: str, cited_span: str, source_content: str) -> ClaimCheck:
    a = _norm(cited_span) in _norm(source_content)

    span_tokens = _content_tokens(cited_span)
    claim_tokens = _content_tokens(claim)
    b = claim_tokens.issubset(span_tokens) if claim_tokens else False

    span_specifics = set(_SPECIFIC.findall(cited_span))
    claim_specifics = set(_SPECIFIC.findall(claim))
    c = claim_specifics.issubset(span_specifics)

    return ClaimCheck(a, b, c, verdict=a and b and c)
