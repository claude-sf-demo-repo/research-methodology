# Contributing — subagent-driven TDD

This repo is built one task at a time. Each task is a GitHub issue (e.g. **Task 0.3**) derived from a layer plan in [`docs/superpowers/plans/`](docs/superpowers/plans/). The issue body is self-contained: the files to touch, the interfaces it consumes/produces, and the exact TDD steps with runnable code.

## The loop (per task)

1. **Read the issue and the spec section(s) it cites.** Canonical spec: [`docs/superpowers/specs/2026-09-02-research-methodology-design-v2.md`](docs/superpowers/specs/2026-09-02-research-methodology-design-v2.md).
2. **Write the failing test first**, then run it and confirm it fails for the expected reason.
3. **Write the minimal implementation** to make it pass — no more than the task asks.
4. **Run the full suite** (`python -m pytest -v`) and confirm green.
5. **Commit** with a Conventional Commits message.

Never write implementation before its test. Never touch files outside the task's **Files** list.

## Branches, commits, PRs

- One branch per task: `task/0.<n>-<slug>` (e.g. `task/0.3-schemas`).
- Small, frequent commits; Conventional Commits (`feat:`, `test:`, `chore:`, `fix:`).
- One PR per task. The PR body says `Closes #<issue>` and completes the checklist in the PR template.
- CI (`.github/workflows/ci.yml`) must be green before merge.

## Order matters

Build strictly bottom-up. Do not start a task whose dependencies (its **Consumes** interfaces) are not yet merged. The plan lists tasks in dependency order; follow it.

## Global constraints (Layer 0)

- Python 3.11+, standard library only at runtime; `pytest` for tests.
- Package name: `research_methodology`.
- **Single source of truth:** all enums, tier base-weights, the volatility policy table, and fold constants live in `research_methodology/constants.py`. No other module hard-codes these values; a drift-check test (Task 0.15) enforces this.
- Every persisted record carries `schema_version`; every event carries a stable `event_id`.
- **Purity:** Layer 0 modules perform no network, no disk I/O, no clock reads (time enters as an injected `now_days`), and no LLM calls.

The plan's **Global Constraints** section is the authoritative list.
