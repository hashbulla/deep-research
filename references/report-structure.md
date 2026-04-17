# Report structure & output schemas

All filenames below are relative to the invocation CWD. Write artifacts atomically at end of Phase 6. Do not emit partial reports during intermediate phases.

## 1. `research-report.md`

```markdown
# <Title derived from research question, in --lang>

> Research date: YYYY-MM-DD · Skill: deep-research · Length: <short|standard|exhaustive>
> Source count: <cited>/<candidates> · Tier 1/2 share: <pct> · Median source date: <YYYY-MM-DD>
> Classification: <academic|technical|current-affairs|mixed> · Profile: <profile>

## Executive summary

- <≤5 bullets, each ≤2 sentences, each with ≥1 citation>
- <bullets are CONFIRMED claims only — any PROBABLY TRUE / POSSIBLY TRUE belongs in the body>

## <Section per sub-question — numbered and titled>

<Prose with inline [^n] footnote citations. Surgical quotes only (≤3 sentences). Each claim carries an Admiralty confidence tag where non-obvious: [CONFIRMED] / [PROBABLY TRUE] / [POSSIBLY TRUE]. Claims tagged [DOUBTFUL] / [IMPROBABLE] / [UNVERIFIED] do NOT appear in these sections — they belong in "Needs Verification".>

## Contradictions & open debates

<One subsection per axis where Tier 1/2 sources disagree. Each side's evidence cited inline. End with the current best-supported position or explicit "unresolved".>

## Needs Verification

<Claims that failed the corroboration gate (credibility 4–6). Each item lists: the claim, why it is unverified, what additional source type would resolve it.>

## Methodology note

- Tier profile: <profile>, domain allowlist size: <n>
- Sub-questions: <n>
- Tavily calls: <n search> + <n research> + <n extract> + <n map> + <n crawl>
- CRAG iterations triggered: <n> (on sub-questions <…>)
- Quality gates: groundedness <pct>, source quality <pct>, coverage <pct>, freshness <median date>, corroboration rate <pct>
- Known gaps: <list, if any — e.g., "no full-text academic search; coverage limited to abstracts for commercial journals">

## Sources

[^1]: <Title>, <Publisher>, <YYYY-MM-DD>. <URL> — Tier <n>, Admiralty <X><digit>, sub-questions: <list>
[^2]: ...
```

### Tone rules
- Match `--lang`. Preserve original-language key terms when they are proper nouns (legislation names, institution names, paper titles).
- No hedging filler ("it seems that", "possibly" — if the claim is possibly true, tag it `[POSSIBLY TRUE]` explicitly rather than softening prose).
- No first-person ("I found…"). The report speaks as an analyst, not a narrator.
- No meta-commentary about the skill's own process beyond the Methodology note.

## 2. `research-plan.md`

Full template at `references/research-plan-template.md`. Produced at Phase 0. **Not overwritten by later phases** — it is the approval artifact.

## 3. `research-sources.json`

Array of source records. One record per cited URL.

```json
[
  {
    "id": "S001",
    "url": "https://eur-lex.europa.eu/eli/reg/2024/1689/oj",
    "url_canonical": "eur-lex.europa.eu/eli/reg/2024/1689/oj",
    "url_punycode": "eur-lex.europa.eu/eli/reg/2024/1689/oj",
    "title": "Regulation (EU) 2024/1689 of the European Parliament...",
    "publisher": "Official Journal of the European Union",
    "author": null,
    "published_date": "2024-07-12",
    "accessed_date": "2026-04-17",
    "domain_tier": 1,
    "admiralty_reliability": "A",
    "tavily_score": 0.94,
    "retrieval_tool": "tavily_search",
    "retrieval_query": "EU AI Act GPAI provisions 2026 official journal",
    "sub_questions": ["sq1", "sq2"],
    "primary_source": true,
    "notes": ""
  }
]
```

### Required fields
- `id` — sequential `S001`, `S002`…
- `url` — as retrieved from Tavily.
- `url_canonical` — lowercased, tracking params stripped.
- `url_punycode` — host normalized to punycode (defense against homograph spoofing).
- `title`
- `publisher` — derived from domain + Tavily metadata.
- `author` — if extractable from byline, else `null`.
- `published_date` — ISO 8601; `null` only if genuinely absent.
- `accessed_date` — ISO 8601 (today).
- `domain_tier` — integer 1–4.
- `admiralty_reliability` — one of `A`, `B`, `C`, `D`, `E`, `F`.
- `tavily_score` — float 0–1.
- `retrieval_tool` — which `mcp__tavily__*` surfaced this result (or `WebSearch` on fallback).
- `retrieval_query` — exact query string used.
- `sub_questions` — array of sub-question IDs referenced in the plan.
- `primary_source` — boolean. True for original research / regulation / dataset; false for commentary or summary.
- `notes` — free text. Always populated on `WebSearch` fallback or on any deviation (paywall, abstract-only, corroboration incomplete, etc.).

## 4. `research-evidence.json`

Array of claim records. One record per distinct factual claim in `research-report.md`.

```json
[
  {
    "claim_id": "C001",
    "claim_text": "GPAI obligations under Articles 53–55 entered application on 2 August 2025.",
    "section": "1. GPAI provisions in force in 2026",
    "supporting_source_ids": ["S001", "S002"],
    "contradicting_source_ids": [],
    "admiralty_credibility": 1,
    "label": "CONFIRMED",
    "corroboration_count": 2,
    "independent_tier12_count": 2,
    "primary_source_present": true,
    "notes": ""
  }
]
```

### Required fields
- `claim_id` — sequential `C001`, `C002`…
- `claim_text` — verbatim sentence or compact paraphrase.
- `section` — section heading in `research-report.md` where the claim appears.
- `supporting_source_ids` — array of `research-sources.json` IDs.
- `contradicting_source_ids` — array of source IDs whose content disagrees with the claim.
- `admiralty_credibility` — integer 1–6.
- `label` — `CONFIRMED` / `PROBABLY TRUE` / `POSSIBLY TRUE` / `DOUBTFUL` / `IMPROBABLE` / `UNVERIFIED`.
- `corroboration_count` — integer. Count of distinct independent sources supporting the claim.
- `independent_tier12_count` — integer. Count restricted to Tier 1/2 sources.
- `primary_source_present` — boolean. True if ≥1 supporting source has `primary_source: true`.
- `notes` — free text (e.g., "paywalled source, abstract only", "CRAG iteration 1 added S042").

## Validation rules (emitter self-check before write)

- Every `[^n]` in `research-report.md` resolves to a `research-sources.json` record.
- Every `research-sources.json` record with `primary_source: true` has `domain_tier ≤ 2`.
- No `research-evidence.json` claim with `admiralty_credibility ≤ 3` is absent from the main report body (should appear in its sub-question section).
- No `research-evidence.json` claim with `admiralty_credibility ≥ 4` appears in the main body — all must be under "Needs Verification".
- Median `published_date` of cited sources is within `--since` (if set) or within the last 3 years (if not set).
- `research-sources.json` contains no record with `tavily_score < 0.7` (unless the record is tagged in `notes` as a recency-critical Tier 1 source manually retained).
