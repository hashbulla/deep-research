# Phase-0 research plan template

Written to `research-plan.md` at the end of Phase 0. **User must approve before Phase 1 fires.** This file is the approval artifact — it is not overwritten by later phases.

---

```markdown
# Research plan: <question in --lang, ≤ 12 words>

> Generated: YYYY-MM-DD HH:MM · Skill: deep-research · Status: awaiting approval

## 1. Question & scope

**Research question:** <verbatim user question>

**Classification:** <academic | technical | current-affairs | mixed>
**Tier profile:** <academic Tier 1 only | Tier 1+2 technical | Tier 1+2 current-affairs | Tier 1+2 mixed>
**Length:** <short | standard | exhaustive>
**Output language:** <fr | en | ...>
**Recency window:** <--since value or "last 3 years default">
**Min corroboration:** <integer, default 2>
**Model tier:** session model <observed via /model> · synthesis <opus | fable (opt-in, ~2× cost)> · subagent overrides <e.g., grading=sonnet, entailment judge=different Claude model> — see `references/model-tiers.md`. <If `--model fable` but the session runs another model: recommend `/model fable` before approval.>
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

## 5. Expected contradiction axes

<List 1–3 axes where Tier 1/2 sources are likely to disagree. These guide Phase-1 query formulation for sub-questions of category "contradictory". Example: "cost estimates (industry self-report vs independent study)", "scope of exemption (commission interpretation vs member state transposition)".>

## 6. Stop conditions

Successful completion requires **all** of:

- [ ] Groundedness ≥ 0.95
- [ ] Source quality ≥ 0.80 Tier 1/2
- [ ] Coverage ≥ 0.90 of sub-questions
- [ ] Corroboration rate ≥ 0.80
- [ ] Source-count floor: <length-specific minimum>
- [ ] Zero pending CRAG iterations

Failure to meet any gate routes affected claims to "Needs Verification" and documents the gap in the Methodology note.

## 7. Known gaps at planning time

<e.g., "No full-text academic search available (Exa / Valyu not in MCP stack); mitigated by Tier 1 academic `include_domains`. Any paywalled commercial journals will contribute abstracts only.">
<e.g., "No integrated NewsGuard / MBFC rating; Tier-4 detection relies on domain tier registry only.">

## 8. Artifacts

At Phase 6 the skill will emit:

- `research-plan.md` (this file — approved)
- `research-report.md` (final synthesis, in <--lang>)
- `research-sources.json` (all cited sources, Admiralty-graded)
- `research-evidence.json` (claim → sources mapping with credibility)

---

**Approve this plan to proceed to Phase 1.**
Reply `approve` to run as-specified, or edit any section above and re-send.
```
