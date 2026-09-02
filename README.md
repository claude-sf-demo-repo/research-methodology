# Research Methodology Harness

A research harness that lets you trust *how* an answer was researched — not just the answer. It infers research intent, plans and expands queries, selects source types, executes the right strategy (simple retrieval vs. multi-step agentic research), **synthesises claim-by-claim with verified attribution to sources**, weights sources by an explicit deterministic function, learns which sources to trust and reuse over time, and keeps full provenance to the URL for every claim. Two promises are load-bearing: **process auditability** and **answer faithfulness**.

## Canonical documents

- **Design spec (v2 — current, approved):** [`docs/superpowers/specs/2026-09-02-research-methodology-design-v2.md`](docs/superpowers/specs/2026-09-02-research-methodology-design-v2.md). Part II is the spec proper; Part III is the layer-by-layer build decomposition; Part IV records the seven resolved design decisions.
- **Design spec (v1 — superseded, kept for history):** [`docs/superpowers/specs/2026-09-02-research-methodology-design.md`](docs/superpowers/specs/2026-09-02-research-methodology-design.md).
- **Layer 0 implementation plan:** [`docs/superpowers/plans/2026-09-02-research-methodology-plan-01-foundation.md`](docs/superpowers/plans/2026-09-02-research-methodology-plan-01-foundation.md) — 15 bite-sized TDD tasks; each is mirrored by a GitHub issue under the **Layer 0 — Foundation** milestone.

## How this repo is being built

Bottom-up, layer by layer, under **subagent-driven, test-driven development**: a fresh worker implements one task at a time, writing the failing test first. Every layer is testable with fakes for the layer above.

| Layer | Scope | Status |
|---|---|---|
| **0 — Foundation** | Pure, deterministic core: constants/SSOT, schemas, validators, sanitisation, source weighting, independence clustering, volatility policy, credibility folds, validation/repair, faithfulness checklist. No network, no I/O, no LLM, no clock reads; stdlib only. | **In progress** — issues open |
| 1 — Storage | SQLite (WAL) event logs + Neo4j-backed Graphiti ledger behind interfaces. | Planned |
| 2 — Tools | Central egress guard + per-tier executors behind a mockable `ToolClient`. | Planned |
| 3 — Judgment | LLM components behind a role-aware `ModelClient` (five-role router, spec §21). | Planned |
| 4 — Orchestrator + eval | End-to-end pipeline, resilience, cost ceilings, golden-set evaluation. | Planned |

Only the **Layer 0** plan and issues exist today. Layers 1–4 will be planned after Layer 0 is green and reviewed.

## Layer 0 quickstart (after Task 0.1 lands `pyproject.toml`)

```bash
pip install -e ".[dev]"
python -m pytest -v
```

Layer 0 targets Python 3.11+ and is **standard-library only** at runtime (`pytest` is the sole dev dependency).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the TDD loop, branch/PR conventions, and how to pick up a task issue.

## Security note

All externally-retrieved content is untrusted input — data to reason about, never instructions to execute (spec §2, Principles 6–7). This principle governs both the design and the code.
