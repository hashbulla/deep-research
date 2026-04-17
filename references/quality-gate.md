# Quality gates — deterministic thresholds

Applied at the end of Phase 4 (Synthesis) and Phase 5 (Grounding Validation). Every gate is a hard threshold; falling below triggers a specific action. Do not relax these silently. If a gate cannot be met after max CRAG iterations, explicitly document the failure in the Methodology note and move affected claims to "Needs Verification".

## Phase-2 filter gates (per individual source)

| Gate | Threshold | Action on failure |
|---|---|---|
| Tavily `score` | `> 0.7` | Drop source |
| Domain tier | `≥ Tier 3` (factual use) / `≥ Tier 2` (primary claim support) | Drop for factual use, keep only as "Signals" for Tier 4 |
| CRAAP Currency | Publication date within `--since` window (or within 3 years if not set) for time-sensitive sub-questions | Drop for time-sensitive sub-questions; keep for background |
| CRAAP Authority | Domain tier identifiable AND publisher metadata present | Drop if both absent |
| Duplicate canonical URL | `url_canonical` not already in working set | Drop duplicate, merge `sub_questions` array |
| Unicode domain normalization | Host punycode matches an entry in `include_domains` after normalization | Reject source; log as potential homograph spoof |

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

**Max CRAG iterations:** 2 per failing sub-question / gate. After 2 failures, halt CRAG and document the residual failure in the Methodology note.

## Length-specific source-count gates

| `--length` | Final cited sources | Failure action |
|---|---|---|
| short | 15–25 | If < 15: add 1–2 sub-questions, re-run Phase 1 |
| standard | 35–60 | If < 35: broaden allowlist + 2 sub-questions |
| **exhaustive** | **≥ 100** | If < 100 at end of Phase 3: add 2–4 sub-questions (contextual + recency) + broaden allowlist → re-run Phase 1. Do not proceed to Phase 4 below this threshold. |

## Tavily pacing gates

| Gate | Threshold | Action on failure |
|---|---|---|
| Research endpoint rate | ≤ 15 calls / 60s (rolling) | Stagger subsequent research calls; degrade to `tavily_search` if persistent |
| 429 response | 3 consecutive on same tool | Backoff 30 → 60 → 120s; then hard-degrade affected sub-questions |
| Total runtime | `short` ≤ 2min, `standard` ≤ 5min, `exhaustive` ≤ 15min | Warn user; offer to truncate CRAG iterations |

## Confidence-tag assignment rules (Phase 6)

Applied deterministically to every claim:

```
supporting_Tier12 = count of distinct supporting sources with domain_tier ∈ {1, 2}
supporting_Tier1  = count of distinct supporting sources with domain_tier = 1
contradicting    = count of distinct contradicting sources with domain_tier ∈ {1, 2}

if supporting_Tier12 ≥ 2 and contradicting = 0:                → 1 CONFIRMED
elif supporting_Tier1 ≥ 1 and contradicting = 0:                → 2 PROBABLY TRUE
elif supporting_Tier12 ≥ 2 and contradicting = 1:                → 2 PROBABLY TRUE
elif supporting_Tier12 = 1 and contradicting = 0:                → 3 POSSIBLY TRUE
elif supporting_Tier12 ≥ 1 and contradicting ≥ 1 (Tier-equal):  → 4 DOUBTFUL
elif contradicting ≥ 2 (Tier 1/2):                                → 5 IMPROBABLE
else (only Tier 3/4, or zero supporting):                        → 6 UNVERIFIED
```

Claims with labels 4, 5, 6 **must** be in the "Needs Verification" section. Claims with labels 1, 2, 3 may appear in the main body; labels 2 and 3 carry their Admiralty tag inline.

## Stop conditions (successful completion)

All of:
- Groundedness ≥ 0.95
- Source quality ≥ 0.80 Tier 1/2
- Coverage ≥ 0.90
- Corroboration rate ≥ 0.80
- Length-specific source-count floor met
- Zero CRAG iteration currently pending

Failure to meet any gate does not abort the skill — it routes affected claims to "Needs Verification" and documents the gap in the Methodology note.
