# Methodology — distilled from `deep-research-report.md`

> This file is the **operational specification** the `deep-research` skill executes. It is a near-verbatim distillation of `deep-research-report.md` (April 2026 revision, sha256 `cb2fe20dced3c4bb…`). Where SKILL.md and this file disagree, **this file wins**. Back-references cite the report section (e.g., `[R§3.1]`).

---

## 1. The Perplexity Deep Research reference loop [R§1]

Five stages, executed iteratively (not single-pass):

1. **Query Decomposition** — split the question into orthogonal sub-topics and atomic search intents.
2. **Parallel Retrieval** — one dedicated search per sub-topic, using a tiered source preference (peer-reviewed > institutional > established press > general web).
3. **Structured Note Synthesis** — write partial answers into intermediate structured notes before final synthesis.
4. **Conflict Detection & Verification** — flag conflicting claims, double-check against independent sources before synthesis.
5. **Final Narrative with Reliability Notes** — single grounded narrative with inline citations and explicit uncertainty markers.

**Key differentiator [R§1]:** the research plan is refined iteratively as new evidence arrives. Do not emit all queries at once. Start wide, then narrow.

---

## 2. Anthropic-published patterns [R§2]

### 2.1 Pre-context filtering [R§2.1]
Filter results **before they enter the LLM context**: score thresholds, domain-tier checks, date filters, dedupe. In API contexts this is `web_search_20260209` Dynamic Filtering; inside a Claude Code skill, the equivalent is inline Claude reasoning applied to Tavily results *before* the synthesis prompt. Measured impact: +16.3pp BrowseComp, −24% input tokens.

### 2.2 Domain allow-lists and block-lists [R§2.2]
- `allowed_domains` → explicit allowlist; only these domains are retrievable.
- `blocked_domains` → explicit denylist for SEO farms, aggregators.
- **Security:** normalize every domain to **punycode** before comparison. Unicode homograph attacks (`аrxiv.org` with a Cyrillic 'а') defeat naive matching.

### 2.3 Anthropic internal research system lessons [R§2.3]
- Early agents preferred SEO-optimized content farms over academic PDFs unless explicit source-quality heuristics were in the system prompt. **→ Encode the Tier registry (§6) in the decomposition prompt.**
- **Orchestrator-worker pattern:** a lead orchestrator dispatches parallel sub-agents, each searching independently; one low-quality chain does not contaminate the whole answer. **→ Phase 1 runs per-sub-question searches in parallel, per-sub-question grading.**
- LLM-as-judge eval included a "source quality" dimension: *"Did the agent use primary sources over lower-quality secondary sources?"* **→ Phase 3 rerank prompt must score primary-vs-secondary explicitly.**
- **Start wide, then narrow:** short broad queries first to discover the landscape; progressively narrower follow-ups to validate and deepen.

### 2.4 Skill authoring guidance [R§2.4]
- Describe **what sources constitute a good answer**, not only what information to retrieve.
- Use **extended thinking** before the first tool call (Phase 0).
- Use **interleaved thinking** after each retrieval result (Phase 2, Phase 3).
- Maintain lightweight URL / path identifiers in context; load full content on demand ("just in time") to avoid polluting context with low-quality content.

### 2.5 First-class source-quality eval [R§2.5]
Three gates every deep-research output must pass:
- **Groundedness** — every claim supported by a retrieved source (no hallucination).
- **Coverage** — key facts that a correct answer must include are present.
- **Source quality** — the agent reached for primary sources, not just the first retrieved.

---

## 3. Tavily retrieval parameters [R§3]

### 3.1 Core quality parameters [R§3.1]

| Parameter | Skill setting | Rationale |
|---|---|---|
| `search_depth` | `advanced` (default) | Returns semantic chunks reranked by relevance. 2–5× credit cost of `basic`; non-negotiable for research. |
| `include_domains` | Tier 1+2 by default, Tier 1 only for `--profile academic` | Up to 300 domains. See §6. |
| `exclude_domains` | SEO farms + aggregators + `--exclude` additions | Up to 150. |
| `max_results` | 10 per Phase-1 call | Rerank down to top 5–7 in Phase 3. |
| `include_raw_content` | `true` for Phase-1 | Full page content needed for accurate Phase-2 grading. |
| score filter | **keep only `score > 0.7`** | Applied in Phase 2. Threshold is taken directly from the report. |
| `auto_parameters` | `true` unless explicitly overridden | Tavily picks remaining sensible defaults. |

### 3.2 `advanced` vs `basic` depth [R§3.2]
`advanced` returns **semantic chunks** (not full pages) reranked by relevance. This is the correct default for a serious research skill. `basic` is acceptable only for the broadest first-pass recency check if credit is a concern.

### 3.3 Tavily Research endpoint [R§3.3]
Autonomous Perplexity-style loop: `Query → Search → Read → Identify gaps → Re-search → Synthesize`. Returns structured synthesis with citations. Cost 15–250 credits/call. Use `mcp__tavily__tavily_research`:
- `model=pro` → multi-step agentic research on narrow sub-questions in exhaustive mode.
- `model=mini` → narrow factual sub-questions.
- **Do not use as the Phase-1 default** — it removes phase-level control needed for custom source grading. Use `tavily_search` at Phase 1; use `tavily_research` at Phase 4 only.

### 3.4 Score-based post-filter pattern [R§3.4]

```
results = tavily_search(query, search_depth="advanced", max_results=10)
trusted = [r for r in results
           if r.score > 0.7
           and canonical(r.url) not in blocked_urls
           and domain_tier(r.url) in (TIER_1, TIER_2)]
```

Pair score filtering with the domain-tier function (§6). Only Tier 1/2 results enter Phase 3 as primary candidates; Tier 3 results are retained solely as potential secondary corroborators (§4.1 Tier 3 rule) and never as primary claim support.

---

## 4. Source grading — OSINT tradecraft [R§4]

### 4.1 NATO Admiralty 2×6 matrix [R§4.1]

**Reliability (A–F), assigned by domain tier:**

| Grade | Meaning | Mapping |
|---|---|---|
| A | Completely reliable | Tier 1 primary (arXiv, journals, `*.gov`, IGO official) |
| B | Usually reliable | Tier 2 (labs' official research pages, established press) |
| C | Fairly reliable | Tier 3 trade press with editorial standards |
| D | Not usually reliable | Tier 3 low-editorial / Tier 4 with byline credibility |
| E | Unreliable | Tier 4 anonymous content, known misinformation sites |
| F | Cannot be judged | Unknown domain, no editorial signal |

**Credibility (1–6), assigned by corroboration after synthesis — NORMATIVE ALGORITHM.**

This cascade is the single source of truth for credibility assignment. `references/quality-gate.md` and `SKILL.md` Phase 6 reproduce it verbatim; `README.md` renders it as a table. Where any copy disagrees, this section wins (invariant I3).

Counters are computed at assignment time by joining each claim's `supporting_source_ids` / `contradicting_source_ids` against `research-sources.json` by `id` to resolve `domain_tier`:

```
supporting_Tier12 = count of distinct supporting sources with domain_tier ∈ {1, 2}
supporting_Tier1  = count of distinct supporting sources with domain_tier = 1
contradicting     = count of distinct contradicting sources with domain_tier ∈ {1, 2}

if   supporting_Tier12 ≥ 2 and contradicting = 0:               → 1 CONFIRMED
elif supporting_Tier1  ≥ 1 and contradicting = 0:               → 2 PROBABLY TRUE
elif supporting_Tier12 ≥ 2 and contradicting = 1:               → 2 PROBABLY TRUE
elif supporting_Tier12 = 1 and contradicting = 0:               → 3 POSSIBLY TRUE
elif supporting_Tier12 ≥ 1 and contradicting ≥ 1 (Tier-equal):  → 4 DOUBTFUL
elif contradicting ≥ 2 (Tier 1/2):                              → 5 IMPROBABLE
else (only Tier 3/4 support, or zero supporting):               → 6 UNVERIFIED
```

**Tier 3 rule (single, deterministic):** Tier 3 sources never change the credibility level. They are admissible as secondary corroborators only when ≥1 supporting Tier 1/2 source exists (Phase-2 admissibility gate); a claim supported only by Tier 3/4 sources is credibility 6.

> Deviation from R§4.1, resolved 2026-06-12: the report's row-3 clause "single Tier 1 uncorroborated → 3" is unreachable under this precedence cascade — a single Tier 1 source matches the credibility-2 rule first. Rule precedence is the deterministic resolution; the report's prose table was internally ambiguous (single Tier 1 appeared in both rows 2 and 3).

**Label → report-section routing (deterministic):**

| Credibility | Label | Report section |
|---|---|---|
| 1 | CONFIRMED | Main body; only label admitted in the executive summary |
| 2–3 | PROBABLY TRUE / POSSIBLY TRUE | Main body with inline tag; never the executive summary |
| 4–6 | DOUBTFUL / IMPROBABLE / UNVERIFIED | "Needs Verification" section only |

Actionable range: A1–B2.

### 4.2 CRAAP test [R§4.2]
Automatable in pre-retrieval / early grading:

| Dimension | Signal | Automated? | Skill phase |
|---|---|---|---|
| **C**urrency | Publication / last-updated date | ✅ | Phase 2 (reject if outside `--since` and sub-question is time-sensitive) |
| **R**elevance | Query-document semantic similarity | ✅ | Tavily `score` in Phase 2 |
| **A**uthority | Author credentials, domain tier, peer-review status | ✅ | Phase 2 (tier) + Phase 3 (byline if available) |
| **A**ccuracy | Evidence-backed, cross-checkable | ⚠️ LLM-judge | Phase 3 rerank + Phase 5 CRAG |
| **P**urpose | Hidden agenda, sensationalism | ⚠️ LLM-judge | Phase 3 rerank |

Drop a candidate that fails ≥2 automatable dimensions (Phase 2). Drop a candidate that fails both judged dimensions after rerank (Phase 3).

### 4.3 Five-step OSINT validation [R§4.3]

1. **Grade the source** — Admiralty A–F by tier + editorial check.
2. **Validate against independent sources** — ≥`--min-corroboration` (default 2) Tier 1/2 sources per factual claim.
3. **Interrogate model logic** — Claude must be able to trace every claim to a URL; otherwise flag as unverified.
4. **Avoid the confidence trap** — LLM fluency ≠ accuracy. Every retrieved chunk is provisional until corroborated.
5. **Automate with curated domain lists** — §6 registry.

---

## 5. Retrieval pipeline — two-stage retrieve + rerank [R§5]

```
STAGE 1 — BROAD RECALL (Phase 1)
  Query Decomposer → Parallel tavily_search (advanced) → 50–100 candidates
  → Domain-tier pre-filter → Score threshold (>0.7)
        ↓  ~20 candidates per sub-question

STAGE 2 — PRECISION RERANK (Phases 2 + 3)
  CRAAP + Admiralty filter → LLM-as-judge authority check (≤10 docs)
        ↓  Top 5–7 per sub-question

STAGE 3 — SYNTHESIS (Phases 4–6)
  LLM synthesis with grounding check → CRAG loop if groundedness < threshold
```

### 5.1 Query decomposition patterns [R§5.1]
Use the CoT pattern by default, plus category coverage (§8):
- **Factual** (what / when / who)
- **Contextual** (why / how / implications)
- **Contradictory / alternative perspectives**
- **Recency** (what changed in the last 12 months or `--since` window)

Advanced patterns (`--length exhaustive`): **LevelRAG** (high-level decomposer → atomic sub-queries) for multi-faceted research; **PRISM** (iterative Question-Analyzer → Selector → Adder loop) for multi-hop fact-finding.

### 5.2 Reranking [R§5.2]
Available here: **Tavily `advanced` depth handles Stage-1 semantic rerank**, and an **LLM-as-judge pointwise/listwise pass handles Stage-2 precision rerank** on ≤10 docs per sub-question. Neither Cohere Rerank nor a local cross-encoder is accessible from this MCP surface; the LLM-as-judge pass approximates cross-encoder accuracy at the cost of latency (acceptable on a ≤10-doc set).

### 5.3 Corrective RAG (CRAG) loop [R§5.3]

```
Synthesize → grade each claim for groundedness
  if groundedness < 0.95 OR corroboration < 0.80:
      rewrite query → supplement tavily_search → re-retrieve → re-synthesize
  else: emit
```

Max 2 CRAG iterations per failing sub-question AND ≤6 CRAG iterations total per run, prioritized by ascending groundedness. Every source retrieved during a CRAG iteration passes the full Phase-2 gate battery before citation. If still failing, move affected claims to "Needs Verification" with explicit reason.

---

## 6. Domain tier registry [R§6]

### Tier 1 — Primary / Peer-reviewed / Government

```
# Academic preprint & journals
arxiv.org, biorxiv.org, medrxiv.org, ssrn.com, semanticscholar.org
pubmed.ncbi.nlm.nih.gov, pmc.ncbi.nlm.nih.gov
nature.com, science.org, cell.com, thelancet.com
ieee.org, acm.org, springer.com, wiley.com, oup.com, sagepub.com
aclanthology.org, neurips.cc, icml.cc, iclr.cc

# Government & intergovernmental
*.gov, *.mil, *.gc.ca, *.gouv.fr, *.europa.eu
who.int, un.org, worldbank.org, imf.org, oecd.org, nato.int

# Statistics & official data
census.gov, bls.gov, eurostat.ec.europa.eu, data.gov
```

→ Admiralty reliability **A** (use with `include_domains` for `--profile academic`).

### Tier 2 — Institutional / Industry research / Established press

```
# AI/tech primary research labs
anthropic.com, openai.com, deepmind.google, research.google
ai.meta.com, microsoft.com/en-us/research, labs.perplexity.ai

# Established tech documentation
docs.python.org, docs.rust-lang.org, kubernetes.io, cncf.io
github.com (official org repos only), stackoverflow.com (accepted answers)

# Established press (international)
reuters.com, apnews.com, bbc.co.uk, ft.com, economist.com
nytimes.com, washingtonpost.com, theguardian.com, lemonde.fr

# Industry analysis
gartner.com, mckinsey.com, hbr.org, mitsloan.mit.edu
```

→ Admiralty reliability **B**. Default Tier 1+2 union for `--profile mixed` / `technical` / `current-affairs`.

### Tier 3 — Trade press / Technical blogs with editorial standards

```
techcrunch.com, wired.com, arstechnica.com, theregister.com
towardsdatascience.com (peer-reviewed), thenewstack.io
substack.com (institution-affiliated authors only)
```

→ Admiralty reliability **C**. Acceptable only with corroboration from Tier 1/2.

### Tier 4 — General web / social / forums

```
reddit.com, twitter.com, x.com, linkedin.com, medium.com
```

→ Admiralty reliability **D–F**. Never cite as primary. Only admissible as social-signal pointers toward Tier 1/2 sources, in a clearly-labeled "Signals" subsection.

### Automatic blocklist
SEO-farm heuristic (defense-in-depth below the main `score > 0.7` gate at `references/quality-gate.md` §Phase-2): if the 0.7 gate is ever relaxed for a known-scarce topic, reject any result with `score < 0.3` plus unknown domain. Under the default 0.7 gate this rule is subsumed. Supplement with NewsGuard / MBFC ratings if integrated.

---

## 7. Specialized APIs (reference only) [R§7]
The report recommends a multi-API stack (Tavily + Exa `findSimilar` + Valyu + Firecrawl). Only the **Tavily MCP** is available in this environment. Known coverage gap: deep academic citation-chaining (Exa) and full-text academic search (Valyu). Mitigation: include full Tier 1 academic domain list in `include_domains`, plus `tavily_extract extract_depth=advanced` on any paper URL surfaced during rerank.

**Optional-source rule.** Any retrieval source added beyond the Tavily MCP suite (additional MCP servers, CLIs, keyed APIs) is OPTIONAL by contract: when its credential, server, or endpoint is absent or persistently failing, the skill degrades to Tavily-only retrieval, records the degradation in the report's Methodology note, and declares the source's availability status in `research-plan.md` at the human gate. A missing optional source is never a run failure.

---

## 8. Prompt engineering [R§8]

### 8.1 Source preference hierarchy (inject into Phase 0 + Phase 3 prompts)
See §6. Phrase to Claude: "Apply the Tier 1–4 hierarchy. Never use Tier 4 as sole evidence for a claim. Flag any claim supported only by Tier 3 as requires-corroboration."

### 8.2 Decomposition prompt [R§8.2]
```
Before issuing any search queries, decompose the research question into:
1. Core factual sub-questions (what / when / who)
2. Contextual sub-questions (why / how / implications)
3. Contradictory / alternative-perspective sub-questions
4. Recency sub-questions (what has changed in the last 12 months)
Issue parallel searches for each category. Synthesize only after each
category has ≥2 independent Tier 1/2 sources.
```

### 8.3 Post-retrieval credibility check prompt [R§8.3]
```
For each source in your retrieved results, evaluate:
- Is the author or publisher identified and credible?
- Is the content dated and is the date relevant to the claim?
- Is this a primary source (original research/data) or secondary (summary/commentary)?
- Can the core claim be independently verified from another source?
Discard results that fail two or more criteria. Do not synthesize claims
resting on a single unverifiable source.
```

---

## 9. Seven-phase architecture [R§9] — this is the skill's execution spine

```
PHASE 0  Query Architect         (extended thinking, no tool calls)
PHASE 1  Broad Retrieval         (parallel tavily_search + tavily_map)
PHASE 2  Source Grading          (inline: tier + CRAAP + Admiralty + dedupe)
PHASE 3  Precision Rerank        (LLM-as-judge on ≤10 docs per sub-question)
PHASE 4  Deep Extract & Synthesis(tavily_research mini/pro + tavily_extract)
PHASE 5  Grounding Validation    (CRAG loop, up to 2 iterations)
PHASE 6  Confidence Annotation   (Admiralty 1–6 per claim, Needs Verification isolation)
```

The **human gate** sits between Phase 0 and Phase 1. No Tavily call fires before the plan is approved.

---

## 10. Evaluation harness [R§10]

Quality gates applied at Phase 5 (deterministic thresholds in `references/quality-gate.md`):

| Gate | Target | Failure action |
|---|---|---|
| Groundedness | ≥ 0.95 | CRAG re-query loop |
| Source quality | ≥ 0.80 Tier 1/2 among cited | Expand allowlist, re-retrieve |
| Coverage | ≥ 0.90 of sub-questions answered with ≥1 Tier 1/2 source | Add follow-up sub-question |
| Freshness | Median source date within `--since` window (or last 3 years if no `--since`) | Add recency sub-question |
| Corroboration rate | ≥ 0.80 claims with ≥`--min-corroboration` sources | CRAG re-query, then move to Needs Verification |

## 11. Known gaps [R§11]

- **Paywalled academic content** — surface abstracts, prefer Tier 1 open-access equivalents. Flag as credibility 3 if only abstract retrieved.
- **Temporal bias in domain trust** — a historically A-reliable domain may publish a low-quality article. Domain tier is a prior; author / date / primary-vs-secondary is the posterior.
- **LLM-as-judge circularity** — same model used for synthesis and judgment. Mitigate: use distinct prompt personas for synthesis vs rerank vs grounding.
- **JS-rendered institutional sites** — Tavily renders; built-in `fetch` tool does not. If `tavily_extract` returns empty, retry with `extract_depth=advanced`.
- **Unicode homograph spoofing** — normalize every domain to punycode before comparison. Reject any mismatch.

---

## Length calibration (skill-specific extension of report §10)

| `--length` | Sub-questions | Broad candidates | Final cited | CRAG max | Tavily calls (approx) |
|---|---|---|---|---|---|
| short | 3–5 | 20–30 | 15–25 | 1 | 8–15 |
| standard | 6–10 | 50–80 | 35–60 | 2 | 20–40 |
| exhaustive | 12–20 | 150–250 | **100+** | 2 per failing sub-question, ≤6 total | 40–80 |

Pace all modes under Tavily's 20 req/min research-endpoint ceiling. For exhaustive, interleave `tavily_search` (cheap) with `tavily_research` (expensive) so research calls stay ≤15/min.
