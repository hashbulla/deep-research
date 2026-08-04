# Phase-0 research plan template

Written to `research-plan.md` at the end of Phase 0, before Phase 1 retrieval. This is the run's planning artifact (artifact #1) — it is not overwritten by later phases. There is no approval halt: Phase 0 proceeds autonomously unless the pre-flight ambiguity-signal checklist (`references/methodology.md` §9) fired a clarifying `AskUserQuestion` round.

---

```markdown
# Research plan: <question in --lang, ≤ 12 words>

> Generated: YYYY-MM-DD HH:MM · Skill: deep-research · Status: planned — proceeding to Phase 1

## 1. Question & scope

**Research question:** <verbatim user question>

**Classification:** <academic | technical | current-affairs | mixed>
**Tier profile:** <academic Tier 1 only | Tier 1+2 technical | Tier 1+2 current-affairs | Tier 1+2 mixed>
**Length:** <short | standard | exhaustive>
**Output language:** <fr | en | ...>
**Recency window:** <--since value or "last 3 years default">
**Min corroboration:** <integer, default 2>
**Model tier:** session model <observed via /model> · synthesis <opus | fable (opt-in, ~2× cost)> · subagent overrides <e.g., grading=sonnet, entailment judge=different Claude model> — see `references/model-tiers.md`. <If `--model fable` but the session runs another model: recommend `/model fable` before Phase 1.>
**Confidential path:** <yes — subagents receive neutral references only, rigor=critical | no>

## 2. Sub-question decomposition

| ID | Category | Sub-question | Tavily tool | include_domains (preview) | time_range / start_date | Target candidates |
|---|---|---|---|---|---|---|
| sq1 | factual | <what / when / who question> | tavily_search | <domains> | <if recency> | 10 |
| sq2 | factual | <...> | tavily_search | <domains> | | 10 |
| sq3 | contextual | <why / how / implications> | tavily_search | <domains> | | 10 |
| sq4 | contextual | <...> | tavily_search | <domains> | | 10 |
| sq5 | contradictory | <alternative perspective> | tavily_search | <domains broader> | | 10 |
| sq6 | recency | <what changed since X> | tavily_search | <domains> | time_range=year, start_date=<YYYY-MM-DD> | 10 |
| sqN | ... | ... | tavily_research mini/pro | ... | | ... |

<Sub-question count by --length:
  short      → 3–5
  standard   → 6–10
  exhaustive → 12–20>

## 3. Domain allowlist / blocklist

**Baseline from tier profile:** <list the concrete domains — first 30 tokens, then "…+N more">

**User `--domains` additions:** <list, or "none">
**User `--exclude` additions:** <list, or "none">

**Flagged user additions below Tier 2** (confirm before Phase 1):
<list any --domains entries below Tier 2, or "none">

**Credibility overlay (MBFC static, user-scope):** <"active, dataset_version YYYY-MM-DD — allowlisted domains flagged/downgraded by the overlay: <list, or none>" | "dataset absent — overlay skipped">

## 4. Retrieval plan

**Phase 1 (broad recall):**
- <N> parallel `tavily_search` calls (advanced depth)
- <M> `tavily_map` calls (if any sub-question needs domain-structure discovery)

**Conditional sources (declared here, or "none"):**
- Context7: <library_id@version per gated sub-question, e.g. "/vercel/next.js@15 (sq3)" — only when the technical-profile + named-dependency + integrate/configure/debug/migrate/understand gating passes; availability status; or "not applicable">
- Newsletter-signal: <buckets + sub-questions consulted, e.g. "ai-engineering (sq2, sq4)" — only when the topic is work-relevant and `~/.claude/deep-research/newsletter-corpus/` exists; routing signal only, never cited; corpus availability status; or "not applicable">
- <other optional sources, with availability status and Tavily degradation noted if unavailable>

**Phase 4 (deep extract & synthesis):**
- <K> `tavily_research model=mini|pro` calls
- <L> `tavily_extract extract_depth=advanced` calls on key URLs

**Estimated total Tavily calls:** <N+M+K+L>
**Estimated runtime:** <minutes, paced under 15 research/min>
**Rate-limit headroom:** <calls/min peak>

## 5. Solution-space sweep plan

**Geometry:** solution space applicable = <true | false> — <reason in one sentence: does the question admit "what tool or approach solves this?">
**Platforms in scope:** <e.g. "YouTube, Instagram" — or "none (platform-independent question)">

| Category | Planned status | Planned queries / registries | Notes |
|---|---|---|---|
| own-stack | <swept \| degraded> | `scripts/stack_inventory.py` grep terms over <configured paths, or "config absent → degraded"> | **Runs FIRST, before any web call.** Zero network, full breadth at every `--length`, never waived for cost. |
| platform-official-api | <swept \| empty \| waived> | <official API / developer-docs queries per platform> | |
| mcp-registries | <swept \| empty \| waived> | <which of the named registries in `references/solution-space.md` will be queried> | The registries actually queried are listed by name in the manifest. |
| open-source | <swept \| empty \| waived> | <capability-class queries + package registries> | Reuses `references/github-research.md`. |
| commercial-vendors | <swept \| empty \| waived> | <capability-class vendor vocabulary, one pass per risk class> | Every risk class enumerated, including a class gated NO-GO. |
| substitution-channels | <swept \| empty \| waived> | <adjacent-modality queries: what else delivers the same outcome> | |

**Sweep order:** own-stack (local, deterministic) → then the five web categories, seeded with the vocabulary the stack sweep surfaced.
**Sweep scale for `--length <short\|standard\|exhaustive>`:** <4–6 | 6–12 | 12–20> web queries spread **across** the five web categories.
**Control queries:** any category planned `empty` names its control query and the known-present item it must return.

<When applicable = false, this section is still emitted: state the geometry, its reason, and mark all six categories `not-applicable` with that reason — `not-applicable` is reserved for this whole-question case and is never a per-category opt-out on an applicable question (that is `waived`, with a real reason). The manifest is universal; the completeness critic still runs, and challenges the declaration itself.>

## 6. Expected contradiction axes

<List 1–3 axes where Tier 1/2 sources are likely to disagree. These guide Phase-1 query formulation for sub-questions of category "contradictory". Example: "cost estimates (industry self-report vs independent study)", "scope of exemption (commission interpretation vs member state transposition)".>

## 7. Stop conditions

Successful completion requires **all** of:

- [ ] Groundedness ≥ 0.95
- [ ] Source quality ≥ 0.80 Tier 1/2
- [ ] Coverage ≥ 0.90 of sub-questions
- [ ] Corroboration rate ≥ 0.80
- [ ] Source-count floor: <length-specific minimum>
- [ ] Zero pending CRAG iterations

Failure to meet any gate routes affected claims to "Needs Verification" and documents the gap in the Methodology note.

## 8. Known gaps at planning time

<e.g., "No full-text academic search available (Exa / Valyu not in MCP stack); mitigated by Tier 1 academic `include_domains`. Any paywalled commercial journals will contribute abstracts only.">
<e.g., "No integrated NewsGuard / MBFC rating; Tier-4 detection relies on domain tier registry only.">

## 9. Artifacts

At Phase 6 the skill will emit:

- `research-plan.md` (this file)
- `research-report.md` (final synthesis, in <--lang>)
- `research-sources.json` (all cited sources, Admiralty-graded)
- `research-evidence.json` (claim → sources mapping with credibility)
- `research-solution-space.json` (solution-space manifest — 6 categories, declared incompleteness, critic block)

Plus a private Artifact page rendering the report, the solution-space benchmark and the gate verdicts (skipped on `--confidential`, or when the Artifact tool is absent).

---

*This plan is the run's first artifact; Phase 0 proceeds to Phase 1 automatically. It pauses only when the pre-flight ambiguity-signal checklist (`references/methodology.md` §9) fires a clarifying `AskUserQuestion` round — otherwise the run is fully autonomous.*
```
