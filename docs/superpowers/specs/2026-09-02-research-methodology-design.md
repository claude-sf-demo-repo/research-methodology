# Research Methodology Harness — Design Spec

**Status:** Approved by user, hardened after external security/engineering review, ready for implementation planning
**Date:** 2026-09-02 (revised same day — security/concurrency/testing hardening pass)
**Repo:** `github.com/claude-sf-demo-repo/research-methodology`

## 1. Purpose

Design a research harness that lets the user trust *how* an AI-generated answer was researched, not just the answer itself. The harness must intuitively infer research intent, expand queries appropriately, select the right source types, execute the right search strategy (simple retrieval vs. multi-step agentic research), synthesize findings with explicit source-authority weighting, adapt to user-specified credibility benchmarks over time, and maintain full provenance down to the URL for every claim.

This spec is **implementation-agnostic methodology first**; a Claude Code plugin (skill + subagent + MCP tool wiring) is the first reference implementation, built directly from this spec.

## 2. Design Principles

These constraints shaped every schema and procedure below — they are load-bearing, not aspirational:

1. **Local-model portability.** Every scoring/decision step must reduce to a deterministic checklist a weaker/local model can execute correctly, not a holistic judgment call only a frontier model happens to get right. This is why intent scoring, source validation, and vetting are all checklist-driven rather than freeform.
2. **Provenance over assertion.** Every claim of depth, rigor, or personalization must be backed by a literal, checkable citation in the ledger — not self-reported by the model.
3. **Surfacing over silent resolution.** Regulatory/theoretical constraints and newly-encountered sources are always surfaced to the user, even when the harness doesn't block on them.
4. **Extensible, not exhaustively pre-solved.** Source tiers, domain-authority definitions, and community hubs are seeded with known examples and grown through a discovery-and-cache (or discovery-and-ask) pattern rather than requiring an exhaustive taxonomy up front.
5. **Don't block on trust-building.** Using a new, unvetted source never stalls the current research task — vetting runs in parallel and reports back afterward.
6. **All externally-retrieved content is untrusted input, always.** Search results, scraped pages, RSS items, and MCP-fetched content (Slack, Reddit, etc.) are data to reason about, never instructions to execute, and never trusted-as-is before sanitization (§9.2a). This generalizes a live incident (see `~/Desktop/projects/incident-report-2026-09-02-mem0-docs-prompt-injection.md`) where a fetched documentation page carried an embedded instruction disguised as agent-facing navigation guidance.

## 3. Architecture

A single dedicated, always-on subagent — **`research-analyst`** — runs one internal pipeline per request:

```
Score intent → derive budget/label → plan (search vs. multi-step agentic; delegate vs. own-research)
  → execute across source tiers, vetting new sources inline
  → synthesize (weighted, constraints always surfaced)
  → write ledger (Graphiti episodes) + roll up credibility/preference updates
  → deliver answer + compact source ledger + any pending vetting review requests
```

This mirrors the existing `salesforce-cloud-router` triage/dispatch/fold-back pattern, generalized beyond Salesforce clouds: when a specialist persona (e.g. a cloud-expert agent) is clearly the better-suited handler, `research-analyst` dispatches it directly and folds its findings back into the same ledger and synthesis — it delegates and synthesizes, it does not just recommend and stop.

## 4. Intent Scoring

Four dimensions, each scored via a fixed checklist mapped to bands — never a freeform float:

| Dimension | 0.0–0.2 | 0.3–0.5 | 0.6–0.8 | 0.9–1.0 |
|---|---|---|---|---|
| **Depth** | single fact, one source suffices | 2–3 corroborating sources, single-hop | multi-hop, cross-tier synthesis required | exhaustive, many sub-questions, report-length |
| **Rigor** | opinion/casual is fine | factual accuracy matters, low stakes | safety/compliance/financial stakes — must ground in authoritative tier | claims must trace to a primary/peer-reviewed source for this domain |
| **Recency** | timeless fact | slow-changing (annual/seasonal) | fast-changing (weekly/monthly) | breaking, must be hours-fresh |
| **Personalization** | fully generic | context helpful, not essential | requires a known user preference to be useful | requires explicit preference-gathering to answer at all |

Each band claim must cite the evidence that proves it (§9.1). A fixed rule then derives:
- a **soft tool/source budget** (e.g. quick-lookup ≈ 1–2 tool calls; deep-research ≈ 20+), which the agent may exceed while still making clear progress, but should flag if ballooning;
- a **derived taxonomy label** (e.g. `quick-lookup`, `deep-research`, `academic`, `planning`) attached *after* scoring, purely for downstream debugging — never fed back into behavior.

The intent-score block is logged and shown to the user by default in v1. **Documented future direction:** move toward hidden-by-default / shown-on-request, and toward ledger visibility that scales with intent depth (quick lookups show little to nothing; deep-research/academic answers always show full citations) — deferred until trust is established through real usage, not built now.

## 5. Source Tiers & Conflict Resolution

**Tiers** are an extensible taxonomy seeded with three canonical examples: *theoretical/scientific*, *regulatory/standards*, *empirical/community*. New tiers (e.g. historical/archival, financial/market-data) may be recognized and labeled for domains that don't fit the seed set. **Open follow-up, explicitly deferred:** a deeper exploration of the ideal tier taxonomy is out of scope for this spec and flagged for a dedicated future conversation.

**Conflict resolution:** weighted synthesis across tiers — no hard priority order by default. However, if regulatory or theoretical constraints exist for a question, they must **always be surfaced** in the answer, even when the synthesis doesn't treat them as an absolute floor and even when community evidence points elsewhere.

**Worked stress cases:**
- *Regulatory constraint directly contradicts a stated user preference* (e.g. the user wants a fitting/approach the local code doesn't permit): the constraint is always disclosed even if the answer proceeds with the user's preference anyway, and the preference is never silently overridden either. Neither side is resolved silently — the user decides with full information visible in the same answer.
- *The only source that would satisfy a domain's Rigor 0.9–1.0 band is blocklisted*: because rigor bands are only valid when backed by a matching citation (§9.1), the system cannot claim a band it can no longer back with evidence. It gracefully **downgrades the reported band** to whatever the remaining sources actually support and states why (e.g. *"the highest-rigor source for this domain is blocklisted per your instruction; this answer reflects a lower rigor band as a result"*) — it never fabricates compliance and never dead-ends silently.

## 6. Tool Layer

Verified via dedicated research (2026-09-02); provider-agnostic wherever possible, MCP-wrappable where an MCP exists:

| Category | Tools | Notes |
|---|---|---|
| General web search | Tavily (primary, metered free tier) + self-hosted **SearXNG** (free fallback) | SearXNG aggregates ~272 backend engines behind a self-hosted instance, avoiding both Tavily's metering and Brave's card-required "free" tier. Building a from-scratch engine (Common Crawl + custom ranking) was evaluated and rejected as materially more effort for a worse result. **Security requirement:** the self-hosted instance's egress must block private/internal IP ranges (RFC1918, link-local, cloud metadata endpoints) to prevent it being used as an SSRF vector against internal infrastructure. |
| Academic/theoretical | Semantic Scholar (MCP available), arXiv API, raw OpenAlex API | arXiv results must be flagged as pre-print/non-peer-reviewed, not equivalent to journal publication. |
| Regulatory/standards | **Confirmed, unsolved gap.** Mitigation: general search scoped with domain allowlists (`.gov`, municipal code portals, standards bodies) | Financial-regulatory APIs (FRED, Census, FINRA BrokerCheck, FDIC BankFind, ESMA registers — all verified real and free) are a narrow **financial-regulatory sub-tier only**; they do not address e.g. building-code lookups (Scenario A). Building a bespoke regulatory-data tool is a candidate for future work, not solved here. |
| Empirical/community | Reddit MCP (`reddit-mcp-server`), Stack Exchange API, Slack MCP (`slack-mcp-server`), Discord (fragmented/lower confidence), Apify social scrapers, plus **`community_hub_map`** (§9.4) | Reddit/Stack Exchange are mainstream defaults, wrong for many niches (e.g. security topics live in CERT/CISA advisories, abuse.ch, BleepingComputer, infosec communities, not Reddit). `community_hub_map` makes "which platform is authoritative for this topic" a learned, growing lookup instead of a hardcoded default. |
| Deep/agentic research | Perplexity Sonar Deep Research, Exa deep search, plus an **internally-encoded plan→search→reflect→iterate loop** | This loop is the pattern behind OpenAI/Gemini Deep Research, Stanford's STORM, and gpt-researcher. LangGraph, CrewAI, Claude Agent SDK, and Pydantic AI were evaluated and rejected as the basis for this — they are orchestration *frameworks* you'd build a research agent *with*, not tools you call; adopting one would be a heavier lift than what Claude Code's own subagent/skill system already provides. |
| Fast-moving/current events | General search + recency filters (Tavily `topic=news`, Exa `category=news`, Brave freshness param), plus a first-party **RSS subscription mechanism** (§12) | No dedicated news API (GDELT, NewsAPI) clearly beat general search + recency filter + cross-check. |

**Content safety:** all content from SearXNG, RSS feeds, Slack, and Reddit — the highest-risk categories for embedded-instruction injection and PII exposure respectively — passes through the sanitization/redaction gate (§9.2a) before any of it can become an episode or influence synthesis. No exceptions for "trusted" tools; the gate runs on content, not on tool identity.

**Fact-check note:** two tools proposed in an earlier conversation were verified as **hallucinated and are explicitly excluded**: "Regulatory Compliance Search API" and "Reuters Business/Financial News MCP" — neither exists. Several others were real but under different names than proposed (e.g. the correct Reddit MCP is `reddit-mcp-server`, not `reddit-mcp-ai`; there is no "PaperMCP" — use the raw OpenAlex API directly).

## 7. Sequential Thinking Integration

The official `Sequential Thinking MCP` (`@modelcontextprotocol/server-sequential-thinking`, part of the official `modelcontextprotocol/servers` reference repo) is used during the deep-research pipeline stage, gated by the same soft-budget rule as the rest of the pipeline (only invoked once the intent score crosses the deep-research threshold). It externalizes the plan→search→reflect→iterate loop into numbered, revisable, branchable thought steps, which get folded into the same session ledger as source citations.

This does not add reasoning capability Claude lacks natively — it adds **structure and auditability** to reasoning that already happens, which is precisely what the local-model-portability goal requires: a weaker model's reasoning becomes inspectable and debuggable in the ledger the same way its sourcing is.

## 8. New-Source Vetting Gate

**Trigger:** the credibility store has no entry for a domain+topic pairing, and the user has not directly named that source. Explicitly user-named sources skip vetting and are seeded directly with `basis: user-specified`.

**Bypass integrity (security-hardened):** `basis: user-specified` may only be set from a literal statement by the real principal in the live conversation turn — never inferred from retrieved web/forum/MCP content, a delegated specialist's report, or anything else that merely *claims* the user said it. This closes off using the bypass as a whitelist-injection vector. The bypass is also not an unconditional permanent trust grant: it's logged like any other credibility-store entry and remains subject to later blocklisting — it just starts with a high seed score instead of going through the automated vetting procedure.

**Baseline/category discovery:** pulls a reputable comparison source from `community_hub_map`/`domain_authority_profile`. If the category is new or has fewer than 2 seeded examples, the agent asks the user directly for 2–3 more examples rather than guessing — those answers seed the map.

**Legitimacy signals checked:**
- `consumer_protection_registry_map`: country → the relevant complaints/registration body (BBB in the US, ACCC/Scamwatch in Australia, Commerce Commission/Consumer Protection in NZ, etc.), seeded and grown via discovery-and-cache. No findable entry for a business that should reasonably have one, in its claimed operating country, is an explicit red flag in the verdict.
- `community_hub_map` review/scam-chatter platforms, now **country-scoped** in addition to topic-scoped (falls back to global/unscoped entries when no country-specific one exists).
- Fixed **site-quality checklist**: HTTPS present; working contact info/physical address; visible business registration number where the jurisdiction expects one; coherent, present return/refund policy; absence of classic scam markers (artificial urgency, implausible discounts, no findable reviews anywhere, brand/domain mismatch); domain-age/registration signal via search (WHOIS is not directly toolable); content-quality consistency against the chosen baseline.

**Flow — non-blocking:** the vetting gate never stalls the current research task. On first encounter with a new source, the agent uses it, completes the research, and delivers the full answer normally. The ledger then appends a review request: *"New source(s) found: [domain(s)] — please review: [links to vetting-assessment episodes]."*

- **Confirm good** → trust score reinforced; no rerun, the delivered answer stands.
- **Reject with reason** → the stated reason is stored as evidence on that credibility-store entry, and the research **reruns**, excluding/deprioritizing that source, informed by the rejection reasoning for future source selection in that category.
- **Blocklist** → same rerun-excluding-the-source behavior as reject, but as a permanent hard exclusion (`user_blocklisted: true`) rather than a score penalty.

## 9. Data Schemas

### 9.1 Intent Score
```json
{
  "session_id": "...", "timestamp": "...",
  "dimensions": {
    "depth":           {"band": "0.6-0.8", "validated_by": "citation_count>=4 across >=2 tiers", "citation_ids": ["ep_1", "ep_2"]},
    "rigor":           {"band": "0.9-1.0", "validated_by": "matches_domain_authority", "domain": "plumbing", "citation_ids": ["ep_3"]},
    "recency":         {"band": "0.3-0.5", "validated_by": "source_publish_date_within_seasonal_window"},
    "personalization": {"band": "0.6-0.8", "validated_by": "memory_citations", "memory_citations": ["pref_electrical_hookup", "pref_near_ocean"]}
  },
  "derived_label": "deep-research",
  "tool_budget": {"soft_max_calls": 12, "actual_calls": 9}
}
```

### 9.2a Sanitization & Redaction Gate (required, upstream of every episode write)
Every piece of externally-retrieved content (search results, scraped pages, RSS items, Slack/Reddit MCP output) passes through this gate **before** it can become `content`, `entities_mentioned`, or any other episode field:
1. **Injection stripping** — content is scanned for embedded second-person imperatives directed at an agent/crawler (the pattern that surfaced in the Mem0 incident: fake "instructions," fake navigation directives, disguised as page content). Detected instruction-like spans are excluded from what gets treated as citable fact content and flagged in the episode as `injection_flagged: true` with the excluded span logged separately for audit, never silently dropped without a trace and never executed.
2. **PII redaction** — content sourced from Slack/Reddit/Discord (inherently personal, conversational sources) is scanned for PII (real names outside public-figure/official-source context, emails, phone numbers, addresses, handles tied to private accounts) and masked before commit. This is mandatory specifically for the empirical/community tier, since that's where PII exposure is concentrated — theoretical/regulatory/official sources rarely carry this risk but pass through the same gate for consistency.

This gate is what makes §2 Principle 6 concrete rather than aspirational: nothing from an external source reaches the ledger, the graph, or synthesis without passing through it first.

### 9.2 Session Ledger — Graphiti Episodes
Built directly on **Graphiti** (Zep's open-source temporal knowledge graph library) from day one, per explicit user decision overriding the initially-recommended "flat now, graph later" path. Every source use, Sequential-Thinking step, delegation, and synthesis output is written as an Episode:
```json
{
  "episode_id": "...", "session_id": "...", "timestamp": "...",
  "episode_type": "source_citation",
  "content": "raw snippet/quote",
  "source_metadata": {
    "url": "...", "title": "...", "tier": "regulatory", "community_hub": null,
    "domain_authority_match": true, "trust_score_at_use": 0.82, "retrieved_at": "..."
  },
  "entities_mentioned": ["1/2-inch NPT fitting", "Uniform Plumbing Code §605"],
  "topic_tags": ["plumbing", "pipe-fitting", "building-code"],
  "relation_hints": [{"subject": "1/2-inch NPT fitting", "predicate": "complies_with", "object": "UPC §605"}],
  "corroborates": ["ep_x"], "contradicts": [],
  "memory_citations": ["pref_electrical_hookup"],
  "valid_at": "...", "invalid_at": null
}
```
`trust_score_at_use` is a snapshot: the flat credibility store can keep changing after the fact without rewriting what a past answer actually relied on. `valid_at`/`invalid_at` gives bi-temporal semantics for free — facts get superseded, never deleted.

### 9.3 Output-Validation/Repair Layer (required component)
Every episode/edge write passes a deterministic `validate_graph_write(payload, schema)` check before commit. On schema-conformance failure, a bounded retry loop (max 3 attempts) feeds the exact failing field/rule back to the model — but with **stagnation detection**: if attempt 2's validation error falls in the same category as attempt 1's (not just "still failing," but the same kind of misunderstanding — e.g. still missing the same required field after being told about it), the loop short-circuits to the `write_failures` queue immediately rather than burning a third identical attempt. This is what makes the retry budget cheap in the common failure mode (a weak model that fundamentally doesn't understand the schema) while still giving genuinely transient failures their full 3 attempts. Persistent failures are always logged, never silently dropped or retried indefinitely. This exists specifically to make graph-writing viable for a weaker/local model, directly addressing the tension identified in research between Graphiti's structured-output demands and the local-model-portability goal.

### 9.4 Credibility Store (append-only event log, source of truth)
**Concurrency model (security/engineering-hardened):** an always-on agent handling concurrent research pipelines will inevitably hit write-locks or races if this is maintained as a mutable in-place record. Fix: the store is **append-only**. Every update — a new vetting verdict, a confirm/reject/blocklist, an implicit corroboration signal — is a new event record, never an in-place mutation:
```json
{
  "event_id": "...", "domain": "...", "topic": "...", "timestamp": "...",
  "event_type": "seed|implicit-signal|explicit-feedback|user-specified|vetted|blocklist",
  "score_delta_or_value": 0.0, "evidence_ids": ["ep_..."], "reason": "..."
}
```
"Current state" (trust score, evidence count, blocklist status) is computed by a deterministic **fold function** over all events for a given `domain+topic` key, read-time, not stored as a separately-mutated field. This eliminates write-locks/races structurally — concurrent pipelines can append simultaneously with no coordination needed, since nothing is ever overwritten. It's also more local-model-friendly: append-only writes require no read-modify-write reasoning.

Numeric, topic-scoped (a source can be high-trust in one topic and untested in another). The fold function applies decay toward neutral (0.5) for keys with no recent events past a staleness threshold, rather than a score remaining frozen indefinitely. Below a `min_evidence_for_high_confidence` threshold (computed from event count), the score reports as provisional. A `blocklist` event, once folded, overrides any score permanently regardless of later positive events (blocklist can only be reversed by an explicit new event type, not accumulated positive signal). Feedback loop closes via both implicit signal inference and explicit user feedback, with explicit weighted higher in the fold function. Plugin-owned, mirrored into the user's global memory system as a lightweight pointer/summary of folded state.

### 9.5 `domain_authority_profile` (extensible, seeded)
`{domain, primary_source_definition, examples}` — defines what "primary/peer-reviewed" means *for this specific domain* (e.g. medicine → peer-reviewed journal indexed in PubMed; law → primary statute/case law, not commentary; AI engineering → the lab's own paper/docs, not a blog recap; plumbing → adopted local code text or manufacturer spec). Rigor band 0.9–1.0 is only valid if a cited source's tier matches this definition — checkable, not asserted.

### 9.6 `community_hub_map` (flat, permanently — confirmed via research, not deferred)
`{topic, country (optional), platforms: [{name, pattern, confidence}], discovered_via: seed|discovery-search|user-provided, last_updated}`. Small, closed-cardinality lookup; a graph representation was evaluated and rejected as unnecessary — no realistic query here needs multi-hop traversal. **Same append-only/fold concurrency model as §9.4** applies here too: additions to a topic's platform list are appended events, not in-place array mutations, folded at read time — this is a general rule for every flat store in this spec, not specific to the credibility store.

### 9.7 `consumer_protection_registry_map` (extensible, seeded)
`{country, registry_name, url_pattern, last_updated}` — e.g. US → BBB, Australia → ACCC/Scamwatch, NZ → Commerce Commission/Consumer Protection. Grown via the same discovery pattern as other lookups.

### 9.8 Personalization Preference Memory — graph-native
A `Preference` node connected via an `applies_when` edge to context-tag node(s) (e.g. `camping-trip`), each edge carrying `valid_at`/`recheck_after` (explicit date or event-triggered, e.g. "next trip with this context tag"). Staleness sets `invalid_at` and triggers a re-ask rather than silently persisting a possibly-outdated preference; reinforcement creates a fresh edge rather than mutating history. Preferences are gathered in-conversation when missing and persisted, never assumed.

## 10. Adaptive Learning Summary

Two things are learned over time, both governed by the credibility-store feedback rules above:
1. **Source credibility** — per-topic trust scores, closed by implicit signals + explicit feedback (explicit weighted higher), including the vetting-gate outcomes.
2. **User preferences** — context-scoped, staleness-aware, re-confirmed rather than assumed permanent.

## 11. RSS / Current-Events Subscription

A first-party feed registry (user-registered feed URL + topic tags), polled on a recurring schedule via `CronCreate` (durable recurring jobs; `ScheduleWakeup` is unsuitable here as it's for single-session self-pacing, not durable cross-session scheduling). **Two-stage triage per item:** a cheap title/headline-only relevance pass runs first; every item is logged regardless of outcome (title, feed, timestamp, triage verdict). Only items passing triage proceed to full-content summarization, appended to the same log entry. No third-party RSS/aggregator service (Feedly, Inoreader) or community RSS-MCP package is used — both were evaluated and rejected as adding a dependency for no real benefit over direct RSS/Atom parsing.

## 12. Testing Strategy — Two Distinct Layers

Earlier drafts of this spec bundled "testing" into one deferred item. That conflated two genuinely different layers with different risk profiles; splitting them explicitly:

**12a. Scenario-level behavioral evaluation (deliberately manual for now — user decision, unchanged)**
- **Scenario A** — plumbing/building-code troubleshooting: exercises regulatory-tier surfacing, theoretical grounding, empirical/community synthesis, and the confirmed regulatory-gap mitigation.
- **Scenario B** — 30-day NZ caravan trip: exercises personalization scoring, preference-memory citation, and localized empirical sourcing.
- **Scenario C** — fast-moving/current-events query: exercises the low end of the intent-depth spectrum, recency weighting, and (optionally) the RSS triage path.

Evaluated via manual end-to-end walkthroughs scored against a lightweight rubric (source diversity, tier coverage, citation validity per §9.1, conflict-surfacing correctness, vetting-gate behavior on at least one deliberately-novel source). Automated grading of *whether an answer is good* is intentionally deferred until the methodology has stabilized through this manual pass — this specific deferral remains a deliberate scope choice, not an oversight.

**12b. Schema/unit-level testing and linting (NOT deferred — required from day one)**
This is a different layer entirely: whether every write actually conforms to its declared structure, independent of whether the research behind it was good. A pipeline this dependent on precise JSON-schema enforcement (§9.1–9.8, the validation/repair layer in §9.3) needs this from the first line of implementation code, not after the methodology "stabilizes":
- Unit tests for every schema validator (Intent Score, Episode, credibility-store event, `community_hub_map` event, `domain_authority_profile`, `consumer_protection_registry_map`, Preference node/edge) — valid-payload and invalid-payload cases for each.
- **Checklist linting**: the intent-scoring rubric bands (§4's table) and the JSON payload structure (§9.1) must be generated from one shared source of truth (e.g. a single constants/schema file both the documentation and the validator import from), with a CI lint check that fails the build if the prose rubric and the enforced schema drift apart.
- Unit tests for the append-only fold functions (§9.4, §9.6) — specifically including concurrent-append test cases, to verify the structural race-avoidance claim rather than asserting it untested.
- Unit tests for the stagnation-detection retry logic (§9.3) — verify it actually short-circuits on repeated same-category errors and doesn't false-positive on genuinely-improving retries.
- Unit tests for the sanitization/redaction gate (§9.2a) — a fixed set of known injection patterns (including the Mem0 incident's actual pattern) and known PII patterns, asserting they're caught before reaching an episode.

This layer ships alongside the first implementation of each component, not as a follow-up phase.

## 13. Non-Goals / Explicitly Deferred

- A definitive, deeply-considered source-tier taxonomy beyond the three seed tiers (§5) — flagged for a dedicated future conversation.
- Solving the regulatory/standards API gap with a bespoke tool (§6) — documented as a known limitation, not built now.
- Ledger-visibility scaling by intent depth, and hiding intent-score visibility by default (§4) — both are documented future direction, not v1 behavior.
- Automated *scenario-level behavioral* grading (§12a) — deferred until manual evaluation stabilizes the methodology. This does **not** cover schema/unit-level testing (§12b), which is required from day one and is explicitly not deferred.
- Migrating `community_hub_map` or the credibility store to a graph representation — evaluated and rejected for both; not revisited unless usage patterns change materially. (Both remain append-only event logs per §9.4/§9.6, which was a later hardening pass, not a reversal of the flat-vs-graph decision.)
- A dedicated bespoke SSRF-scanning/network-security review of the self-hosted SearXNG deployment beyond the baseline egress restriction in §6 — flagged as a candidate for security review once the instance is actually stood up, not solved at the spec level here.

## 14. Naming

The dedicated persona is named **`research-analyst`**.
