# Quality gates — deterministic thresholds

Applied at the end of Phase 4 (Synthesis) and Phase 5 (Grounding Validation). Every gate is a hard threshold; falling below triggers a specific action. Do not relax these silently. If a gate cannot be met after max CRAG iterations, explicitly document the failure in the Methodology note and move affected claims to "Needs Verification".

## Rigor profiles

Two profiles scale verification depth to the run's stakes. The default keeps the everyday research instrument fast; the critical profile carries the zero-fault discipline for confidential / high-stakes corpora.

| | `standard` (default) | `critical` (implied by `--confidential`, or `--rigor critical`) |
|---|---|---|
| Gates below | All apply | All apply |
| Entailment judge (decorrelated subagent, different Claude model, claim + cited span only — no scratch context) | Executive-summary claims + every single-source claim | **Every claim** |
| Unsourced assertion (zero supporting sources) | Credibility 6 → "Needs Verification" | **Refuse-if-no-source**: the assertion is removed; the report states "no sourced answer available" — never a parametric-knowledge fallback |
| `anchor` field on claims (`research-evidence.json`) | Optional (recommended for executive-summary claims) | **Required on every claim** — `verbatim_quote` for web sources, `snapshot_char_range` (+ snapshot SHA-256) for persisted corpus documents; verified by `scripts/verify_gates.py check-artifacts --rigor critical` |
| Sycophancy / false-premise probe | — | Phase 0 verifies the question's presuppositions against Tier 1/2 sources; an unsupported premise is surfaced at the human gate instead of researched |
| Contradiction critic | Contradictions section per SKILL.md | Dedicated critic pass re-scans the draft for smoothed-over disagreements before Phase 6 |
| Subagent content policy | Condensed findings + references | **Neutral references only** — no confidential text ever enters a subagent prompt, log, or MCP call |

## Phase-2 filter gates (per individual source)

These gates apply to **every** source regardless of when it is discovered — Phase 1 broad retrieval, Phase 4 (`tavily_research` citations, `tavily_extract` pulls), or Phase 5 CRAG re-queries. A source first seen after Phase 2 repasses the full battery before it may support any claim.

| Gate | Threshold | Action on failure |
|---|---|---|
| Tavily `score` | `> 0.7` | Drop source |
| Domain tier | `≥ Tier 2` (factual use, primary claim support); Tier 3 admissible only when a corroborating Tier 1/2 source exists; Tier 4 → Signals subsection only | Drop if no corroborating Tier 1/2 source; Tier 4 kept only as "Signals" |
| CRAAP Currency | Publication date within `--since` window (or within 3 years if not set) for time-sensitive sub-questions | Drop for time-sensitive sub-questions; keep for background |
| CRAAP Authority | Domain tier identifiable AND publisher metadata present | Drop if both absent |
| Duplicate canonical URL | `url_canonical` not already in working set | Drop duplicate, merge `sub_questions` array |
| Unicode domain normalization | When an `include_domains` allowlist is active for the call: normalized (punycode) host matches an allowlist entry. When no allowlist is active (broad discovery): any host containing non-ASCII is normalized; reject if the normalized form mimics a known domain (homograph) | Reject source; log as potential homograph spoof |

## Phase-3 rerank gates (per sub-question)

| Gate | Threshold | Action on failure |
|---|---|---|
| Top-5 candidates present | ≥ 5 candidates passed Phase-2 | Broaden `include_domains` → re-run Phase 1 for this sub-question |
| Tier 1/2 share of top 5 | ≥ 60% | Re-rank with stricter authority weight; re-run Phase 1 if still failing |
| Primary-vs-secondary split | ≥ 1 primary source among top 5 (for factual sub-questions) | Add a targeted `tavily_search` with `include_domains` narrowed to Tier 1 primary domains |
| Author-identified share | ≥ 40% (for technical / academic profile) | Flag sub-question for extra corroboration in Phase 5 |

## Phase-5 whole-report gates (CRAG trigger)

| Gate | Threshold | Action on failure |
|---|---|---|
| **Groundedness rate** | ≥ 0.95 (% claims traceable to a supporting source URL that actually supports the claim) | CRAG iteration: rewrite query for failing claims, `tavily_search` supplement, update claims or move to Needs Verification |
| **Source quality** | ≥ 0.80 of cited sources are Tier 1 or Tier 2 | Expand allowlist to Tier 1+2 union, re-run affected sub-questions |
| **Coverage** | ≥ 0.90 of planned sub-questions answered with ≥1 Tier 1/2 source | Add a follow-up sub-question per gap, re-run Phase 1 for it |
| **Freshness** | Median source `published_date` within `--since` window, or within 3 years if no `--since` | Add a recency sub-question with `time_range=year` or `start_date=<--since>` |
| **Corroboration rate** | ≥ 0.80 of claims have ≥ `--min-corroboration` (default 2) independent Tier 1/2 supporting sources | CRAG iteration; then move uncorroborated claims to Needs Verification |

**Max CRAG iterations:** 2 per failing sub-question / gate AND **≤6 total per run**, prioritized by ascending groundedness (weakest sub-questions first). The runtime gates below take precedence on conflict. After the caps are hit, halt CRAG and document the residual failure in the Methodology note.

## Length-specific source-count gates

| `--length` | Final cited sources | Failure action |
|---|---|---|
| short | 15–25 | If < 15: add 1–2 sub-questions, re-run Phase 1 |
| standard | 35–60 | If < 35: broaden allowlist + 2 sub-questions |
| **exhaustive** | **≥ 100** | If < 100 at end of Phase 3: run **one** expansion round (add 2–4 contextual + recency sub-questions, broaden allowlist to full Tier 1+2 union, re-run Phase 1). If still < 100 after that round, proceed to Phase 4 and document the shortfall in the Methodology note — the 100+ target is calibration, not a hard contract. |

## Tavily pacing gates

| Gate | Threshold | Action on failure |
|---|---|---|
| Research endpoint rate | ≤ 15 calls / 60s (rolling) | Stagger subsequent research calls; degrade to `tavily_search` if persistent |
| 429 response | 3 consecutive on same tool | Backoff 30 → 60 → 120s; then hard-degrade affected sub-questions |
| Total runtime | `short` ≤ 2min, `standard` ≤ 5min, `exhaustive` ≤ 15min | Warn user; offer to truncate CRAG iterations |

## Confidence-tag assignment rules (Phase 6)

Applied deterministically to every claim. **The normative algorithm lives in `references/methodology.md §4.1`; the block below is a verbatim copy — methodology wins on any divergence (invariant I3).**

**Derivation of the counters below.** The three counters are computed at assignment time; they are **not** stored fields of `research-evidence.json`. For a given claim record, join its `supporting_source_ids` and `contradicting_source_ids` arrays against `research-sources.json` by `id` to resolve each referenced source's `domain_tier`. The persisted fields in `research-evidence.json` — `corroboration_count`, `independent_tier12_count`, `primary_source_present` — are described in `references/report-structure.md §4`.

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

**Tier 3 rule:** Tier 3 sources never change the credibility level; admissible as secondary corroborators only when ≥1 supporting Tier 1/2 source exists. A claim supported only by Tier 3/4 sources is credibility 6.

**Routing:** claims with labels 4, 5, 6 **must** be in the "Needs Verification" section. Claims with labels 1, 2, 3 may appear in the main body; labels 2 and 3 carry their Admiralty tag inline and never appear in the executive summary (CONFIRMED only).

## Stop conditions (successful completion)

All of:
- Groundedness ≥ 0.95
- Source quality ≥ 0.80 Tier 1/2
- Coverage ≥ 0.90
- Corroboration rate ≥ 0.80
- Length-specific source-count floor met
- Zero CRAG iteration currently pending

Failure to meet any gate does not abort the skill — it routes affected claims to "Needs Verification" and documents the gap in the Methodology note.
