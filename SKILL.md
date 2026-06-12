---
name: deep-research
description: Agentic multi-source deep research via Tavily MCP, calibrated to Perplexity Deep Research (100+ sources on exhaustive runs). Activate on /deep-research, "deep research on X", "recherche approfondie sur X", "analyse multi-sources", "comparative analysis of X vs Y with sources". Do NOT activate for single-fact lookups, known-URL extractions, or library doc lookups (use tavily_skill).
---

## Provenance & deviations

- **Methodology source:** `./deep-research-report.md` in the invocation CWD (or the copy bundled under `references/methodology.md` if the invocation CWD has no report). Hash at generation time: `cb2fe20dced3c4bb…` (sha256, April 2026 version).
- **Report wins:** Where this SKILL.md and `references/methodology.md` disagree, follow the methodology reference. `references/methodology.md` is a faithful distillation of the report — treat it as the spec.
- **Deviations from the integration scaffold (documented, intentional):**
  - The scaffold proposes `tavily_research model=pro` as the default for multi-step agentic research. The report (§3.3) reserves the Research endpoint for autonomous loops and recommends the Search endpoint when phase-level control is needed. **This skill uses `tavily_search search_depth=advanced` as the primary retrieval call for Phase 1 broad recall, and `tavily_research` only for Phase 4 narrow sub-question synthesis** where the inner loop can be delegated.
  - The scaffold references `web_search_20260209` Dynamic Filtering (Anthropic API only). It is not available inside a Claude Code skill. **Equivalent functionality — score thresholding, domain tier gating, dedupe — is performed by Claude's inline reasoning on Tavily results** before any content enters the synthesis prompt.
  - The scaffold references Cohere Rerank / `ms-marco` cross-encoders as a Stage-2 reranker. Neither is an MCP tool available here. **Tavily `advanced` depth already returns semantically reranked chunks;** Stage-2 precision rerank is performed by a structured LLM-as-judge pass on a small candidate set (≤10 docs per sub-question), per report §5.2.
  - The scaffold references Exa `findSimilar` and Valyu as academic fallbacks. Neither is in the MCP registry. **Academic reach is covered by Tavily `include_domains` restricted to Tier 1** (arXiv, PubMed, `*.gov`, journals — see `references/methodology.md` §6). Document this as a known coverage gap for pure-academic queries.
- **Interim defaults** (report is silent; scaffold values retained and tagged inline with `<!-- interim default -->`):
  - Artifact filenames (`research-plan.md`, `research-report.md`, `research-sources.json`, `research-evidence.json`).
  - Flag names (`--since`, `--domains`, `--length`, `--lang`).
  - Default `--length standard`; exhaustive mode targets 100+ sources.
  - Score threshold `> 0.7` is taken directly from report §3.1 (not interim).

## Overview

This skill runs intelligence-grade, multi-source research against the open web using the Tavily MCP suite. It implements the 7-phase architecture defined in `references/methodology.md` (derived from report §9): Query Architect → Broad Retrieval → Source Grading → Precision Rerank → Deep Extract & Synthesis → Grounding Validation → Confidence Annotation. Sources are graded on the NATO Admiralty A–F × 1–6 scale (report §4.1); claims graded credibility 4–6 by the normative cascade (`references/methodology.md` §4.1) are isolated in a "Needs Verification" section, and credibility 2–3 claims carry inline tags in the main body (never the executive summary). The skill halts after Phase 0 for user approval before any Tavily call fires.

## Trigger

Activate on any of:

- Slash: `/deep-research <question>`
- Natural: "deep research on X", "recherche approfondie sur X", "analyse multi-sources", "comparative analysis of X vs Y with sources", "benchmark X against Y with citations"

Do NOT activate for:

- Single-fact lookups (use `tavily_search` directly)
- Known-URL extractions (use `tavily_extract`)
- Library / API documentation queries (use `tavily_skill`)
- Domain sitemap discovery (use `tavily_map`)

## Inputs

**Required:** a research question in any natural language.

**Flags** (all optional; `<!-- interim default: flag names not prescribed by report -->`):

| Flag | Values | Default | Effect |
|---|---|---|---|
| `--length` | `short` \| `standard` \| `exhaustive` | `standard` | Calibrates sub-question count, retrieval breadth, target source count (see `references/methodology.md` §"Length calibration") |
| `--lang` | `fr` \| `en` \| (ISO 639-1) | inferred from question | Language of `research-report.md` output |
| `--since` | `YYYY` or `YYYY-MM-DD` | inferred from question freshness needs | Lower bound for source publication date (passed to Tavily `time_range` / `start_date`) |
| `--domains` | comma-separated list | tier profile from methodology §6 | Additional allowlist appended to the tier profile |
| `--exclude` | comma-separated list | tier profile blocklist | Additional blocklist |
| `--profile` | `academic` \| `technical` \| `current-affairs` \| `mixed` | inferred | Domain tier profile (selects `include_domains` baseline) |
| `--min-corroboration` | integer ≥1 | `2` | Minimum independent Tier 1/2 sources required for a claim to be CONFIRMED |

Target source counts per `--length` (from `references/methodology.md`):

| Length | Sub-questions | Broad recall candidates | Final cited | Rough runtime |
|---|---|---|---|---|
| short | 3–5 | 20–30 | 15–25 | 1–2 min |
| standard | 6–10 | 50–80 | 35–60 | 3–5 min |
| exhaustive | 12–20 | 150–250 | **100+** | 8–15 min |

## Workflow

### Phase 0 — Query Architect (extended thinking, no tool calls)

1. Parse the research question and flags. Normalize any domains to punycode (defense against Unicode homograph attacks, report §2.2 and §11).
2. Classify the query: `academic` / `technical` / `current-affairs` / `mixed`. Choose the corresponding tier profile from `references/methodology.md` §6 unless `--profile` overrides.
3. Decompose using the CoT pattern documented in `references/methodology.md` §5.1 and §8.2:
   - **Factual sub-questions** (what / when / who)
   - **Contextual sub-questions** (why / how / implications)
   - **Contradictory / alternative-perspective sub-questions**
   - **Recency sub-questions** (what changed in the last 12 months — or `--since` window)
4. For each sub-question, draft:
   - Tavily tool to use (Phase 1: `tavily_search`; Phase 4: `tavily_research` mini|pro; see `references/tool-routing.md`)
   - Preliminary `include_domains` (max 300) and `exclude_domains` (max 150)
   - `time_range` or `start_date` if recency-sensitive
   - Target candidate count
5. Write `research-plan.md` using the template in `references/research-plan-template.md`. The plan must include: classification, tier profile, sub-question list with proposed Tavily calls, domain allowlist preview, estimated total Tavily calls (respect 20 req/min research-endpoint rate limit — pace accordingly), expected contradiction axes, stop conditions from `references/quality-gate.md`.
6. **HUMAN GATE — STOP.** Present `research-plan.md` to the user and wait for explicit approval (or an edit request). Do not proceed to Phase 1 until approval is received. This gate is non-negotiable; it is listed in `references/anti-patterns.md` as a forbidden pattern to skip.

### Phase 1 — Broad Retrieval (parallel)

1. Execute the approved plan's Phase-1 calls. Default tool: `mcp__tavily__tavily_search` with `search_depth=advanced`, `include_raw_content=true`, `max_results=10`, tier-profile `include_domains` + any `--domains` additions.
2. For recency-sensitive sub-questions, add `time_range` or `start_date` / `end_date`.
3. For domain discovery sub-questions (e.g., "what are the authoritative sources on X"), use `mcp__tavily__tavily_map` first to surface a URL tree, then feed selected paths back into `tavily_search`.
4. Pace calls to stay under Tavily's 20 req/min ceiling. If the plan exceeds 20 calls in a minute, batch by tier: Tier 1 allowlisted calls first, then Tier 2 supplementary, then broad.
5. Record every result (URL, title, score, published date, raw snippet, retrieval query, sub-question) in a working buffer — these will become `research-sources.json` rows.

### Phase 2 — Source Grading (inline filtering, no tool calls)

Apply grading rules from `references/methodology.md` §"Source grading" (distilled from report §4):

1. **Score threshold:** drop any result with Tavily `score < 0.7` (report §3.1 and §3.4).
2. **Canonical URL dedupe:** collapse near-duplicates (same path ignoring tracking params, same title + same domain).
3. **Domain tier classification:** map each result's domain to Tier 1 / 2 / 3 / 4 using `references/methodology.md` §6. Reject all Tier 4 sources for factual use (they remain usable only as social-signal pointers).
4. **Admiralty A–F reliability score** per domain tier (Tier 1 → A, Tier 2 → B, Tier 3 → C, Tier 4 → D–F).
5. **CRAAP automated checks:** Currency (publication date vs `--since` and vs query recency need), Authority (tier + byline if available). Drop results failing ≥2 CRAAP dimensions.
6. **Unicode domain normalization:** re-normalize any result URL whose host contains non-ASCII; reject mismatches against the allowlist.
7. Keep the top ~10 candidates per sub-question after grading.

### Phase 3 — Precision Rerank (LLM-as-judge)

1. For each sub-question's top-10 candidates, run a structured LLM-as-judge pass (inline, no separate tool). Prompt pattern is documented in `references/methodology.md` §8.3.
2. Grade each on: primary-vs-secondary, author/publisher identified, date relevance, independent verifiability.
3. Select the final top 5–7 per sub-question (standard length) or 8–15 (exhaustive).
4. If a sub-question has fewer than `--min-corroboration` Tier 1/2 sources after rerank, queue a follow-up search (expand `include_domains` to full Tier 1+2 or broaden query terms) before Phase 4. This is the report's "start wide, then narrow" pattern (§2.3).

### Phase 4 — Deep Extract & Synthesis

1. For narrow sub-questions needing multi-step synthesis across sources, delegate to `mcp__tavily__tavily_research` with `model=pro` (exhaustive) or `model=mini` (standard narrow questions). See `references/tool-routing.md` for selection rules.
2. For specific high-value URLs identified during rerank (e.g., a key paper), pull full content with `mcp__tavily__tavily_extract extract_depth=advanced`.
3. **Re-grade late sources.** Any source first surfaced in Phase 4 (cited inside `tavily_research` output, or pulled via `tavily_extract`) must pass the full Phase-2 gate battery (score threshold, tier classification, CRAAP, punycode normalization, dedupe) before it may support any claim. No grading bypass for late-discovered sources.
4. Draft `research-report.md` in working memory following the structure in `references/report-structure.md`:
   - Executive summary (≤5 bullets)
   - One section per sub-question with inline `[^n]` citations
   - Contradictions & open debates section
   - Needs Verification section (single-source or ≤1 Tier 1/2 corroboration)
   - Methodology note (tier profile, source counts, stop conditions triggered)
   - Footnote-style source list (title, publisher, date, URL, Admiralty grade, sub-questions covered)
5. Use surgical quotes only. Never dump raw extract content into the report draft (forbidden, `references/anti-patterns.md`).
6. Draft `research-sources.json` and `research-evidence.json` rows in parallel. Schemas in `references/report-structure.md`. **No artifact file is written in this phase** — all four artifacts are written atomically at the end of Phase 6 (anti-pattern B11).

### Phase 5 — Grounding Validation (CRAG loop, report §5.3)

1. For each claim in `research-report.md`, check: is it traceable to ≥1 URL in `research-sources.json`, and does that source actually support it (not just mention the topic)?
2. Compute metrics from `references/quality-gate.md`:
   - Groundedness rate (% claims with supporting URL)
   - Source quality (% Tier 1/2 among cited sources)
   - Corroboration rate (% claims with ≥`--min-corroboration` independent sources)
   - Freshness (median publication date)
3. If groundedness `< 0.95` or corroboration `< 0.80`, run one CRAG re-query loop: identify the weakest claims, rewrite the query, re-retrieve via `tavily_search`, update the draft. Every source retrieved during a CRAG iteration passes the full Phase-2 gate battery before citation. Max 2 CRAG iterations per failing sub-question AND ≤6 total per run (prioritize sub-questions by ascending groundedness; the runtime table in `references/quality-gate.md` wins on conflict) — if gates still fail, finalize the draft with the failing claims explicitly moved to "Needs Verification".

### Phase 6 — Confidence Annotation

1. Tag every claim with Admiralty credibility 1–6 by applying the normative cascade from `references/methodology.md` §4.1 (verbatim copy — methodology wins on divergence):

   ```
   if   supporting_Tier12 ≥ 2 and contradicting = 0:               → 1 CONFIRMED
   elif supporting_Tier1  ≥ 1 and contradicting = 0:               → 2 PROBABLY TRUE
   elif supporting_Tier12 ≥ 2 and contradicting = 1:               → 2 PROBABLY TRUE
   elif supporting_Tier12 = 1 and contradicting = 0:               → 3 POSSIBLY TRUE
   elif supporting_Tier12 ≥ 1 and contradicting ≥ 1 (Tier-equal):  → 4 DOUBTFUL
   elif contradicting ≥ 2 (Tier 1/2):                              → 5 IMPROBABLE
   else (only Tier 3/4 support, or zero supporting):               → 6 UNVERIFIED
   ```

   Tier 3 sources never change the level (secondary corroborators only, alongside ≥1 Tier 1/2 source).
2. Route by label: credibility 1 may appear anywhere including the executive summary; 2–3 in the main body with inline tags; isolate all 4–6 claims into the "Needs Verification" section.
3. Write all four artifacts atomically to the invocation CWD — this is the first and only artifact write of the run:
   - `research-plan.md` (Phase 0, already approved)
   - `research-report.md` (final synthesis)
   - `research-sources.json` (all cited sources, full schema)
   - `research-evidence.json` (claim → source IDs mapping)

## Output Format

All artifacts written to the invocation CWD.

- **`research-plan.md`** — template at `references/research-plan-template.md`. Produced in Phase 0, approved by user before Phase 1.
- **`research-report.md`** — structure at `references/report-structure.md`. In `--lang` (default: match question language).
- **`research-sources.json`** — array of source records. Schema at `references/report-structure.md` §"Sources schema". Required fields: `id`, `url` (canonical, punycode-normalized), `title`, `publisher`, `published_date`, `accessed_date`, `domain_tier` (1–4), `admiralty_reliability` (A–F), `tavily_score`, `sub_questions` (array), `notes`.
- **`research-evidence.json`** — array of claim records. Schema at `references/report-structure.md` §"Evidence schema". Required fields: `claim_id`, `claim_text`, `supporting_source_ids` (array), `admiralty_credibility` (1–6), `corroboration_count`, `contradicting_source_ids` (array).

## Scope Constraints

- Do NOT run any Tavily call before Phase 0 is approved by the user (non-negotiable, `references/anti-patterns.md`).
- Do NOT fall back to built-in `WebSearch` while any Tavily MCP tool returns successfully. `WebSearch` is a fallback only when Tavily is unreachable (connection error / 5xx). Document every fallback in `research-sources.json` under `notes`.
- Do NOT fabricate URLs or citations. Every `[^n]` must resolve to a record in `research-sources.json`.
- Do NOT cite Tier 4 sources (Reddit, LinkedIn, Medium, Twitter) as primary evidence. They may appear as social-signal pointers in a "Signals" subsection, never as factual support.
- Do NOT dump raw `tavily_extract` content into `research-report.md`. Quotes must be surgical (≤3 sentences) and attributed.
- Do NOT skip the CRAG loop when gates fail. Either re-query or move the failing claim to "Needs Verification".
- Do NOT output unrelated commentary, suggestions for further research beyond the plan, or meta-discussion of the skill's own design. Emit only the four artifacts.
- Any retrieval source beyond the Tavily MCP suite is OPTIONAL. If its MCP server, CLI, or credential is absent or persistently failing, degrade to Tavily-only retrieval, record the degradation in the Methodology note, and surface it in `research-plan.md` at the human gate.
- Do NOT paginate or stream a report while phases are still running. Write artifacts atomically at end of Phase 6.

## Edge Cases

- **Report file missing from CWD.** `references/methodology.md` is the skill-local authoritative copy; proceed using it. Do NOT downgrade methodology discipline.
- **Input question is missing or ambiguous.** Ask the user one clarifying question before Phase 0. If the user confirms ambiguity is intentional (open-ended exploration), classify as `mixed` and decompose across all four sub-question categories.
- **Language mismatch between flag and question.** The flag wins. Translate the question internally but preserve original-language key terms for search queries — proper nouns and domain-specific terminology retrieve better in their source language.
- **User-provided `--domains` conflicts with tier profile.** Union them; never drop user-specified domains. Flag any user-added domain below Tier 2 in `research-plan.md` for confirmation before Phase 1.
- **Tavily returns `score < 0.7` across an entire sub-question.** Do not proceed with low-quality sources. Either broaden the allowlist (add adjacent Tier 1/2 domains), rephrase the sub-question, or mark the sub-question as "Insufficient sources — moved to Needs Verification" in the final report.
- **Tavily research endpoint hits rate limit (20 req/min).** Back off with exponential delay (30s, 60s, 120s) up to 3 retries. If still failing, degrade to `tavily_search` + manual multi-step decomposition for the affected sub-questions.
- **All Tavily tools unreachable.** Halt, report the outage to the user, and ask whether to (a) wait and retry, or (b) proceed with `WebSearch` fallback (with explicit quality-degradation warning appended to every affected source in `research-sources.json`).
- **Paywalled sources (report §11).** Prefer open-access equivalents (PubMed Central, arXiv preprint of a journal paper). If only abstract is retrievable, flag the claim as `admiralty_credibility: 3` unless a second independent source corroborates.
- **Two phases produce contradicting claims from equally authoritative sources.** Do not silently pick one. List both in a "Contradictions & open debates" subsection with each side's evidence. This is explicit report guidance (§1, §5.3 CRAG handling).
- **User asks for a re-run with different flags.** Re-run from Phase 0. Do not reuse prior `research-sources.json` without re-grading — scores and freshness may have shifted.
- **Exhaustive run trending under 100 sources by end of Phase 3.** Expand domain allowlist to full Tier 1+2 union and add 2–4 contextual / recency sub-questions before Phase 4. **One expansion round maximum** — if the run still trends under 100 after it, proceed to Phase 4 and document the shortfall in the Methodology note. The 100-source target is a quality calibration, not a hard contract (report §1 "dozens of searches against hundreds of sources").

## Examples

### Example 1 — Happy path, standard length, English

**Input:** `/deep-research impact of EU AI Act on open-source model providers in 2026`

**Phase 0 output (excerpt from `research-plan.md`, shown to user for approval):**

```markdown
# Research plan: EU AI Act impact on open-source model providers, 2026

**Classification:** mixed (regulatory / technical / current-affairs)
**Tier profile:** current-affairs + technical (Tier 1 gov + Tier 2 tech labs + Tier 2 press)
**Target sources:** 35–60 cited / 50–80 candidates (standard length)

## Sub-questions

1. [factual] What GPAI provisions took effect in 2026 under the EU AI Act? (include_domains: europa.eu, ec.europa.eu, eur-lex.europa.eu)
2. [factual] Which open-source exemptions exist and how are they defined? (include_domains: same + scholar sources)
3. [contextual] How have major open-source model providers (Meta, Mistral, HuggingFace) responded? (include_domains: ai.meta.com, mistral.ai, huggingface.co + Tier 2 press)
4. [contextual] What compliance costs have been reported? (include_domains: Tier 2 press + gartner.com, mckinsey.com)
5. [contradictory] What critiques of the open-source exemption have been published? (broad Tier 2 + Tier 3 press with corroboration)
6. [recency] What enforcement actions or guidance documents were issued since 2026-01-01? (time_range=year, start_date=2026-01-01)

**Estimated Tavily calls:** 24 (6 search + 6 research-mini + 12 extract)
**Pacing:** 2 minutes, well under 20/min rate limit
**Stop conditions:** groundedness ≥ 0.95, corroboration ≥ 0.80 across all sub-questions, ≥2 Tier 1 sources for every factual claim

Proceed? (reply 'approve' or edit the plan)
```

**After user approves**, Phases 1–6 execute. Final `research-report.md` (excerpt):

```markdown
# Impact of the EU AI Act on open-source model providers in 2026

## Executive summary

- GPAI obligations under Articles 53–55 entered application on 2 August 2025, with systemic-risk provisions applying to models above the 10²⁵ FLOPs threshold.[^1][^2]
- The open-source exemption (Article 2(5g)) excludes free and open-source GPAI models from several transparency obligations **unless** they meet the systemic-risk threshold, in which case the exemption does not apply.[^1][^3] [CONFIRMED]
- [...]

## 1. GPAI provisions in force in 2026

Under Article 53 of Regulation (EU) 2024/1689, providers of general-purpose AI models must [...].[^1][^4] The European AI Office published its Code of Practice on 2025-07-10 [...].[^5] [CONFIRMED]

## Contradictions & open debates

The scope of "sufficiently detailed summary" of training data (Article 53(1)(d)) remains disputed. The Commission's July 2025 template[^5] is interpreted by Meta[^6] as [...], while Mozilla[^7] argues [...]. [POSSIBLY TRUE — contested]

## Needs Verification

- Claim that compliance costs exceed €1M for small open-source providers — rests on a single trade-press source[^12] without regulatory corroboration. [UNVERIFIED]

## Sources

[^1]: Regulation (EU) 2024/1689, Official Journal of the EU, 2024-07-12. eur-lex.europa.eu/eli/reg/2024/1689/oj — Tier 1, Admiralty A1
[^2]: European AI Office, "GPAI guidance", 2025-07-18. digital-strategy.ec.europa.eu — Tier 1, A1
[...]
```

### Example 2 — Edge case, exhaustive French run with recency flag

**Input:** `/deep-research --length exhaustive --lang fr --since 2025 comparaison LangGraph / CrewAI / AutoGen / Claude Agent SDK`

**Phase 0 output highlights:**

- Classification: `technical` (developer frameworks)
- Tier profile: technical (Tier 1 docs + Tier 2 engineering blogs + Tier 3 trade press with corroboration)
- Sub-questions: 14 (architecture, runtime model, memory/state, tool-calling, observability, production deployment, community activity, benchmark results, cost model, licensing, contradiction axis on "best for X", recency of 2025 releases)
- `include_domains`: langchain.com, python.langchain.com, github.com/langchain-ai, crewai.com, docs.crewai.com, microsoft.github.io/autogen, github.com/microsoft/autogen, docs.anthropic.com, github.com/anthropics, + Tier 2 press + aclanthology.org for any cited papers
- Target: 100+ cited sources, 200+ candidates
- Estimated Tavily calls: 52, paced across 4 minutes

**After approval**, the run produces a French `research-report.md` with ~110 cited sources. Because `--since 2025` is set, all sources with `published_date < 2025-01-01` are flagged in `research-sources.json` with `notes: "published before --since window, kept for foundational context"` and cannot be the sole support for any time-sensitive claim. Comparative tables per sub-question, one "Contradictions & open debates" section per axis where Tier 1/2 sources disagree, and a "Needs Verification" section for any claim resting on a single Tier 3 source.

## References

Load these on demand — do not read all at Phase 0:

- **`references/methodology.md`** — faithful distillation of `deep-research-report.md`. Read at Phase 0 (decomposition), Phase 2 (grading rules), Phase 5 (gates). **Authoritative for methodology.**
- **`references/tool-routing.md`** — which Tavily tool for which intent. Read at Phase 0 (plan) and any time a tool choice is ambiguous.
- **`references/report-structure.md`** — exact output structure + JSON schemas. Read at Phase 4.
- **`references/quality-gate.md`** — deterministic thresholds and CRAG trigger rules. Read at Phase 5.
- **`references/anti-patterns.md`** — forbidden patterns (skill non-negotiables + report anti-patterns). Consult whenever uncertain.
- **`references/research-plan-template.md`** — exact Phase 0 plan scaffold. Read at Phase 0.
