"""Deterministic sanitization & redaction gate (§9.2a).

Layers implemented here: (1) normalization/decode, (2) deterministic injection-pattern
rules, (3) content-based PII redaction. The injection-resistant *judge* is the Layer-3
`scoring` role and is not implemented in Layer 0. This gate never executes retrieved content.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

_ZERO_WIDTH = dict.fromkeys(map(ord, "​‌‍﻿"), None)

# Instruction-like spans: imperative agent-steering and declarative source-steering.
_INJECTION_PATTERNS = [
    re.compile(r"ignore (all )?previous instructions.*?(?=[.!?]|$)", re.I),
    re.compile(r"disregard (the )?(above|prior).*?(?=[.!?]|$)", re.I),
    re.compile(r"you are now .*?(?=[.!?]|$)", re.I),
    re.compile(r"(please )?fetch (the )?(complete )?.*?https?://\S+", re.I),
    re.compile(r"system:\s*.*?(?=[.!?]|$)", re.I),
]

_EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
_PHONE = re.compile(r"\b(?:\+?\d[\d\-\s]{7,}\d)\b")


@dataclass(frozen=True)
class SanitizeResult:
    clean: str
    flags: tuple[str, ...]
    excluded_spans: tuple[str, ...]
    redactions: int


def sanitize(content: str) -> SanitizeResult:
    # (1) Normalize: strip zero-width, fold homoglyphs via NFKC, drop HTML comments.
    text = content.translate(_ZERO_WIDTH)
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)

    # (2) Injection rules: excise instruction-like spans, log them, never execute.
    flags: list[str] = []
    excluded: list[str] = []
    for pat in _INJECTION_PATTERNS:
        for m in pat.finditer(text):
            excluded.append(m.group(0).strip())
        text = pat.sub("", text)
    if excluded:
        flags.append("injection")

    # (3) PII redaction (content-based, all tiers).
    redactions = 0
    text, n = _EMAIL.subn("[REDACTED_EMAIL]", text)
    redactions += n
    text, n = _PHONE.subn("[REDACTED_PHONE]", text)
    redactions += n
    if redactions:
        flags.append("pii")

    clean = re.sub(r"\s{2,}", " ", text).strip()
    return SanitizeResult(clean, tuple(flags), tuple(excluded), redactions)
