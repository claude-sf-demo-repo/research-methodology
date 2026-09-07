# Layer 1 — Build Guide (hand-off)

You are building **Layer 1 (Storage)** of the Research Methodology Harness, one task at a time, test-first. This guide is the on-ramp; the **plan is the contract**.

## Read these, in order
1. This guide.
2. [`CONTRIBUTING.md`](../../CONTRIBUTING.md) — the per-task loop, branch/commit/PR rules.
3. The plan: [`plans/2026-09-07-research-methodology-plan-02-storage.md`](plans/2026-09-07-research-methodology-plan-02-storage.md) — **Global Constraints**, then your task.
4. The spec section(s) your task cites: [`specs/2026-09-02-research-methodology-design-v2.md`](specs/2026-09-02-research-methodology-design-v2.md).

The Epic is **#38**; the 13 task issues are **#25–#37**. Each issue is self-contained (Files, Interfaces, exact TDD steps with runnable code) and maps 1:1 to a plan task.

## Non-negotiable rules
- **Build strictly in order** #25 → #37. Never start a task whose *Consumes* interfaces are not yet merged. The dependency spine: 1.1/1.2 → 1.3 → {1.4, 1.5} → 1.6 → 1.11; 1.3 → 1.7, 1.8; 1.9 → 1.10, 1.13.
- **One branch + one PR per task**: `task/1.<n>-<slug>` (e.g. `task/1.3-event-log`). PR body says `Closes #<issue>` and completes the PR template checklist.
- **Test first, always.** Write the failing test, run it, confirm it fails *for the stated reason*, then write the minimal implementation. Never implement before the test.
- **Stay inside the task's Files list.** No scope creep, no drive-by refactors, no touching another task's files.
- **`python -m pytest -v` is green** at the end of every task (all prior tests + the new ones). CI must be green before merge.
- **Conventional Commits** (`feat:`, `test:`, `fix:`, `chore:`). The plan gives the exact commit message per task — use it.

## Layer 1 invariants (from the plan's Global Constraints)
- **Stdlib only.** Do not add any third-party runtime import or dependency in this layer. `sqlite3` is the only new I/O primitive. If a task seems to need `neo4j`, `graphiti`, `cryptography`, or `sqlcipher` — it does not: that path is deferred behind an interface + fake (see below). Adding a dependency is a sign you've misread the task.
- **Purity boundary shifted, not removed.** Disk I/O (`sqlite3`, `pathlib`) is now allowed. Still **no network, no LLM calls, no `datetime.now()`.** Time enters as `now_days: float` (folds) or caller-supplied ISO-8601 strings.
- **Config-driven paths.** No module hard-codes a filesystem path; everything roots at `StorageConfig` / `RM_DATA_DIR` (Task 1.1). This is what keeps the agent lift-and-shift / containerizable.
- **Every persisted record carries `schema_version` and a stable id.** Idempotency is by id (`INSERT OR IGNORE`); a retried append never double-counts. Files are `0600`, the data dir `0700`; every payload is written through the `Encryptor`.
- **Reuse Layer 0, don't re-implement it.** `credibility.fold`/`CredEvent`/`CredState`, `volatility.policy`/`ResolvedPolicy`, `episode.validate_episode`, and `constants.*` are consumed as-is.

## As-merged Layer 0 caveat (matters for #30 and #35)
PR #24 corrected the plan-01 prose: `volatility.policy()` leaves `min_evidence_clusters` **unscaled** when the class's `half_life_days`/`staleness_days` are infinite (`None`). So `policy(DURABLE, ...).min_evidence_clusters == 1` and `durable` has `min_explicit == 0` — a single durable source can reach high confidence. The credibility store (#30) and trusted-source registry (#35) tests are written to this **merged** behavior, not the old prose. Trust the tests in the issue.

## What is deferred (and why your task still ships something testable)
Two backends are real-in-production but **out of scope for Layer 1**; you ship the interface + a fully-tested fake so Layers 2–4 have something to build on:
- **Ledger** (#33): ship the `Ledger` ABC + `InMemoryLedger` fake (validates via `validate_episode`, idempotent by `episode_id`) and, in #37, a `Neo4jGraphitiLedger` **skeleton** that constructs without a backend and raises `NotImplementedError("...deferred...")`. Do **not** import `neo4j`/`graphiti` at module top level or connect to anything.
- **Encryptor** (#26): ship the `Encryptor` protocol + passthrough `IdentityEncryptor`. Real Fernet/SQLCipher is a later task.

If a test asks you to prove a payload is encrypted at rest (#27), it injects a tiny reversible cipher — that's the mechanism check, not a request to add real crypto.

## Definition of done (Layer 1)
All of #25–#37 merged; `python -m pytest -v` green (51 Layer 0 + ~52 Layer 1); CI green on `main`; **no third-party runtime dependency added**; every store reachable behind its interface with the fakes as Layer-1 defaults.

## When something doesn't fit
The plan and its embedded tests are the contract. If a task's code seems wrong or a test can't pass as written, **stop and flag it in the PR / issue** rather than inventing behavior or widening scope — that's exactly how the Layer 0 deviations (PR #24) were surfaced and recorded. Do not silently deviate.
