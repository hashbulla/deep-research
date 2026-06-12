# Research plan: EU AI Act impact on open-source model providers, 2026

> Generated: 2026-04-17 10:22 · Skill: deep-research · Status: approved (illustrative example)

## 1. Question & scope

**Research question:** impact of EU AI Act on open-source model providers in 2026

**Classification:** mixed (regulatory / technical / current-affairs)
**Tier profile:** current-affairs + technical — Tier 1 gov + Tier 2 tech labs + Tier 2 press
**Length:** short
**Output language:** en (inferred from question)
**Recency window:** last 3 years (default — no `--since` provided)
**Min corroboration:** 2 (default)

## 2. Sub-question decomposition

| ID | Category | Sub-question | Tavily tool | include_domains (preview) | time_range / start_date | Target candidates |
|---|---|---|---|---|---|---|
| sq1 | factual | What GPAI provisions took effect under the EU AI Act and what do they require? | tavily_search | europa.eu, ec.europa.eu, eur-lex.europa.eu, digital-strategy.ec.europa.eu | — | 8 |
| sq2 | factual | Which open-source exemptions exist and how are they defined (Article 2(5g))? | tavily_search | eur-lex.europa.eu, ec.europa.eu, oecd.org | — | 8 |
| sq3 | contextual | How have major open-source model providers (Meta, Mistral, HuggingFace) responded? | tavily_search | ai.meta.com, mistral.ai, huggingface.co + reuters.com, apnews.com, ft.com | — | 8 |
| sq4 | contradictory | What critiques and cost concerns about the open-source exemption have been published? | tavily_search | mozilla.org, oecd.org + Tier 2/3 press with corroboration | — | 8 |
| sq5 | recency | What enforcement actions or guidance documents were issued since 2026-01-01? | tavily_search | digital-strategy.ec.europa.eu, ec.europa.eu, europarl.europa.eu | time_range=year, start_date=2026-01-01 | 8 |

## 3. Domain allowlist / blocklist

**Baseline from tier profile:** eur-lex.europa.eu, europa.eu, ec.europa.eu, digital-strategy.ec.europa.eu, europarl.europa.eu, oecd.org, *.gov, ai.meta.com, mistral.ai, huggingface.co, anthropic.com, reuters.com, apnews.com, ft.com, economist.com, theguardian.com, lemonde.fr, gartner.com, mckinsey.com, mozilla.org …+10 more.

**User `--domains` additions:** none
**User `--exclude` additions:** none

**Flagged user additions below Tier 2** (confirm before Phase 1): none

## 4. Retrieval plan

**Phase 1 (broad recall):**
- 5 parallel `tavily_search` calls (advanced depth, include_raw_content=true, max_results=8)
- 0 `tavily_map` calls (not required for this question)

**Phase 4 (deep extract & synthesis):**
- 3 `tavily_research model=mini` calls (narrow synthesis on sq1, sq4, sq5)
- 6 `tavily_extract extract_depth=advanced` calls on high-value URLs surfaced during rerank (OJ regulation text, Code of Practice, EPRS enforcement briefing, OECD comparative note, key press analyses)

**Estimated total Tavily calls:** 14 (5 search + 3 research-mini + 6 extract)
**Estimated runtime:** ~90 seconds
**Rate-limit headroom:** peak 8 calls/min; well under 20 req/min research-endpoint ceiling

## 5. Expected contradiction axes

- **Scope of "sufficiently detailed summary" of training data** (Article 53(1)(d)) — Commission's July 2025 template interpretation (ec.europa.eu) vs provider interpretation (ai.meta.com) vs civil-society interpretation (mozilla.org).
- **Whether the Article 2(5g) open-source exemption meaningfully reduces compliance burden** — industry positive framing vs independent-study cost estimates.

## 6. Stop conditions

Successful completion requires **all** of:

- [ ] Groundedness ≥ 0.95
- [ ] Source quality ≥ 0.80 Tier 1/2
- [ ] Coverage ≥ 0.90 of sub-questions
- [ ] Corroboration rate ≥ 0.80
- [ ] Source-count floor: 15 (short length)
- [ ] Zero pending CRAG iterations

Failure to meet any gate routes affected claims to "Needs Verification" and documents the gap in the Methodology note.

## 7. Known gaps at planning time

- No full-text academic search available (Exa / Valyu not in MCP stack); mitigated by Tier 1 academic `include_domains`. Commercial journals will contribute abstracts only.
- Some national-transposition sources are in languages other than English (e.g., French, German); Tavily will return them but Phase-3 rerank may under-weight them relative to English Tier-1 EU-level sources. Flag in Methodology note if material.

## 8. Artifacts

At Phase 6 the skill will emit:

- `research-plan.md` (this file — approved)
- `research-report.md` (final synthesis, in en)
- `research-sources.json` (all cited sources, Admiralty-graded)
- `research-evidence.json` (claim → sources mapping with credibility)

---

**Approve this plan to proceed to Phase 1.**
Reply `approve` to run as-specified, or edit any section above and re-send.
