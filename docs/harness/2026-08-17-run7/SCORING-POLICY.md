# Run #7 — scoring policy, pre-registered before the data exists

> Written 2026-08-17T16:5xZ, **before** `run_evals.py --models opus,sonnet,haiku` was launched.
> Purpose: the checkpoint that opened this session warns that the *reading* of this matrix is the
> judgment, and that this chantier has twice fallen on the wrong side of it. Committing the rules
> ahead of the numbers is the only way a bar means anything.

## What run #7 measures

The loading suite (31 fixtures = 15 positives + 16 negatives) of `deep-research` at
`chantier/AI-372-v1x-dettes` (HEAD `48eaac8`), routed by three models through the
OAuth `claude -p` backend against a 30-skill synthetic index built from `~/.claude/skills`.

**The opus column is a cache replay of run #6, not a re-measurement.** `cache_key` =
sha256(prompt + system + model); 31/31 opus keys were verified present before launch, so opus
returns run #6's stored replies verbatim. Its value here is a corpus-drift check: identical
replies confirm the index and fixtures did not move. Only sonnet and haiku are new evidence.

## Index assertion (addendum precaution #1) — PASSED before launch

The hazard is live, not theoretical, and the check discriminates:

| Assertion | Value |
|---|---|
| entries named `deep-research` in the index | **1** |
| dead `plugin-namespaced` clause present in index | **False** |
| branch-unique `(use /research ` wording present | **True** |
| peer `~/.claude/skills/deep-research` → resolves to | main checkout (old description) |
| peer description carries the dead clause | **True** — dropped by name-dedup, as designed |
| total skills in index | 30 (15 617 chars) |

## Verdict semantics (from `run_evals.py:86-104`)

The runner emits raw verdicts and a `no_verdict_counts` tally. **It computes no pass/fail** —
that arithmetic is this document's job.

- `deep-research` — the target fired.
- any other kebab-case name (`research`, `superpowers:dispatching-parallel-agents`, …) — another
  owner fired. On a negative this is a **pass**.
- `none` — explicit no-route. On a negative this is a **pass**.
- `NO_VERDICT` — empty reply (subprocess failure / timeout) or prose. **Not a verdict.**

## The four rules

1. **Positive (`expect: load`) passes** iff the verdict is exactly `deep-research`.
2. **Negative (`expect: skip`) passes** iff the verdict is usable AND is not `deep-research`.
3. **`NO_VERDICT` is never a leak and never a pass.** The runner's own docstring (`:89-92`) records
   that conflating it with a real `none` scores harness format-noncompliance as a routing miss.
   It shrinks the *measurable denominator*, it does not move the numerator either way.
4. **Unmeasurable ≠ failed, and neither one pushes.** If `NO_VERDICT` count drops a model's
   measurable positives below 14 or its measurable negatives below 15, that column is
   **unmeasurable** — report it to Victor, do not push, and do not round up to "close enough".

## Bar (`evals/rubric.md:17`, verbatim)

≥ 14/15 positives **AND** ≥ 15/16 negatives, **per model**. Plus, regardless of aggregate:

- `neg-07` (`/research koyeb custom domain peering`, territorial to the user-scope command) —
  a leak here is a release blocker.
- the `neg-08` → `neg-15` → `neg-16` succession — **graded on `neg-16`**, which carries the only
  reachable owner (`superpowers:dispatching-parallel-agents` or `/research`).

**Measured before launch:** those three succession ids are the *same prompt string* (verified —
29 distinct prompts across 31 rows). They therefore share one cache key and always return one
identical verdict. Consequence, stated now rather than discovered later: the 16 negatives carry
**14 independent prompts**, and the succession passes or fails as one. This is the documented
design, not a defect, and it is why the rubric says to grade the succession on `neg-16` alone.

- A release-blocker fixture returning `NO_VERDICT` gets a **targeted retry** (free — empty replies
  are never cached). Persistent `NO_VERDICT` there ⇒ unmeasurable ⇒ stop.

## Decision table, fixed in advance

| Outcome | Action |
|---|---|
| Bar holds on all three models, blockers usable and clean | push the 7 commits (Victor's go was conditional on the measurement), then pull the main checkout — **that pull is the deploy** |
| A real leak on sonnet or haiku | **do not push.** Read the raw `responses` column before labelling it: this repo has measured that a negative leak can be a **framing artifact of the proxy** rather than a routing defect (historic finding #6 — hardening the negatives closed nothing, only the framing moved). Either way the action is stop-and-report, not iterate on the description |
| A column is unmeasurable (rule 4) | do not push; report the coverage gap |
| Opus replies diverge from run #6 | the corpus or fixtures moved ⇒ the baseline is void, re-open before reading anything else |

## The n≥3 step — a trap named before walking into it

Re-invoking `run_evals.py` for repetitions **replays the cache and returns byte-identical
replies**, manufacturing a fake-stable n=3 out of a single sample. Verified mechanically: 31/31
opus keys hit before this run. The repeats must therefore either call `router_query` directly
(no cache) or delete the specific key files between repetitions. Note also that "4 blocker
fixtures" is **2 distinct prompts** (`neg-07` + the shared succession prompt), so the repeat cost
is well under the checkpoint's ~24-call estimate.
