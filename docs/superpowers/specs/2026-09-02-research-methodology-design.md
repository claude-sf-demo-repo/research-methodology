# Research Methodology Harness — Design Spec

**Status:** Approved by user, ready for implementation planning
**Date:** 2026-09-02
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

## 6. Tool Layer

Verified via dedicated research (2026-09-02); provider-agnostic wherever possible, MCP-wrappable where an MCP exists:

| Category | Tools | Notes |
|---|---|---|
| General web search | Tavily (primary, metered free tier) + self-hosted **SearXNG** (free fallback) | SearXNG aggregates ~272 backend engines behind a self-hosted instance, avoiding both Tavily's metering and Brave's card-required "free" tier. Building a from-scratch engine (Common Crawl + custom ranking) was evaluated and rejected as materially more effort for a worse result. |
| Academic/theoretical | Semantic Scholar (MCP available), arXiv API, raw OpenAlex API | arXiv results must be flagged as pre-print/non-peer-reviewed, not equivalent to journal publication. |
| Regulatory/standards | **Confirmed, unsolved gap.** Mitigation: general search scoped with domain allowlists (`.gov`, municipal code portals, standards bodies) | Financial-regulatory APIs (FRED, Census, FINRA BrokerCheck, FDIC BankFind, ESMA registers — all verified real and free) are a narrow **financial-regulatory sub-tier only**; they do not address e.g. building-code lookups (Scenario A). Building a bespoke regulatory-data tool is a candidate for future work, not solved here. |
| Empirical/community | Reddit MCP (`reddit-mcp-server`), Stack Exchange API, Slack MCP (`slack-mcp-server`), Discord (fragmented/lower confidence), Apify social scrapers, plus **`community_hub_map`** (§9.4) | Reddit/Stack Exchange are mainstream defaults, wrong for many niches (e.g. security topics live in CERT/CISA advisories, abuse.ch, BleepingComputer, infosec communities, not Reddit). `community_hub_map` makes "which platform is authoritative for this topic" a learned, growing lookup instead of a hardcoded default. |
| Deep/agentic research | Perplexity Sonar Deep Research, Exa deep search, plus an **internally-encoded plan→search→reflect→iterate loop** | This loop is the pattern behind OpenAI/Gemini Deep Research, Stanford's STORM, and gpt-researcher. LangGraph, CrewAI, Claude Agent SDK, and Pydantic AI were evaluated and rejected as the basis for this — they are orchestration *frameworks* you'd build a research agent *with*, not tools you call; adopting one would be a heavier lift than what Claude Code's own subagent/skill system already provides. |
| Fast-moving/current events | General search + recency filters (Tavily `topic=news`, Exa `category=news`, Brave freshness param), plus a first-party **RSS subscription mechanism** (§12) | No dedicated news API (GDELT, NewsAPI) clearly beat general search + recency filter + cross-check. |

**Fact-check note:** two tools proposed in an earlier conversation were verified as **hallucinated and are explicitly excluded**: "Regulatory Compliance Search API" and "Reuters Business/Financial News MCP" — neither exists. Several others were real but under different names than proposed (e.g. the correct Reddit MCP is `reddit-mcp-server`, not `reddit-mcp-ai`; there is no "PaperMCP" — use the raw OpenAlex API directly).

## 7. Sequential Thinking Integration

The official `Sequential Thinking MCP` (`@modelcontextprotocol/server-sequential-thinking`, part of the official `modelcontextprotocol/servers` reference repo) is used during the deep-research pipeline stage, gated by the same soft-budget rule as the rest of the pipeline (only invoked once the intent score crosses the deep-research threshold). It externalizes the plan→search→reflect→iterate loop into numbered, revisable, branchable thought steps, which get folded into the same session ledger as source citations.

This does not add reasoning capability Claude lacks natively — it adds **structure and auditability** to reasoning that already happens, which is precisely what the local-model-portability goal requires: a weaker model's reasoning becomes inspectable and debuggable in the ledger the same way its sourcing is.

## 8. New-Source Vetting Gate

**Trigger:** the credibility store has no entry for a domain+topic pairing, and the user has not directly named that source. Explicitly user-named sources skip vetting and are seeded directly with `basis: user-specified`.

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
Every episode/edge write passes a deterministic `validate_graph_write(payload, schema)` check before commit. On schema-conformance failure, a bounded retry loop (e.g. 3 attempts) feeds the exact failing field/rule back to the model; persistent failure routes to a logged `write_failures` queue rather than being silently dropped or retried indefinitely. This exists specifically to make graph-writing viable for a weaker/local model, directly addressing the tension identified in research between Graphiti's structured-output demands and the local-model-portability goal.

### 9.4 Credibility Store (flat, source of truth)
```json
{
  "domain": "...", "topic": "...", "trust_score": 0.0,
  "basis": "seed|implicit|explicit-feedback|user-specified|vetted",
  "evidence_ids": ["ep_..."], "evidence_count": 0,
  "last_reinforced_at": "...", "min_evidence_for_high_confidence": 5,
  "user_blocklisted": false
}
```
Numeric, topic-scoped (a source can be high-trust in one topic and untested in another). Untouched scores decay toward neutral (0.5) past a staleness threshold rather than remaining frozen indefinitely. Below `min_evidence_for_high_confidence`, the score reports as provisional. Feedback loop closes via both implicit signal inference (corroboration, contradiction with a higher-trust source, user correction/override) and explicit user feedback, with explicit weighted higher. Plugin-owned, mirrored into the user's global memory system as a lightweight pointer/summary.

### 9.5 `domain_authority_profile` (extensible, seeded)
`{domain, primary_source_definition, examples}` — defines what "primary/peer-reviewed" means *for this specific domain* (e.g. medicine → peer-reviewed journal indexed in PubMed; law → primary statute/case law, not commentary; AI engineering → the lab's own paper/docs, not a blog recap; plumbing → adopted local code text or manufacturer spec). Rigor band 0.9–1.0 is only valid if a cited source's tier matches this definition — checkable, not asserted.

### 9.6 `community_hub_map` (flat, permanently — confirmed via research, not deferred)
`{topic, country (optional), platforms: [{name, pattern, confidence}], discovered_via: seed|discovery-search|user-provided, last_updated}`. Small, closed-cardinality lookup; a graph representation was evaluated and rejected as unnecessary — no realistic query here needs multi-hop traversal.

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

## 12. Test Scenarios & Evaluation

- **Scenario A** — plumbing/building-code troubleshooting: exercises regulatory-tier surfacing, theoretical grounding, empirical/community synthesis, and the confirmed regulatory-gap mitigation.
- **Scenario B** — 30-day NZ caravan trip: exercises personalization scoring, preference-memory citation, and localized empirical sourcing.
- **Scenario C** — fast-moving/current-events query: exercises the low end of the intent-depth spectrum, recency weighting, and (optionally) the RSS triage path.

**Evaluation approach:** manual end-to-end walkthroughs of all three scenarios, scored against a lightweight rubric (source diversity, tier coverage, citation validity per §9.1, conflict-surfacing correctness, vetting-gate behavior on at least one deliberately-novel source). Automated grading is explicitly deferred until the methodology has stabilized through this manual pass.

## 13. Non-Goals / Explicitly Deferred

- A definitive, deeply-considered source-tier taxonomy beyond the three seed tiers (§5) — flagged for a dedicated future conversation.
- Solving the regulatory/standards API gap with a bespoke tool (§6) — documented as a known limitation, not built now.
- Ledger-visibility scaling by intent depth, and hiding intent-score visibility by default (§4) — both are documented future direction, not v1 behavior.
- Automated evaluation/grading (§12) — deferred until manual evaluation stabilizes the methodology.
- Migrating `community_hub_map` or the credibility store to a graph representation — evaluated and rejected for both; not revisited unless usage patterns change materially.

## 14. Naming

The dedicated persona is named **`research-analyst`**.
