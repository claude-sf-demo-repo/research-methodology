# Final Review + v2 Spec — Research Methodology Harness

## Context

This is the last review of `~/Downloads/2026-09-02-research-methodology-design (1).md` before it becomes an implementation plan built by lower-capability models under subagent-driven, test-driven development. The goal of this document is to be complete enough that the next step is `writing-plans`, not another review.

**v2.1 update.** The seven open decisions in Part IV are now resolved (see Part IV for the answers), and one design upgrade was added throughout: an **Information Volatility Model** (§5.3) that makes retention and trust a function of how fast the underlying information changes and how authoritative the source is. This unifies what were two separate questions (retention TTLs and credibility-fold constants) into one dimension, and unlocks point-in-time belief reconstruction and durable-source reuse.

**What this review is based on.** Four parallel expert deep-dives (AI/evaluation, adversarial security, software-engineering/testing/decomposition, research-methodology/trust-UX) plus my own independent close reading of the spec and the anchoring incident report (`~/Desktop/projects/incident-report-2026-09-02-mem0-docs-prompt-injection.md`). Two of the four reviewers wedged in a tooling tangle; one of them had already written a complete review to disk, which was recovered, and the fourth dimension was covered from my own analysis. Every Critical finding below is corroborated by at least two independent sources.

**Provenance note (two stray files to manage).** The wedged reviewers left `~/Downloads/2026-09-02-research-methodology-design-REVIEW.md` (their raw review, now folded into this document) and a spec copy at `/private/tmp/research-methodology/docs/superpowers/specs/2026-09-02-research-methodology-design.md`. Delete or keep them as you like; nothing here depends on them.

**How to use this document.** Part I is the review and prioritization (the review of v1 — still the justification). Part II is the rewritten v2 spec you can copy into the repo. Part III is the build decomposition for handoff. Part IV lists the seven decisions and their resolutions. Severity tags: **[C]** critical, **[H]** high, **[M]** medium, **[L]** low. Type tags: **must-fix** (before writing the plan), **should-fix** (fold in during planning — all now in v1), **nice-to-have**.

---

# PART I — Review & Prioritization

## I.1 Verdict

The spec is a strong, security-conscious *systems* design with an excellent audit substrate, and it is unusually honest (it fact-checks its own tool claims and separates real testing layers). It under-delivers on the harder half of its own promise. "Trust *how* an answer was researched" hides two promises:

1. **Process is auditable** — you can inspect what was searched, from where, weighted how. **Delivered well** (the Graphiti ledger, intent-score block, append-only credibility store, Sequential-Thinking capture).
2. **The answer is faithful to its sources** — the claims are actually supported by the cited sources. **Not delivered.** Every check in the spec verifies a citation of the right *tier* exists; nothing verifies the cited source *says what the answer claims*. A weak model can attach a real, authoritative citation to an unsupported sentence and pass every gate.

A trusted research agent that guarantees provenance but not faithfulness is trustworthy about its bibliography and unverified about its conclusions. Closing that gap is the single highest-value change, and it is cheap (span-copy plus a fixed checklist, not holistic judgment).

Beyond faithfulness, the spec is strong wherever the work is **bookkeeping and provenance** and thin-to-missing wherever the work is **generative judgment** (synthesis, weighting, extraction, faithfulness) or **operational** (runtime, storage, cost, security posture, deletion). That boundary is exactly where a weak-model build will stall.

## I.2 Capability coverage map

| # | Capability | Spec coverage | Gap |
|---|---|---|---|
| 1 | Intent understanding & budgeting | §4 strong, but conflates provisional vs. validated scoring | H |
| 2 | Query planning / decomposition / expansion | §1 promises it; no section specifies how | H |
| 3 | Tiered source acquisition | §6 strong | — |
| 4 | Source vetting & learned credibility | §8/§9.4 strong, but poisonable + vertical-reading bias | H |
| 5 | Untrusted-content ingestion safety | §9.2a present but detection-based (weak primary control) | C |
| 6 | Evidence extraction & provenance | provenance strong; faithful extraction unguarded | C |
| 7 | Conflict detection, weighting, independence | weighting undefined; no independence check | C |
| 8 | Synthesis (grounded answer generation) | weakest — no attribution or faithfulness gate | C |
| 9 | Uncertainty, calibration, abstention | partial (band downgrade §5); no abstention path | H |
| 10 | Personalization without bias | §9.8 good; confirmation-bias safeguard missing | H |
| 11 | Auditability & reproducibility | audit strong; reproducibility record thin | M |
| 12 | Learning / adaptation loop | §10/§9.4 good; poisoning-resistance thin | H |
| 13 | Evaluation & QA | §12b strong; metric definitions missing | H |
| 14 | Security & privacy | scattered; no threat model; several gaps | H |
| 15 | Ops, storage infra, cost control, migration | thin/absent | H |
| 16 | Human-in-the-loop / decision support | surfacing good; comparison/decision artifact missing | H |
| 17 | Research-mode differentiation (academic/web/purchase) | one pipeline, one output shape; mode-blind | H |

## I.3 The six Critical findings

- **C1 — Groundedness is never verified (AI-trust).** §9.1 validates a rigor band by the *tier* of an attached citation; nothing checks the cited episode's `content` supports the specific claim. This is "has a bibliography" vs. "is grounded," and it is the whole ballgame. A subtlety sharpens it: `WebFetch` output may already be a summariser paraphrase, so a stored snippet is not guaranteed verbatim; high-rigor claims need a second check against a re-fetched source span. *Fix: v2 §16 faithfulness gate.*
- **C2 — Runtime, concurrency, and storage model is undefined (SWE).** §3 says "one internal pipeline per request"; §9.4 justifies append-only by "concurrent research pipelines." Both can't be literal without an execution model. The real concurrency is the RSS cron, background vetting, and delegated specialists writing to shared stores — concurrent *writers*, not in-agent pipelines. Graphiti needs a backend graph DB (Neo4j/FalkorDB) never mentioned. Atomic-append, fold compaction, and idempotency are unaddressed. *Fix: v2 §19.*
- **C3 — Synthesis is unstructured and unguarded (AI-trust/SWE).** The pipeline structures scoring, sourcing, and reasoning, but the actual snippets-to-prose step has no structure, no attribution rule, no gate — the most hallucination-prone stage on a weak model. *Fix: v2 §16a.*
- **C4 — "Weighted synthesis" has no weighting function (research-methodology).** §5 asserts weighted synthesis but never defines the weights (tier? trust? recency? combination?). The core engine of a "trustworthy synthesis" system is a black box; two implementers build two systems. *Fix: v2 §5.1.*
- **C5 — Source independence / circular reporting is unhandled (methodology + security).** §9.2 counts `corroborates`, but ten sites echoing one press release is one source. This is both false confidence and a poisoning/Sybil vector: manufactured corroboration inflates confidence and astroturfed implicit signals inflate trust scores. *Fix: v2 §5.2 + §9.4.*
- **C6 — Local-model-portability is overstated; Graphiti write path is ambiguous (clarity/SWE).** Portability holds for bookkeeping (scoring, folds, validation, sanitization) but not for synthesis, the faithfulness check, or **Graphiti's own LLM-based entity/edge extraction**, which fires on every episode write. The §9.3 validation/repair layer governs the JSON the agent *emits*, not Graphiti's internal extraction — which is where the determinism problem actually lives. And it is unstated whether the agent hands Graphiti raw text or pre-structured payloads; that one choice changes cost, determinism, and whether §9.3 is even relevant. *Fix: v2 §2 (Principle 1 amended) + §9.2 write path + §21 model routing.*

## I.4 Prioritized punch-list

| ID | Finding | Sev | Type | v2 home |
|---|---|---|---|---|
| C1 | Groundedness/faithfulness never verified | C | must-fix | §16 |
| C2 | Runtime/concurrency/storage undefined | C | must-fix | §19 |
| C3 | Synthesis unstructured/unguarded | C | must-fix | §16a |
| C4 | Source-weighting function undefined | C | must-fix | §5.1 |
| C5 | Source independence / circular reporting | C | must-fix | §5.2, §9.4 |
| C6 | Portability overstated; Graphiti write path | C | must-fix | §2, §9.2, §21 |
| H-SWE-1 | Provisional vs. validated intent score conflated | H | must-fix | §4, §9.1 |
| H-SWE-2 | §9.3 stagnation error taxonomy missing | H | must-fix | §9.3 |
| H-SWE-3 | No injectable test seams (ToolClient/ModelClient) | H | must-fix | §12b, Part III |
| H-SWE-4 | Pipeline resilience/resumability unspecified | H | v1 | §19 |
| H-SEC-1 | No explicit threat model | H | must-fix | §15 |
| H-SEC-2 | Injection defense detection-based, not architectural | H | must-fix | §2 P7, §9.2a |
| H-SEC-3 | Delegated reports outside untrusted boundary | H | must-fix | §3, §9.2a |
| H-SEC-4 | SSRF scoped to SearXNG only | H | must-fix | §6a |
| H-SEC-5 | Outbound query/context egress leaks PII to 3rd parties | H | must-fix | §9.2b |
| H-SEC-6 | "Never deleted" vs. erasure/PII (policy decided) | H | must-fix | §9.9 |
| H-SEC-7 | Secrets management absent | H | must-fix | §6b |
| H-SEC-8 | Denial-of-wallet / no hard cost ceilings | H | must-fix | §19.6 |
| H-SEC-9 | Principal identity undefined; cron runs unbounded | H | must-fix | §8a |
| H-SEC-10 | MCP supply-chain trust | H | v1 | §6b, §15 |
| H-RES-1 | Academic mode thin (esp. retraction check) | H | v1 | §6 |
| H-RES-2 | Lateral reading / SIFT not systematized | H | v1 | §8 |
| H-RES-3 | Purchase/selection is second-class | H | v1 | §20 |
| H-RES-4 | Personalization can bias conclusions | H | must-fix | §9.8 |
| H-AI-1 | Trust-metric definitions + golden set | H | v1 | §18 |
| H-AI-2 | No abstention/calibration path | H | must-fix | §16b |
| M-RES-5 | Contestedness dimension missing | M | v1 | §4 |
| M-RES-6 | Stopping criteria cost-only (no saturation) | M | v1 | §6c |
| M-AI-3 | Reproducibility record thin | M | nice-to-have | §9.2 |
| M-SWE-5 | Query planning/expansion unspecified | M | v1 | §6c |
| M-OPS-1 | Observability, lifecycle, schema migration | M | v1 | §19.5 |
| M-TEST-1 | Extend single-source-of-truth to all schemas | M | v1 | §12b |
| M-AI-4 | Cost-unit (token) not call-count budgeting | M | v1 | §4 |
| M-UX-1 | Cold-start seeding (everything <2 seeds early) | M | v1 | §8 |
| M-BIAS-1 | Rich-get-richer / popularity / geographic bias | M | v1 | §5.3, §9.4, §18 |
| L-DRIFT | Numeric drift (§4 "20+" vs §9.1 "12"; count vs ids) | L | must-fix (done) | §4, §9.1 |
| L-AI-5 | Benchmark vs. existing research agents over time | L | nice-to-have | §18 |
| L-RES-7 | Add Scenarios D/E/F/G | L | v1 | §12a |

## I.5 Recommended v1 cut-line

All Criticals, all must-fix Highs, and (per the resolution of Part IV Q5) **all should-fix items** are in v1. §13 defers only the true nice-to-haves: automated *answer-quality* grading, the reproducibility record, cross-agent benchmarking, deeper tier taxonomy, the bespoke regulatory tool, ledger-visibility scaling, and the operational SSRF pentest.

---

# PART II — Revised v2 Spec (copy-ready)

> **Research Methodology Harness — Design Spec v2.1**
> Status: hardened for implementation planning. Adds faithfulness, weighting, independence, runtime/storage, security posture, mode-awareness, per-role model routing, and the Information Volatility Model. Supersedes the 2026-09-02 v1.

## 1. Purpose

A research harness that lets the user trust *how* an answer was researched, not just the answer. It infers research intent, plans and expands queries, selects source types, executes the right strategy (simple retrieval vs. multi-step agentic research), **synthesises claim-by-claim with verified attribution to sources**, weights sources by an explicit deterministic function, learns which sources to trust and reuse over time, and maintains full provenance to the URL for every claim. Two promises are load-bearing: **process auditability** and **answer faithfulness**. It also remembers *what it believed and decided on any past date*, and reuses durable knowledge it has already found instead of re-researching it.

Implementation-agnostic methodology first; a Claude Code plugin (skill + subagent + MCP wiring) is the first reference implementation.

## 2. Design Principles

1. **Portability is scoped and configurable per role.** Deterministic bookkeeping steps (intent scoring, folds, schema validation/repair, sanitization, source weighting, volatility classification) reduce to checklists a weak/local model executes correctly. The **generative** steps — synthesis, the faithfulness check (§16), and Graphiti's entity/edge extraction — need a more capable model. Rather than a fixed split, the system exposes a **five-role model router (§21)**: each role (`orchestration`, `scoring`, `synthesis`, `faithfulness`, `graph_extraction`) is independently assignable to a model. The initial deployment points all five at one cloud frontier model for testing; the local end-state reassigns per role across models sharing a 96 GB-VRAM host.
2. **Provenance *and* faithfulness over assertion.** Every claim of depth/rigor/personalization is backed by a checkable citation in the ledger, **and** every asserted claim is verified to be entailed by the source content it cites (§16).
3. **Surfacing over silent resolution.** Regulatory/theoretical constraints, newly-encountered sources, contested evidence, cost, and insufficient-evidence states are surfaced to the user even when the harness doesn't block on them.
4. **Extensible, not exhaustively pre-solved.** Tiers, domain-authority definitions, community hubs, and volatility classifications are seeded and grown via discovery-and-cache (or discovery-and-ask).
5. **Don't block on trust-building.** Using a new, unvetted source never stalls the current task; vetting runs in parallel and reports back.
6. **All externally-retrieved content is untrusted input, always** — search results, scraped pages, RSS items, MCP output (Slack/Reddit), **and delegated-specialist reports**. Data to reason about, never instructions to execute, never trusted-as-is before sanitization (§9.2a). Generalizes the Mem0 incident.
7. **Capability confinement.** Retrieved content may inform *what the agent believes*, never *what the agent does*. No tool-call target, MCP write, credibility-store event, `user-specified` bypass, blocklist change, or new fetch URL may originate from retrieved/parsed content or a delegated report. Fetch targets come only from search-result metadata that passed the egress guard (§6a) and, for new domains, the vetting path (§8). This is the primary defense against prompt injection; the §9.2a content scanner is measured defense-in-depth on top of it.

## 3. Architecture

A dedicated subagent — **`research-analyst`** — runs one pipeline per request:

```
Score intent (provisional) → plan (decompose, expand, choose search vs. agentic, delegate vs. own,
    CHECK trusted-source registry §5.3 for durable knowledge already held)
  → execute across source tiers, vetting new sources inline, applying the egress guard to every fetch
  → classify each source/claim by volatility (§5.3) → rerank by relevance
  → synthesise claim-by-claim → verify faithfulness (§16) → weight & resolve conflicts (§5)
  → re-check intent bands against evidence actually gathered (validated) → abstain or answer at flagged confidence
  → write ledger (Graphiti episodes) + append credibility/preference events + graduate durable knowledge
  → deliver answer (mode-appropriate shape) + compact source ledger + per-request cost (§19.6)
    + any pending vetting review requests
```

"Always-on" refers to the **harness** (RSS cron §11, background vetting §8, delegated specialists), which may write to shared stores concurrently with a live pipeline. These concurrent **writers** — not concurrent in-agent pipelines — are what the append-only model (§9.4) defends against.

Delegation follows the `salesforce-cloud-router` triage/dispatch/fold-back pattern, generalized: when a specialist persona is the better handler, `research-analyst` dispatches it and folds its findings into the same ledger and synthesis. **Delegated reports are untrusted content** (§2 P6): they pass the §9.2a gate, are constrained to structured non-instruction output, must carry URL-level citations at the same granularity as first-party episodes, and can never set the `user-specified` bypass (§8).

## 4. Intent Scoring — two-phase

Four+ dimensions, each scored via a fixed checklist mapped to bands (never a freeform float). Scoring happens in **two phases** to break the chicken-and-egg between "score sets the budget" and "score is validated by citations that only exist after research":

- **Provisional score** — computed *before* research from query text + memory. Drives the budget and plan. `intended_band` + `intended_basis`.
- **Validated score** — computed *after* research from the deduplicated ledger. What the answer reports; may be downgraded. `attested_band` + `attested_by` + `citation_ids`.

| Dimension | 0.0–0.2 | 0.3–0.5 | 0.6–0.8 | 0.9–1.0 |
|---|---|---|---|---|
| **Depth** | single fact, one source | 2–3 independent corroborating sources, single-hop | multi-hop, cross-tier synthesis | exhaustive, many sub-questions, report-length |
| **Rigor** | opinion/casual | factual, low stakes | safety/compliance/financial — must ground in authoritative tier | claims must trace to a primary/peer-reviewed source for this domain |
| **Recency** | timeless | slow-changing (annual/seasonal) | fast-changing (weekly/monthly) | breaking, hours-fresh |
| **Personalization** | fully generic | context helpful | requires a known preference | requires explicit preference-gathering to answer |
| **Contestedness** | settled fact | mild disagreement | actively debated | no consensus / value-laden |

Recency (a property of the *query's* freshness need) is distinct from `volatility_class` (§5.3, a property of the *source/claim's* rate of change); both are recorded. Contestedness selects the synthesis rule: settled → force consensus; contested → represent multiple positions with citations, avoid false balance (keyed off `contradicts` density in §9.2).

A fixed rule derives from the **provisional** score:
- a **budget** denominated in **cost units** (estimated tokens + tool-call count + wall-clock), not raw call count alone. Example bands: quick-lookup ≈ 1–2 calls / low token ceiling; deep-research ≈ 20+ calls / high ceiling. Soft budget may be exceeded while making clear progress (flag at 1.5× soft, hard-stop at the §19.6 hard ceiling). Reuse of durable knowledge (§5.3) reduces the budget actually spent.
- a **breadth/depth pair** for the agentic loop (§6c), not a single scalar.
- a **derived label** (`quick-lookup`, `deep-research`, `academic`, `purchase-decision`, `planning`) attached after scoring, used to select the **output shape** (§20) and for debugging.

Intent-score block logged and shown by default in v1.

## 5. Source Tiers, Weighting, Independence & Volatility

Tiers are extensible, seeded with *theoretical/scientific*, *regulatory/standards*, *empirical/community*. Deeper taxonomy deferred (§13).

**§5.1 Source weight (deterministic).** Synthesis weight = `tier_base_weight × trust_score_at_use × recency_fit × independence_factor`, where `tier_base_weight` is a documented per-tier constant in the §12b single-source-of-truth file, `recency_fit ∈ {0.5, 1.0}` from the recency band vs. the source date, and `independence_factor` from §5.2. Regulatory/theoretical constraints are **always surfaced** regardless of weight. Weights and the resulting ranking are logged so synthesis is auditable and reproducible.

**§5.2 Independence.** Before counting corroboration or crediting an implicit trust signal, cluster sources by shared registrable domain, shared author/byline, near-duplicate content (minhash or embedding cosine over `content`), and shared cited-primary-source. **Corroboration counts independent clusters, not raw source count.** Implicit trust-signal gain (§9.4) is capped per cluster and per time window; a domain may not cross the high-confidence bar on implicit signals alone. Detected circular-citation rings emit a penalty event.

**§5.3 Information Volatility Model (drives both retention and trust).** Every source/claim is tagged at ingestion with a `volatility_class` — the rate of change of the *underlying* information — which parameterizes retention (§9.9) and the credibility-fold constants (§9.4). Combined with an orthogonal `authority_class` (source standing, derived from the trust score + `domain_authority_profile` §9.5), it forms a **class-keyed policy table** rather than global scalars:

| `volatility_class` | Examples | Decay half-life | Staleness threshold | Min-evidence (independent clusters §5.2) | Retention (§9.9) |
|---|---|---|---|---|---|
| `durable` | laws of physics, math, canonical textbooks, ISO/ASTM standards | ∞ (none) | ∞ (none) | 1 authoritative source may suffice | source + claim retained permanently; graduates to durable knowledge |
| `slow` | medical consensus (Mayo, AMA), regulatory codes, DSM-driven diagnoses | ~3 years | tied to revision cycle (new edition/guideline) | 2–3, authority-weighted | long; re-verify on revision-cycle events |
| `moderate` | tech best-practice, product categories, methods | 180 d *(baseline default)* | 90 d *(baseline default)* | ≥4 incl. ≥1 explicit *(baseline default)* | claim + provenance retained; raw content aged out |
| `fast` | news, prices, availability, fashion trends | 30–90 d | weeks | **high bar for news** — multiple *independent* reputable outlets (anti-fake-news) | episodic record + provenance retained; volatile value NOT promoted to a durable fact |
| `ephemeral` | today's price/weather, one-off transactional facts | n/a | n/a | n/a | store only "on date X we consulted S and reported R"; never persist the value as a durable fact |

`authority_class` scales the row: a high-authority source (Mayo Clinic on a `slow` claim, a university-standard textbook on a `durable` claim) gets a longer effective half-life and clears min-evidence with fewer independent clusters; a blog/influencer gets a shorter half-life and needs more corroboration. The recommended fold defaults (§9.4) seed the `moderate` row; other rows scale from it. Classification is a `scoring`-role checklist judgment seeded with a topic→class map (physics/math/standards→`durable`; medical-consensus/regulatory→`slow`; news/prices/trends→`fast`; transactional→`ephemeral`). Class boundaries and the seed map are tunable config in the §12b file.

**Durable-knowledge reuse.** `durable`/`slow` sources that clear the evidence bar graduate into a **trusted-source registry** (a view over the credibility store + ledger, keyed by topic). The planner (§6c) checks this registry *before* exhaustive search; for a durable topic with a known authoritative source, it reuses that source instead of re-researching — cheaper (fewer tool calls/$) and consistent. This is the "I already hold the fluid-dynamics textbook; physics hasn't changed; go there first" behavior.

**News / anti-fake-news.** For `fast`-class news claims, min-evidence requires multiple *independent* reputable outlets (clustered per §5.2), explicitly to resist fake news and single-source amplification.

**Conflict resolution:** weighted synthesis (§5.1). Regulatory/theoretical constraints are always surfaced even when synthesis doesn't treat them as an absolute floor. Worked stress cases (unchanged from v1): regulatory-vs-preference is disclosed and never silently overridden either way; a blocklisted highest-rigor source downgrades the reported band with a stated reason rather than fabricating compliance.

## 6. Tool Layer

Provider-agnostic where possible, MCP-wrappable where an MCP exists. (Table condensed; v1 content preserved.)

| Category | Tools | Notes |
|---|---|---|
| General web search | Tavily (primary) + self-hosted **SearXNG** (fallback) | All fetches subject to §6a egress guard. |
| Academic/theoretical | Semantic Scholar (MCP), arXiv API, OpenAlex API | arXiv = pre-print, flagged non-peer-reviewed. See academic workflow below. |
| Regulatory/standards | **Confirmed unsolved gap;** general search scoped to `.gov`/municipal/standards allowlists | Financial-regulatory APIs (FRED, Census, FINRA, FDIC, ESMA) are a narrow financial sub-tier only. Bespoke regulatory tool deferred (§13). |
| Empirical/community | Reddit MCP (`reddit-mcp-server`), Stack Exchange API, Slack MCP (`slack-mcp-server`), Discord (low confidence), Apify + **`community_hub_map`** (§9.6) | Mainstream defaults are wrong for many niches; the map makes "authoritative platform for this topic" a learned lookup. |
| Deep/agentic research | Perplexity Sonar Deep Research, Exa deep search, + internally-encoded loop (§6c) | Frameworks (LangGraph/CrewAI/Agent SDK/Pydantic AI) evaluated and rejected. |
| Fast-moving/current | General search + recency filters + first-party **RSS** (§11) | No dedicated news API beat search + recency + cross-check. |

Fact-check note (preserved): "Regulatory Compliance Search API" and "Reuters Business/Financial News MCP" are hallucinated and excluded; use `reddit-mcp-server` and the raw OpenAlex API.

**Academic-mode workflow additions (in v1).** For rigor-0.6+ academic claims: (a) **retraction gate** — check Retraction Watch / Crossref retraction notices; a retracted source is a hard exclusion with a surfaced note; (b) primary/secondary/tertiary discrimination; (c) forward+backward citation snowballing for depth; (d) an evidence-hierarchy weight for empirical claims (systematic review/meta-analysis > RCT > cohort > case-control > case report > expert opinion, with domain analogues in §9.5); (e) `domain_authority_profile` may declare that for a fast-moving domain the preprint/lab report *is* the primary source, so rigor isn't perpetually downgraded on exactly the domains that move fastest.

**§6a — Central egress guard (required, day one, ALL local fetchers: SearXNG, scraper, deep-research fetches, RSS poller).** For each outbound fetch: allow only `http`/`https`; resolve DNS and validate the **resolved** IP against a denylist of all private, reserved, loopback, link-local, ULA, IPv4-mapped-IPv6 (`::ffff:a.b.c.d`), and cloud-metadata ranges (IPv4 `169.254.169.254`, IPv6 `fd00:ec2::254`, `metadata.google.internal`) for IPv4 and IPv6; connect to the validated IP with Host/SNI pinned (no re-resolution — defeats DNS rebinding); re-validate **every** redirect hop; reject alternate IP encodings (decimal/octal/hex) and non-HTTP schemes (`file`/`gopher`/`dict`); cap redirects, timeouts, and response size. Run SearXNG and any local fetcher in a network context with no route to internal ranges or the metadata endpoint. §13 defers only the operational pentest, not these design controls.

**§6b — Secrets & dependency posture (required).** All API keys and DB credentials (Neo4j auth, tool API keys) live in a secret store / env only, never in code, logs, the ledger, the memory mirror, the audit store, or error traces; secret-shaped strings are redacted from all logs (with a CI lint that fails the build if a key-shaped string can reach an episode or log). MCP servers and other dependencies are version/hash-pinned, least-privilege-scoped, their privileges documented, and their output treated as untrusted (§2 P6).

**§6c — Deep-research loop mechanics (required).**
0. **Reuse check (new).** Before searching, query the trusted-source registry (§5.3) for durable knowledge already held on the topic; for `durable`/`slow` topics with a known authoritative source above the trust bar, reuse it and skip or narrow the search.
1. **Decompose** into an explicit list of sub-questions (target 3–8, scaling with intended depth), each tagged with the perspective/tier it needs (perspective-guided decomposition, per STORM; planner/executor split, per gpt-researcher).
2. **Breadth vs. depth (2-D budget):** `breadth` = number of sub-questions pursued (optionally in parallel), `depth` = max recursive follow-up hops per sub-question. Derived from intent bands, not a single call count.
3. **Reflect / gap-detect (explicit trigger):** after each round, per sub-question compute (a) answered by ≥1 entailed, sufficiently-trusted source? (b) did this round surface any *new* independent source/entity? Iterate a sub-question only if (a) is false; retire it if (a) true or (b) false two rounds running (patterns: Self-RAG, FLARE, Reflexion, ReAct).
4. **Terminate on saturation OR budget:** stop when all sub-questions are retired (coverage), or no new independent source appeared in a full round (saturation), or the cost budget is reached — whichever first; flag which fired. A minimum-evidence floor (§5.3, by class) applies so cheap ≠ under-evidenced.
5. **Coverage report:** the answer includes a sub-question × answered? matrix.

## 7. Sequential Thinking Integration

Official `Sequential Thinking MCP` used during the deep-research stage, gated by the soft budget. Externalizes the loop into numbered, revisable, branchable thought steps folded into the ledger. Adds **structure and auditability**, not reasoning capability. Sequential-Thinking steps that quote retrieved content are sanitized (§9.2a) before being folded. (Reconsider vs. logging the model's own plan/reflect steps directly as episodes — the MCP is an extra nondeterministic dependency; keep only if the branchable-thought auditability earns its keep.)

## 8. New-Source Vetting Gate

**Trigger, bypass integrity, baseline discovery, legitimacy signals, non-blocking flow** — preserved from v1 (user-named sources seed with `basis: user-specified`; bypass only from the live principal; confirm/reject/blocklist with rerun-on-reject). Additions:

**§8 lateral reading (in v1).** The v1 site-quality checklist is *vertical* reading (judging a site by its own content — the weaker method). Add **lateral reading / SIFT** (Stop, Investigate the source, Find better coverage, Trace claims): leave the page and check what independent sources say *about* the source, and trace each claim to its original source before citing. Checklist-able, portable, and it strengthens both credibility and injection-resistance.

**§8 implicit-signal cap (C5).** Implicit corroboration credited only per §5.2 independence clustering; capped per cluster/time-window; can never auto-blocklist.

**§8 cold-start seeding (in v1).** Early on, every category has <2 seeds. Ship a substantial seed set for `community_hub_map`, `domain_authority_profile`, `consumer_protection_registry_map`, and the §5.3 volatility topic→class map (AU/NZ/US at minimum, given the primary user's locale), and prefer infer-then-confirm-asynchronously over blocking asks once seeds exist.

**§8a — Principal model (required).** "Principal input" = content on the direct user↔agent turn only — never a tool result, subagent report, retrieved page, or Cron trigger. Trust-elevating, preference-writing, `user-specified` bypass, and blocklist actions require principal-channel provenance. Cron/RSS runs (§11) and delegated specialists have **no principal** and may only append triage/summary/finding episodes; they may not elevate trust, write preferences, set bypasses, or change blocklists.

## 9. Data Schemas

### 9.1 Intent Score (two-phase; drift fixed)
```json
{
  "session_id": "...", "timestamp": "...", "schema_version": 2,
  "dimensions": {
    "depth": {
      "intended_band": "0.6-0.8", "intended_basis": "cross-source comparison + 3 sub-questions detected",
      "attested_band": "0.6-0.8", "attested_by": "independent_clusters>=4 across >=2 tiers after dedup",
      "citation_ids": ["ep_1","ep_2","ep_3","ep_4"]
    },
    "rigor": {"intended_band":"0.9-1.0","attested_band":"0.9-1.0","attested_by":"matches_domain_authority","domain":"plumbing","citation_ids":["ep_3"]},
    "recency": {"intended_band":"0.3-0.5","attested_band":"0.3-0.5","attested_by":"source_date_within_seasonal_window","date_reliable":true},
    "personalization": {"intended_band":"0.6-0.8","attested_band":"0.6-0.8","attested_by":"memory_citations","memory_citations":["pref_electrical_hookup","pref_near_ocean"]},
    "contestedness": {"intended_band":"0.0-0.2","attested_band":"0.0-0.2","attested_by":"contradicts_density<0.1"}
  },
  "derived_label": "deep-research",
  "budget": {"soft_max_calls": 20, "soft_token_ceiling": 120000, "breadth": 5, "depth": 2, "actual_calls": 9, "actual_tokens": 61000},
  "reuse": {"durable_sources_reused": ["src_fluid_dynamics_textbook"], "calls_saved_estimate": 6}
}
```
Budget derives from `intended_*` only. `attested_*` computed post-research from the deduplicated ledger; may be lower. `date_reliable:false` when a source has no trustworthy publish date. Canonical numbers: deep-research soft budget ≈ 20 calls.

### 9.2a Sanitization & Redaction Gate (required, upstream of every episode write AND upstream of Graphiti extraction, delegated reports, Sequential-Thinking inputs, and RSS titles)
Detection is **layered and stated**, not a single regex: (1) normalization/decoding pass (unescape, strip zero-width/homoglyph, decode base64/HTML-comment/CSS-hidden spans); (2) deterministic rules for known patterns and encodings; (3) an injection-resistant judge (the `scoring` role) that receives content inside a data-only frame it cannot be steered by. The gate:
1. **Injection handling** — flags instruction-like spans (imperative *and* declarative source-steering, multilingual, reported-speech) as `injection_flagged:true`, excludes them from citable fact content, logs the excluded span separately for audit, never executes. Defense-in-depth; the *primary* control is capability confinement (§2 P7). False-positive/false-negative rates measured on a held-out + adversarial set (§13a).
2. **PII redaction — content-based across all tiers** (not tool-scoped): scans all content for names outside public-figure context, emails, phones, addresses, private handles; masks before commit. Because redaction happens at the gate, retained `supporting_span`s are already PII-free.

### 9.2b Outbound egress gate (required, symmetric to 9.2a)
Before any query or context leaves to a third-party tool/MCP (Tavily, Perplexity, Exa, Apify, Reddit, Slack), strip or mask user PII and sensitive context unless the user has consented for that tool. Per-tool policy declares which context classes may egress; empirical/community and Slack-sourced content default to **no-egress**.

### 9.2 Session Ledger — Graphiti Episodes (write path = pre-structured payloads)
Built on **Graphiti** (temporal knowledge graph) from day one, backed by **Neo4j Community Edition** (§19.2). **Write path:** `research-analyst` submits **pre-structured** episode payloads (entities + `relation_hints`) to Graphiti; Graphiti performs resolution/dedup against the existing graph using the `graph_extraction` model role (§21). The §9.3 validation/repair layer governs the emitted payload. Episode schema (adds volatility/authority, `supporting_span`, `data_class`, `schema_version`):
```json
{
  "episode_id":"...","session_id":"...","timestamp":"...","schema_version":2,
  "episode_type":"source_citation",
  "data_class":"raw_content",
  "content":"raw sanitized snippet/quote",
  "supporting_span":"verbatim PII-redacted span used to ground a claim (§16)",
  "volatility_class":"durable","authority_class":"canonical_textbook",
  "source_metadata":{"url":"...","title":"...","tier":"theoretical","community_hub":null,
    "domain_authority_match":true,"trust_score_at_use":0.82,"retrieved_at":"...","content_is_verbatim":false},
  "entities_mentioned":["1/2-inch NPT fitting","Uniform Plumbing Code §605"],
  "topic_tags":["plumbing","pipe-fitting","building-code"],
  "relation_hints":[{"subject":"1/2-inch NPT fitting","predicate":"complies_with","object":"UPC §605"}],
  "independence_cluster_id":"clu_7",
  "corroborates":["ep_x"],"contradicts":[],
  "memory_citations":["pref_electrical_hookup"],
  "valid_at":"...","invalid_at":null
}
```
`valid_at`/`invalid_at` give bi-temporal semantics — the basis for point-in-time belief reconstruction (§9.9) — subject to §9.9 hard-delete for erasure. Reproducibility record (M-AI-3, nice-to-have): optionally log tool queries + raw results + model+version.

### 9.3 Output-Validation/Repair Layer (error taxonomy)
`validate_graph_write(payload, schema)` before every commit. Bounded retry (max 3) feeds the exact failing field/rule back, with **stagnation detection** on a defined error taxonomy — enum: `MISSING_REQUIRED_FIELD(field)`, `WRONG_TYPE(field)`, `ENUM_VIOLATION(field)`, `EXTRA_FIELD`, `MALFORMED_JSON`, `CONSTRAINT_VIOLATION(rule)`. Two attempts are "same category" iff equal code **and** locus (field/rule); on repeat, short-circuit to `write_failures` immediately. Persistent failures logged, never silently dropped or retried indefinitely.

### 9.4 Credibility Store (SQLite append-only; class-keyed folds; independence + idempotency)
Append-only table in **SQLite (WAL)** (§19.2); current state computed by a deterministic **fold** over all events per `domain+topic` key at read time. Event schema carries `event_id` (stable, `UNIQUE`), `schema_version`, and the `volatility_class`/`authority_class` of the evidence. **Fold constants are a class-keyed policy table (§5.3), not global scalars:**
- **decay half-life**, **staleness threshold**, and **min_evidence_for_high_confidence** are looked up by `(volatility_class, authority_class)`; the `moderate` row seeds the recommended defaults (180 d / 90 d / ≥4 clusters incl. ≥1 explicit); `durable` → ∞/∞/1-authoritative; `fast`-news → short/short/high-bar.
- explicit feedback weighted **3× implicit** (tunable); **implicit signals independence-capped (§5.2)** and unable alone to cross into high-confidence; below the class bar the score reports `provisional`.
- a `blocklist` event overrides any score permanently (reversible only by an explicit new event).
- **Idempotency:** folds dedupe by `event_id` (`INSERT OR IGNORE`), so a retried append never double-counts.

The **trusted-source registry** (§5.3) is a query over this store filtered to `volatility_class ∈ {durable, slow}` with trust ≥ bar and evidence ≥ class-min. Plugin-owned; mirrored into global memory as **folded summaries only** (no raw topic detail — topic keys can reveal health/finance/legal interests; see §9.9).

### 9.5 `domain_authority_profile` (extensible, seeded)
`{domain, primary_source_definition, examples, preprint_is_primary?, authority_class}` — defines "primary/peer-reviewed" per domain and supplies the `authority_class` that scales the §5.3 policy table. Rigor 0.9–1.0 valid only if a cited source's tier matches. `preprint_is_primary?` lets fast-moving domains treat a preprint/lab report as primary.

### 9.6 `community_hub_map` (flat, permanent) / 9.7 `consumer_protection_registry_map` (extensible, seeded)
Flat SQLite tables (append-only/fold, discovery-and-cache). AU/NZ/US seeded (§8 cold-start).

### 9.8 Personalization Preference Memory — graph-native (bias guard)
`Preference` node → `applies_when` edge to context-tag node(s), each edge carrying `valid_at`/`recheck_after`; staleness sets `invalid_at` and triggers a re-ask; reinforcement creates a fresh edge. **Bias guard:** personalization may shape *relevance, framing, and which options surface* but must never alter *evidential weighting* or suppress contradicting evidence. On truth-vs-preference conflict, surface both. High-rigor factual conclusions are preference-invariant.

### 9.9 Retention, Erasure & Encryption — volatility-tiered
**Why the mechanism is decided day-one (not just numbers):** the system is architected around immutability and never-forgetting — trust is *derived* by folding over full history, and Graphiti *supersedes* rather than deletes. Retrofitting deletion later means rewriting the fold to tolerate gaps, recomputing all snapshots, chasing PII copies across the mirror + snapshots + backups, and retroactively re-classifying data — a lossy cross-cutting migration. So three things are non-negotiable from the first write: every record carries a `data_class` tag; a **tombstone-and-purge hard-delete path** exists distinct from `valid_at`/`invalid_at`; and the graph, the SQLite stores, the memory mirror, and the audit store are **encrypted at rest**. SQLite (§19.2) makes the flat-store purge trivial. With these in place, the actual TTLs are pure config.

**Volume context (why retention is about signal, not space):** at an aggressive ~100 source-episodes/day, maximum-audit retention (raw snippet + embeddings + graph) is ~30 KB/episode ≈ ~1 GB/year ≈ **~33 GB over 30 years** (~110 GB worst-case if full raw pages are stored). Storage is a non-constraint; intelligent retention exists for **recall correctness** (a stale price stored as a durable belief misleads), **retrieval quality** (a graph clogged with ephemera retrieves worse), and **embedding cost** — not disk.

**Retention is therefore driven by `volatility_class` (§5.3):**
- **Episodic record — always retained (indefinitely).** "On date X, for query Y, we consulted sources S and concluded/decided R." Tiny, and it is the core memory value. Stores conclusions + provenance pointers (URL, title, `retrieved_at`, `trust_score_at_use`), NOT raw page copies.
- **`durable`/`slow` knowledge — retained long/permanently.** The source + claim graduate into durable knowledge and the trusted-source registry (§5.3), reused not re-researched.
- **`fast`/`ephemeral` values — provenance kept, value not promoted.** Record "we saw $X at store Y on date Z" as a point-in-time observation; never persist it as a durable fact. Raw content aged out on the `moderate` default (90 d) or faster by class; retained `supporting_span`s are already PII-free (§9.2a).
- **Injection-flagged span audit store** — 180 d, access-controlled, human/deterministic-read-only, never re-fed to a model.
- **User-requested erasure / gate-missed PII** — immediate tombstone-purge across ledger + SQLite + mirror + snapshots.

**Point-in-time belief reconstruction:** Graphiti's bi-temporal semantics make "what did we believe / discuss / decide on date X" a first-class supported query, distinct from current belief.

## 10. Adaptive Learning Summary
Learned over time under the §9.4/§5.3 rules: **source credibility** (per-topic, class-keyed, independence-capped, explicit>implicit), **durable knowledge** (graduated authoritative sources, reused), and **user preferences** (context-scoped, staleness-aware, bias-guarded). Guard against rich-get-richer/popularity/geographic bias via §5.2 independence, class-keyed decay, and the §18 regression eval on a frozen gold set.

## 11. RSS / Current-Events Subscription
First-party feed registry polled via `CronCreate`. Two-stage triage: cheap title-only relevance pass (log every item), then full-content summarization only on pass. **All feed fetches pass §6a egress guard; titles pass §9.2a before triage.** Cron runs are principal-less (§8a) and append-only. RSS-sourced current events are `fast`-class (§5.3). No third-party aggregator.

## 12. Testing Strategy — three layers

**12a. Scenario-level behavioral evaluation (manual for now).** Scenarios A (plumbing/building-code), B (30-day NZ caravan trip), C (fast-moving current events), **D** (academic literature synthesis with a retraction-prone/contested claim), **E** (head-to-head product selection with fake-review risk), **F** (controversial topic — multi-position surfacing / false-balance avoidance), **G** (durability & memory: ask a `durable` question e.g. fluid dynamics, then re-ask two simulated years later and assert durable-source reuse with no re-search; then query "what did we believe on date X" and assert correct point-in-time reconstruction). Scored against a rubric (source diversity, tier coverage, citation validity §9.1, **faithfulness §16**, conflict-surfacing, vetting behavior, volatility classification, reuse). Automated *answer-quality* grading deferred (§13); metric *definitions* and the golden set are in v1 (§18).

**12b. Schema/unit-level testing and linting (day one).** Unit tests (valid + invalid) for every validator; **checklist linting** from one shared source-of-truth (intent rubric, all schemas, §5.1 tier weights, §5.3 volatility policy table, §9.4 fold constants) with a CI drift check; concurrent-append + idempotency tests for the folds; stagnation-detection tests (§9.3 taxonomy); sanitization/redaction tests (known injection incl. Mem0 + known PII). **Injectable test seams:** every tool and model call sits behind a mockable `ToolClient`/`ModelClient` (role-aware, §21) so each component is unit-testable with fakes, fixtures, and golden transcripts.

**§13a Security test suite (day one).** Abuse-case fixtures per §15 threat: poisoned-fact corpus (declarative, no imperative), encoded/multilingual/zero-width injection corpus, SSRF payload set (rebinding, redirect-to-internal, IPv6, alternate encodings, metadata), Sybil-corroboration graph, principal-spoofing-via-retrieved-content, outbound-PII-leak cases — each asserting the control blocks before any episode write or egress.

## 13. Non-Goals / Explicitly Deferred
Definitive tier taxonomy beyond three seeds; bespoke regulatory-data tool; ledger-visibility scaling + hidden intent score; **automated answer-quality grading** (metric definitions and golden set are in v1 — §18); operational SSRF pentest of SearXNG (the §6a design controls are in v1); reproducibility record (M-AI-3) and cross-agent benchmarking (L-AI-5). All other should-fix items are in v1.

## 14. Naming
The dedicated persona is **`research-analyst`**.

## 15. Threat Model
Assets: answer integrity, credibility store, durable-knowledge registry, user PII/preferences, internal network/cloud credentials, Neo4j + API keys, cost budget. Trust boundaries: principal channel (trusted) | retrieved content, MCP output, delegated reports, cron (untrusted). Adversaries: SEO-spam/astroturf, targeted injector, Sybil corroborator, fake-news amplifier, malicious/compromised MCP, curious cross-project reader. STRIDE table maps each to the control that blocks it (§2 P7, §5.2, §5.3 news bar, §6a, §6b, §8a, §9.2a, §9.2b, §9.9, §19.6) and marks each control load-bearing vs. optional.

## 16. Synthesis & Faithfulness
**§16 Faithfulness gate (required).** Before delivery, the answer is decomposed into atomic claims. Each claim carries ≥1 `citation_id` **and** a verbatim `supporting_span` from that episode's sanitized `content`. A deterministic per-claim checklist (run by the `faithfulness` role §21): (a) does `supporting_span` come unaltered from the cited episode? (b) does the span state, or directly and non-speculatively entail, the claim? (c) is the claim free of specifics (numbers/names/dates) not present in some cited span? Fail → re-ground, weaken to what spans support, or drop. For rigor 0.9–1.0, a second check verifies the stored snippet is itself entailed by a freshly re-fetched source span (because `WebFetch` output may be a paraphrase). Per-claim result logged as a `faithfulness_check` episode; the answer reports a **faithfulness score** = fraction of claims entailed. Weak-model-portable: span-copy + a 3-question checklist.

**§16a Synthesis discipline (required).** Claim-by-claim, not free-text. **No citation → no claim.** Connective/structural prose may not introduce new factual specifics. Contradictory evidence cites both sides (§5, keyed off contestedness §4). Synthesis (the `synthesis` role §21) emits a structured `answer` = list of `{claim, citation_ids, supporting_spans, confidence}`; the renderer flattens it for the user and the ledger stores it verbatim.

**§16b Abstention / calibration (required).** If no claim clears §16 at the query's required rigor band, the harness abstains or answers at flagged low confidence rather than fabricate. Answer-level confidence is derived from the evidence gathered (independent-cluster count, faithfulness score, tier match, volatility/authority).

## 17. (reserved — weighting/independence/volatility live in §5.1/§5.2/§5.3)

## 18. Evaluation Metrics & Golden Set (definitions in v1)
Named metrics (automated grading deferred): **faithfulness**, answer-relevance, context precision/recall (RAGAS-style), citation accuracy (ALCE-style), atomic-fact precision (FActScore-style), coverage, conflict-surfacing correctness, **intent-band inter-rater reliability** (Krippendorff's α across repeated runs and across frontier + local model), **durable-source reuse rate** and **recall-correctness over time** (does re-asking a durable question reuse the known source; does a stale value ever get served as current). Versioned golden set with expected-source fixtures per scenario (A–G). Distinguish "was the *process* sound" (auditable from the ledger, automatable now) from "is the *answer* correct" (needs ground truth, manual). LLM-as-judge design when switched on: rubric, judge ≠ generator, bias controls, human spot-check. A frozen gold set also detects credibility-store drift. Name target numbers (faithfulness rate, recall@k, α, latency p50/p99, cost per deep-research run) — TBD but named.

## 19. Runtime, Storage & Concurrency
- **19.1 Process model.** `research-analyst` runs as an **ephemeral pipeline per request**. "Always-on" = the harness (RSS cron, background vetting, delegated specialists) — the real concurrent **writers**.
- **19.2 Storage (decided).** Ledger + preference graph in **Graphiti backed by Neo4j Community Edition** (reference/best-supported Graphiti backend, mature graph-visualization tooling that serves the auditability thesis, user-familiar; footprint lands on system RAM not the 96 GB VRAM the models contend for). The Layer-1 `Ledger` interface keeps FalkorDB/Kuzu a swap-in if footprint ever bites. All flat event logs (§9.4/§9.6/§9.7, RSS log, `write_failures`) in **SQLite (WAL mode)** — ACID kills torn-write corruption (no `PIPE_BUF` problem), `UNIQUE(event_id)` gives idempotency, indexed folds beat file scans, single-file `0600` + at-rest encryption, and `DELETE`/`UPDATE` make the §9.9 purge path trivial; kept append-only by discipline (inserts only, except the erasure path). Every record carries `schema_version` + stable `event_id`.
- **19.3 Fold performance.** Each fold key keeps a periodic snapshot (folded state + last-folded `event_id`) as a SQLite table; reads fold snapshot + tail only. Compaction on a row-count/time trigger.
- **19.4 Idempotency.** Folds dedupe by `event_id`; appends safe to retry.
- **19.5 Observability & lifecycle.** `write_failures` queue monitored/alerted with a drain policy; budget/cost telemetry (§19.6) surfaced; metrics/tracing; SearXNG self-host ops; schema versioning/migration for the append logs (fold-time compat rules).
- **19.6 Cost ceilings, transparency & resilience (decided).**
  - **Per-request cost is part of the standard output** in early phases: every run appends that search's cost (per-role tokens × model price + per-tool API cost) to the answer, surfaced like the new-source-review prompt. Per-role token accounting + per-tool cost tags are built in day one. A config flag later demotes cost from the answer into logs/dashboards.
  - **Hard $10/day hold:** a running daily-cost meter; on reaching **$10/day** it fires an **immediate notification** and **stops all further searches** until the user personally resets it after review. A hard gate, not a throttle — distinct from the §4 soft per-request budget. Also enforce per-request `hard_max_calls`, `max_wall_clock`, `max_cost` + circuit breaker; on breach return a partial answer explicitly labeled budget-truncated.
  - **Resilience:** per-tool retry/backoff + fallback (Tavily→SearXNG); partial-failure policy (research done + synthesis failed = deliver degraded with a flag, don't lose the ledger); sessions replayable from their ledger.

## 20. Decision-Support / Comparison Mode (in v1)
When `derived_label = purchase-decision`/selection, the output shape is a decision artifact: (a) **criteria elicitation**; (b) **option enumeration**; (c) a **comparison matrix** (options × criteria, each cell sourced per §16); (d) total-cost/availability; (e) **fake-review detection** (astroturf clustering via §5.2); (f) a **recommendation with rationale** tied to the weighted criteria. Prices/availability are `fast`/`ephemeral` (§5.3) — surfaced with their observation date, not stored as durable facts. Academic-mode output is a lit-review with a citation graph; quick-lookup is a direct answer. Output shape branches on the derived label (§4).

## 21. Model Routing & Role Assignment (new)
Five independently-configurable model roles, so the split-model boundary is a config decision optimizable later, not baked into code:

```yaml
model_roles:
  orchestration:    { provider, model_id, endpoint, max_tokens, temperature }  # planning, tool selection, loop control
  scoring:          { ... }   # intent scoring, folds, checklist eval, sanitization judge, volatility classification
  synthesis:        { ... }   # claim-by-claim answer generation (§16a)
  faithfulness:     { ... }   # entailment checklist over spans (§16)
  graph_extraction: { ... }   # Graphiti's internal entity/edge extraction (configured via Graphiti's LLM client)
```
**Default now:** all five point at one cloud frontier model for initial testing and analysis. **Later:** reassign per role across models sharing the 96 GB-VRAM host — e.g., a small always-loaded local model for `orchestration`/`scoring`/`faithfulness` (checklist-shaped, portable), a larger local model for `synthesis`/`graph_extraction`. `graph_extraction` routes through Graphiti's own configurable LLM client so its internal calls are not a hidden fixed dependency. The Layer-3 `ModelClient` exposes `ModelClient.for(role)`; every judgment component receives its client by role injection, so a role can be re-pointed or mocked without touching component code.

---

# PART III — Implementation Decomposition for Subagent-Driven TDD

Build strictly **bottom-up** — every layer is testable with fakes for the layer above. Layers 0–1 are deterministic (cleanest, cheapest TDD); Layers 2–3 become testable only because Layer 0 schemas and the injected role-aware `ToolClient`/`ModelClient` fakes isolate them.

**Layer 0 — pure, deterministic, no external deps (build first):**
- `constants/schema` single source of truth (§12b: all schemas, §5.1 tier weights, **§5.3 volatility policy table**, §9.4 fold constants) — imported by everything.
- All JSON-schema validators (§9.1–§9.9). Contract: `validate(payload) → {ok, errors[]}`.
- Sanitization/redaction gate deterministic layers (§9.2a). Contract: `sanitize(content) → {clean, flags, excluded_spans}`.
- Source weight + independence functions (§5.1/§5.2). `weight(source, ctx) → float`; `cluster(sources) → clusters[]`.
- **Volatility policy lookup (§5.3):** `policy(volatility_class, authority_class) → {half_life, staleness, min_evidence, retention}` — pure table lookup.
- Fold functions (§9.4): class-keyed decay + staleness + min-evidence + blocklist-override + idempotency (`event_id` dedup). `fold(events, policy) → state`.
- Validation/repair + error taxonomy + stagnation (§9.3). `repair(payload, schema, attempts) → {payload|write_failure}`.
- Faithfulness checklist deterministic part (§16): `check(claim, spans) → {a,b,c, verdict}`.

**Layer 1 — storage adapters behind interfaces (§19 decided):**
- `EventLog` = **SQLite (WAL)** adapter: atomic append, `UNIQUE(event_id)`, snapshot/compaction, `0600` + encryption, tombstone-purge. Credibility store, flat maps, RSS log, `write_failures` over it.
- **Trusted-source registry** = query/view over the credibility store + ledger (§5.3).
- `Ledger` = **Neo4j-backed Graphiti** writer behind an interface with an in-memory fake; pre-structured payload write path; bi-temporal query incl. point-in-time reconstruction (§9.9).
- Preference memory (§9.8).

**Layer 2 — tool executors behind a mockable `ToolClient` (all mocked in tests):**
- Central egress guard wrapper (§6a) — wraps every fetch. Outbound egress gate (§9.2b).
- Per-tier executors: web, academic (incl. retraction gate), community, regulatory-scoped-search, news/recency, RSS poller + two-stage triage (§11).
- Deep/agentic loop (§6c) incl. the reuse check (step 0) + Sequential Thinking (§7).

**Layer 3 — LLM-judgment components with role-aware `ModelClient` (§21) + golden transcripts:**
- Intent scorer (provisional + validated, §4/§9.1) — `scoring` role.
- Volatility/authority classifier (§5.3) — `scoring` role, seeded topic→class map.
- Planner (decomposition/expansion/reuse, §6c) — `orchestration` role.
- Vetting engine (§8) incl. lateral reading — `scoring` role.
- Reranker (relevance, §5.1 input).
- Synthesizer (§16a) — `synthesis` role — + faithfulness gate (§16) — `faithfulness` role — + abstention (§16b).
- Comparison/decision-support builder (§20).
- Delegation/fold-back (§9.2a gate + §8a principal constraint applied).

**Layer 4 — orchestrator + evaluation:**
- End-to-end pipeline wiring; resilience/resumability/partial-failure + cost accounting/output + $10/day hold (§19.6).
- Eval harness: metric definitions + golden set (§18); then §12a manual scenarios A–G.

**Cross-cutting acceptance criteria (gates on every relevant Layer 1–3 task, NOT a final hardening phase):** §6a egress guard, §6b secrets, §19.6 cost ceilings + per-request cost output + $10/day hold, `schema_version`/`data_class` on every record, §8a principal constraints, §9.9 encryption + tombstone-purge, and the §15 threat-model controls — each an acceptance criterion on the task it touches, with a matching §13a abuse-case test.

**TDD seam summary:** role-aware `ModelClient.for(role)` (§21) and `ToolClient` are the two interfaces that make the pipeline unit-testable; every Layer 2–3 component takes its clients by injection and tests pass fakes returning fixtures / golden transcripts.

---

# PART IV — The seven decisions (resolved)

1. **Graphiti write path** → **pre-structured payloads** (§9.2). Graphiti's internal extraction is the `graph_extraction` model role (§21).
2. **Storage tech** → **Neo4j Community Edition** for the Graphiti graph (best-supported backend, auditability tooling, user-familiar; RAM not VRAM); **SQLite (WAL)** for all flat event logs (security + efficiency + trivial purge). `Ledger` interface keeps FalkorDB/Kuzu a swap-in.
3. **Split-model boundary** → **five-role model router (§21)**, all roles → one cloud frontier model now, per-role reassignable for the local end-state. Configurable, not baked in.
4. **Retention** → **volatility-tiered (§5.3/§9.9)**: episodic record retained indefinitely; `durable`/`slow` knowledge retained/reused; `fast`/`ephemeral` values not promoted to durable facts. Mechanism (data_class tags, tombstone-purge, encryption) fixed day-one; TTL numbers are config. Volume is tens of GB over 30 years — signal quality, not disk, is the driver.
5. **v1 scope** → **all should-fix items in v1** (academic retraction, lateral reading, comparison mode §20, metric definitions §18, resilience, contestedness, saturation, query planning, observability, cost-unit budgeting, cold-start, bias guards, Scenarios D–G). §13 defers only true nice-to-haves.
6. **Cost ceilings** → **per-request cost in standard output** (early phase, config-demotable) + **hard $10/day hold** with immediate notification and manual reset (§19.6).
7. **Fold constants** → recommended defaults seed the `moderate` baseline (180 d / 90 d / ≥4 clusters incl. ≥1 explicit; explicit 3× implicit), elevated to a **class-keyed policy table (§5.3)** so decay/staleness/min-evidence are functions of `(volatility_class, authority_class)`. All tunable in the §12b constants file.

**Remaining tunables (config, not blockers):** the §5.3 volatility class boundaries and topic→class seed map; the per-class constant values; per-tool egress-consent classes; the exact retention TTL numbers per `data_class`.

---

# Verification

The v2 spec is implementation-ready when:
1. **Every Critical + must-fix item in I.4 maps to a concrete section** in Part II (checked: C1→§16, C2→§19, C3→§16a, C4→§5.1, C5→§5.2/§9.4, C6→§2/§9.2/§21, and each must-fix High to its listed home).
2. **Part IV is resolved** — all seven decisions are folded into the v2 spec text (done); remaining items are config tunables.
3. **Every component in Part III has a testable contract** — a validator, a pure function, or an interface with an injectable fake — so a weak model can write a failing test first.
4. **Dry-run Scenarios A–G against the v2 pipeline on paper** — confirm each exercises its intended controls (A: regulatory surfacing + faithfulness; E: comparison matrix + fake-review clustering; F: multi-position surfacing; **G: durable-source reuse + point-in-time belief reconstruction**) before any code.
5. **Hand Part II + Part III to `writing-plans`** — if it can produce dependency-ordered tasks without asking a clarifying question that Part IV didn't already answer, the spec is ready.
