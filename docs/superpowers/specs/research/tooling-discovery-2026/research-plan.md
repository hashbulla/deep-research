# Research plan: Claude Code skill/plugin/MCP discovery channels (2026)

> Generated: 2026-06-13 · Skill: deep-research · Status: awaiting approval

## 1. Question & scope

**Research question:** Current (2026) landscape of Claude Code skill / plugin / MCP discovery channels. For EACH channel — (1) the Anthropic plugin marketplace, (2) vercel-labs/agent-skills, (3) the MCP registry (modelcontextprotocol/registry), (4) smithery.ai, (5) awesome-claude-* GitHub lists, (6) general GitHub discovery — characterize: the discovery API/feed shape (REST / JSON / static manifest / git), how to query it programmatically, update freshness / staleness behavior, and the trust signals each exposes (official/verified status, maintenance cadence, stars, provenance, package signing, supply-chain incident history). Goal: design an automated recommender that ranks and trust-grades third-party skills/plugins/MCPs by maintenance, provenance, popularity, recency, and official status — and never auto-installs.

**Classification:** technical
**Tier profile:** Tier 1+2 technical union (registry §6), topic-augmented with vendor-primary + security-research domains (see §3)
**Length:** exhaustive (12–20 sub-questions, 150–250 candidates, 100+ cited target)
**Output language:** en
**Recency window:** `--since 2025-01-01` (the ecosystem barely predates this; plugins GA'd ~Oct 2025, MCP registry preview ~Sept 2025)
**Min corroboration:** 2
**Model tier:** session model `claude-opus-4-8[1m]` · synthesis `opus` · subagent overrides: grading=`sonnet`, entailment judge=different Claude model (per `references/model-tiers.md`)
**Confidential path:** no

## 2. Sub-question decomposition

| ID | Category | Sub-question | Tavily tool | include_domains (preview) | time_range / start_date | Target candidates |
|---|---|---|---|---|---|---|
| sq1 | factual | Anthropic plugin marketplace: marketplace.json / plugin manifest schema, how a marketplace is defined/added (`/plugin`, marketplace git repos), is there a programmatic feed/API? | tavily_search + tavily_map | docs.claude.com, docs.anthropic.com, anthropic.com, github.com | start=2025-01-01 | 12 |
| sq2 | factual | MCP registry (registry.modelcontextprotocol.io): REST/OpenAPI surface, list/search endpoints, data model, namespace/verification model | tavily_search + tavily_map | modelcontextprotocol.io, github.com, registry.modelcontextprotocol.io | start=2025-01-01 | 12 |
| sq3 | factual | smithery.ai: discovery API endpoints, query/auth model, ranking + install signals it exposes | tavily_search | smithery.ai, github.com | start=2025-01-01 | 10 |
| sq4 | factual | vercel-labs/agent-skills: repo structure, skill manifest shape, how skills are listed/distributed, any feed | tavily_search | github.com, vercel.com | start=2025-01-01 | 10 |
| sq5 | factual | awesome-claude-* GitHub lists: which lists exist (awesome-claude-code, -skills, -mcp), curation cadence, staleness, programmatic parsing | tavily_search + GitHub cond. | github.com | start=2025-01-01 | 10 |
| sq6 | factual | General GitHub discovery: topics/tags (`claude-code`, `claude-skill`, `mcp-server`, `model-context-protocol`), search shards, metadata available | **GitHub conditional** (gh CLI) | github.com | start=2025-01-01 | 15 |
| sq7 | contextual | Trust signals across channels: official/verified badges, namespace verification (DNS/GitHub-OIDC), publisher identity — how does each channel signal "official"? | tavily_search + tavily_research | modelcontextprotocol.io, docs.claude.com, github.com, smithery.ai | start=2025-01-01 | 12 |
| sq8 | contextual | Package signing & provenance: sigstore / npm provenance / OIDC attestation / MCP registry signing — what attestation exists in this ecosystem? | tavily_search | github.com, slsa.dev, sigstore.dev, modelcontextprotocol.io | start=2025-01-01 | 10 |
| sq9 | contextual | Freshness / staleness: how each channel exposes last-updated / maintenance cadence; how to programmatically detect an abandoned listing | tavily_search | github.com, modelcontextprotocol.io, smithery.ai | start=2025-01-01 | 10 |
| sq10 | contextual | Popularity / maintenance metrics: install counts, stars, download counts per channel; which metrics exist and how to fetch them | tavily_search | smithery.ai, github.com, modelcontextprotocol.io | start=2025-01-01 | 10 |
| sq11 | contradictory | MCP/plugin supply-chain incidents & risks: malicious MCP servers, tool-poisoning, prompt-injection via tool descriptions, "rug pull" — independent security research vs vendor framing | tavily_search + tavily_research | invariantlabs.ai, simonwillison.net, theregister.com, arstechnica.com, snyk.io, github.com | start=2025-01-01 | 14 |
| sq12 | contradictory | Reliability of trust signals: are stars / install counts gameable? fake-star / fake-install evidence in this ecosystem (ties to the fake-star gate the recommender reuses) | tavily_search | github.blog, arxiv.org, theregister.com, github.com | start=2025-01-01 | 10 |
| sq13 | recency | MCP registry 2025→2026: launch (preview Sept 2025), GA status, API stability/versioning, governance/moderation model changes | tavily_search | modelcontextprotocol.io, github.com, anthropic.com | time_range=year, start=2025-01-01 | 10 |
| sq14 | recency | Claude Code plugins/marketplaces 2025→2026: plugin launch, whether an official Anthropic marketplace exists, current ecosystem state | tavily_search | docs.claude.com, anthropic.com, github.com | time_range=year, start=2025-01-01 | 10 |

## 3. Domain allowlist / blocklist

**Baseline from tier profile (Tier 1+2 technical union, §6):** arxiv.org, *.gov, *.europa.eu, anthropic.com, openai.com, github.com (official orgs), docs.python.org, kubernetes.io, cncf.io, stackoverflow.com, reuters.com, apnews.com, ft.com …+more

**Topic-augmented primary domains (added):** docs.claude.com, docs.anthropic.com, modelcontextprotocol.io, registry.modelcontextprotocol.io, smithery.ai, vercel.com, github.blog, slsa.dev, sigstore.dev

**Topic security/incident domains (Tier 3 — corroboration-required):** invariantlabs.ai, simonwillison.net, theregister.com, arstechnica.com, thenewstack.io, snyk.io, bleepingcomputer.com

**User `--domains` additions:** none
**User `--exclude` additions:** none

**Flagged additions below Tier 2** (confirm before Phase 1): smithery.ai, invariantlabs.ai, simonwillison.net, snyk.io, bleepingcomputer.com — admitted as **primary-for-self** (smithery's own API) or **high-signal security research** (the others). Each is graded Tier 3; any claim resting on one alone is corroboration-required and cannot enter the executive summary uncorroborated.

**Credibility overlay (MBFC static, user-scope):** not checked (current-affairs-oriented; this is a technical run) — overlay skipped.

## 4. Retrieval plan

**Phase 1 (broad recall):**
- 14 parallel `tavily_search` calls (advanced depth), paced in 2 batches to stay under 20 req/min
- 2 `tavily_map` calls: `registry.modelcontextprotocol.io` (API surface) and the `modelcontextprotocol/registry` GitHub tree (sq1, sq2)

**Conditional sources (declared here):**
- **GitHub tooling-discovery (`references/github-research.md`): ACTIVE.** `gh` authenticated (account `hashbulla`; search 30/30, graphql 4980/5000 at preflight). `experts.yaml` present → expert-starred prior available. Used for sq5, sq6, sq12. Star-band sharding on topics `claude-code`, `mcp-server`, `model-context-protocol`, `claude-skill`; GraphQL enrichment; ecosyste.ms dependents; deterministic ranking via `scripts/github_rank.py`. Repo READMEs are untrusted data (A6) — never executed, never self-upgrade a claim.
- **Context7 doc retrieval:** available but **gated OFF** — the run's intent is ecosystem characterization, not "integrate/configure a named library." Marginal candidates (sq1 Claude Code plugin docs, sq2 registry API) will be served by Tavily + official docs; Context7 invoked only if Tavily coverage on a registry's API contract is thin, then degrade-recorded.
- **Newsletter-signal:** topic IS work-relevant (`ai-engineering`), but `~/.claude/deep-research/newsletter-corpus/` is **absent** → source skipped, degradation recorded in the Methodology note (optional-source rule, §7).
- **Academic-graph:** not applicable (no scholarly SOTA sub-question; arXiv reachable via allowlist for sq12 fake-star research only).

**Phase 4 (deep extract & synthesis):**
- 3–4 `tavily_research model=pro` calls on the synthesis-heavy sub-questions (sq7 trust signals, sq11 incidents, sq13 registry evolution)
- ~6 `tavily_extract extract_depth=advanced` calls on key URLs (registry OpenAPI/README, plugin-marketplace docs, MCP registry verification docs, top security advisories)

**Estimated total Tavily calls:** ~26 (16 Phase 1 + ~10 Phase 4) + GitHub via gh CLI (off Tavily quota)
**Estimated runtime:** 9–14 min
**Rate-limit headroom:** peak ≤ 14 calls/min (Phase-1 batch 1) — within the 20 req/min ceiling

## 5. Expected contradiction axes

1. **Trust-signal reliability** — vendor-reported install/star/download counts vs independent fake-signal research (fake stars, install-count gaming). Drives sq10/sq12.
2. **MCP supply-chain risk severity** — security-researcher framing (tool-poisoning, rug pulls, line-jumping are systemic) vs vendor/ecosystem framing (mitigated by verification + user approval). Drives sq11.
3. **Registry maturity** — "MCP registry is production-ready / stable API" (vendor) vs "still preview, sub-registry model, API churn" (independent). Drives sq2/sq13.

## 6. Stop conditions

Successful completion requires **all** of:

- [ ] Groundedness ≥ 0.95
- [ ] Source quality ≥ 0.80 Tier 1/2 — **at risk** on this topic (heavy Tier 2 vendor + Tier 3 security blogs; see §7). If unmet, the Methodology note documents the ceiling and affected claims route to Needs Verification.
- [ ] Coverage ≥ 0.90 of sub-questions
- [ ] Corroboration rate ≥ 0.80
- [ ] Source-count floor: exhaustive → 100+ (calibration, not hard contract; one expansion round if trending under by Phase 3)
- [ ] Zero pending CRAG iterations

## 7. Known gaps at planning time

- **Tier-1 academic coverage is ~nil.** This is an 8-month-old ecosystem; primary evidence is vendor docs (Tier 2: anthropic.com, modelcontextprotocol.io) + official-org GitHub + the registries' own APIs. Source-quality gate may land below 0.80; triangulation is cross-registry + cross-source rather than via peer-reviewed Tier 1. Declared, not hidden.
- **Vendor-primary Tier-3 sources** (smithery.ai for its own API; invariantlabs.ai/simonwillison.net for MCP security) are admitted under corroboration-required discipline; none may solely support an executive-summary claim.
- **Newsletter-signal corpus absent** → work-relevant routing seeds unavailable; pure-Tavily + GitHub retrieval (no quality loss to grading, only to recall breadth).
- **Live registry API shapes may have churned** since any given source's publication date; sq2/sq13 will prefer the registries' own current docs (tavily_extract on the live OpenAPI/README) over secondary descriptions, and flag version at retrieval.
- **Recommender-design framing is out of scope for this report.** This run produces graded findings about the discovery landscape only; the spec that consumes it (the recommender feature) is authored separately. The report emits exactly the four artifacts — no design commentary (SKILL.md scope constraint).

## 8. Artifacts

At Phase 6 the skill will emit (to `docs/superpowers/specs/research/tooling-discovery-2026/`):

- `research-plan.md` (this file — approved)
- `research-report.md` (final synthesis, en)
- `research-sources.json` (all cited sources, Admiralty-graded)
- `research-evidence.json` (claim → sources mapping with credibility)

---

**Approve this plan to proceed to Phase 1.**
Reply `approve` to run as-specified, or edit any section above and re-send.
