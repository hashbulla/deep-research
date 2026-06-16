# Worked examples

> Read on demand — typically when composing a Phase-0 plan for the first time in a session. Moved out of SKILL.md to keep the always-loaded tier under budget. A complete end-to-end artifact set (short run, gate-conformant, CI-validated) lives in `../examples/eu-ai-act-2026/`.

## Example 1 — Happy path, standard length, English

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

**Once the plan is written**, Phases 1–6 execute autonomously. Final `research-report.md` (excerpt):

```markdown
# Impact of the EU AI Act on open-source model providers in 2026

## Executive summary

- GPAI obligations under Articles 53–55 entered application on 2 August 2025, with systemic-risk provisions applying to models above the 10²⁵ FLOPs threshold.[^1][^2] [CONFIRMED]
- The open-source exemption (Article 2(5g)) excludes free and open-source GPAI models from several transparency obligations **unless** they meet the systemic-risk threshold, in which case the exemption does not apply.[^1][^3] [CONFIRMED]
- [...]

## 1. GPAI provisions in force in 2026

Under Article 53 of Regulation (EU) 2024/1689, providers of general-purpose AI models must [...].[^1][^4] The European AI Office published its Code of Practice on 2025-07-10 [...].[^5] [CONFIRMED]

## Contradictions & open debates

The scope of "sufficiently detailed summary" of training data (Article 53(1)(d)) remains disputed. The Commission's July 2025 template[^5] is interpreted by Meta[^6] as [...], while Mozilla[^7] argues [...]. [CONFIRMED — the dispute itself; the competing readings remain unresolved]

## Needs Verification

- Claim that compliance costs exceed €1M for small open-source providers — rests on a single trade-press source[^12] without regulatory corroboration. [UNVERIFIED]

## Sources

[^1]: Regulation (EU) 2024/1689, Official Journal of the EU, 2024-07-12. eur-lex.europa.eu/eli/reg/2024/1689/oj — Tier 1, Admiralty A1
[^2]: European AI Office, "GPAI guidance", 2025-07-18. digital-strategy.ec.europa.eu — Tier 1, A1
[...]
```

Phase 6 closes with the mandatory deterministic verification, quoted in the final chat message:

```bash
python3 <skill-dir>/scripts/verify_gates.py check-artifacts \
  --sources research-sources.json --evidence research-evidence.json --length standard
# → {"verdict": "PASS", ...}
```

## Example 2 — Edge case, exhaustive French run with recency flag

**Input:** `/deep-research --length exhaustive --lang fr --since 2025 comparaison LangGraph / CrewAI / AutoGen / Claude Agent SDK`

**Phase 0 output highlights:**

- Classification: `technical` (developer frameworks)
- Tier profile: technical (Tier 1 docs + Tier 2 engineering blogs + Tier 3 trade press with corroboration)
- Sub-questions: 14 (architecture, runtime model, memory/state, tool-calling, observability, production deployment, community activity, benchmark results, cost model, licensing, contradiction axis on "best for X", recency of 2025 releases)
- `include_domains`: langchain.com, python.langchain.com, github.com/langchain-ai, crewai.com, docs.crewai.com, microsoft.github.io/autogen, github.com/microsoft/autogen, docs.anthropic.com, github.com/anthropics, + Tier 2 press + aclanthology.org for any cited papers
- Target: 100+ cited sources, 200+ candidates
- Estimated Tavily calls: 52, paced across 4 minutes

**After approval**, the run produces a French `research-report.md` with ~110 cited sources. Because `--since 2025` is set, all sources with `published_date < 2025-01-01` are flagged in `research-sources.json` with `notes: "published before --since window, kept for foundational context"` and cannot be the sole support for any time-sensitive claim. Comparative tables per sub-question, one "Contradictions & open debates" section per axis where Tier 1/2 sources disagree, and a "Needs Verification" section for any claim resting on a single Tier 3 source. If the run trends under 100 sources at the end of Phase 3, exactly one expansion round fires (allowlist broadened to the full Tier 1+2 union, 2–4 sub-questions added); a residual shortfall is documented in the Methodology note, never silently absorbed.
