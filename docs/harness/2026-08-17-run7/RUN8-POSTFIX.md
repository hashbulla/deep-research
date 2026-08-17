# Run #8 — the description fix is confirmed on its diagnosed axis, and the harness still fails `neg-16`

> Measured 2026-08-17 after `f7f7904`, under the same pre-registered policy as run #7
> (`SCORING-POLICY.md`). **Verdict: still DO NOT PUSH** — but the reason has moved, and the next
> step is no longer a description edit. Two independent axes show the diagnosed defect is fixed;
> the residual failure is now attributable to the instrument's own configuration, which this
> repo's rubric already declares invalid (`rubric.md:9`).

## 1. What the fix was, and what it was aimed at

Run #7 diagnosed the leak with the strict-framing arm: asked whether "fan out a bunch of research
agents on this topic and just give me the gist, no plan needed" is *clearly within* the skill's
stated scope, sonnet answered yes **5/5**. The description opened on "Agentic multi-source deep
research" and its `Do NOT` list never mentioned fan-out, parallel subagents, or the absence of a
plan. `f7f7904` added one clause inside that list, naming the intent and its owner:

> `fanning out parallel research subagents for a quick gist with no plan (use superpowers:dispatching-parallel-agents)`

One variable changed on purpose: the opening "Agentic" was left alone.

## 2. The fix is confirmed on two independent axes

| Evidence | Pre-fix | Post-fix | What it shows |
|---|---|---|---|
| **STRICT framing**, sonnet, n=5, owner absent | **5/5 leak** | **0/5 leak** | The description no longer claims the territory. This was *the* diagnosed defect, measured by the instrument that found it. |
| `neg-16` / **haiku**, n=8 | `research` 3/3 | **`superpowers:dispatching-parallel-agents` 8/8** | The clause is read and acted on: haiku now names the exact owner the clause designates, unanimously. |
| `neg-16` / **opus**, n=8 | `none` 3/3 | `none` 8/8 | No regression. |
| **Positives**, n=1 × 3 models | 15/15 | 15/15 | No silent-skill regression. |
| `pos-03` ("architectures **multi-agents**"), `pos-14` ("**agent**-observability"), sonnet, n=5 | — | **fire 5/5 each** | The two positives most exposed to a clause about "parallel research subagents" are unharmed. |

The strict-framing reversal is the strongest single result in this chantier: the same arm that
produced 5/5 leaks before the edit produces 0/5 after it, with the corpus held constant and the
owner *absent*. The description now resolves the boundary correctly on its own merits.

## 3. And the harness still fails the fixture

`neg-16` / sonnet under the harness's **default** framing, cache bypassed:

| Condition | Pre-fix | Post-fix |
|---|---|---|
| owner **absent** from index (the harness as configured) | 5/13 ≈ 38 % | **11/21 ≈ 52 %** |
| owner **present** in index | 2/5 = 40 % | **1/8 = 12.5 %** |

`evals/rubric.md:17` makes a single failure here a release blocker regardless of the aggregate.
**The blocker still fires, so the package still does not ship.**

## 4. The mechanism, and the generalisation worth keeping

The two rows of that table move in *opposite* directions, and the split explains itself.

`build_skill_index` rule 3 tells the router: "If multiple skills could match, pick the **most
specific** one based on the user's exact intent." That framing applies pressure to pick *something*
close. The fix added fan-out vocabulary ("parallel research subagents", "quick gist", "no plan") to
`deep-research`'s description — and the escape hatch it names, `dispatching-parallel-agents`, is
**not in the harness corpus** (`DEFAULT_CORPUS = ~/.claude/skills`; the skill lives under
`~/.claude/plugins/.../superpowers/6.3.0/skills/`). So under default framing the clause makes the
skill *lexically nearer* the prompt while the alternative it points to is off the menu.

Corroboration, not conjecture: **haiku, on the same index, answers
`superpowers:dispatching-parallel-agents` 8/8** — a name absent from the list it was given, reached
from ambient knowledge of the real environment. Sonnet confines itself to the list more closely, so
with the owner missing it takes the nearest present option. Add the owner and sonnet's leak drops
3/8 → 1/8, and one of its eight replies *is* `dispatching-parallel-agents`.

> **`rubric.md:9` says "a neighbour that does not exist cannot be a test condition."**
> Run #8 extends it: **a neighbour that does not exist cannot be a deferral target either.**
> A `Do NOT … use X` clause is only as good as the router's ability to reach `X`. Naming an
> unreachable owner can make a leak *worse* than saying nothing, because it supplies the vocabulary
> without supplying the alternative.

Honest statistics: 3/8 vs 1/8 at n=8 is **directional, not significant** (Fisher exact ≈ 0.57). The
claim defended here is the mechanism plus the strict-framing reversal, not the size of that gap.

## 5. What this means for the verdict

Three conditions, three answers, and the instrument's configuration is now **load-bearing**:

| Condition | `neg-16` / sonnet | Closeness to production |
|---|---|---|
| default framing, owner absent | ~52 % leak | the harness as configured — and a setup `rubric.md:7` forbids |
| default framing, owner present | 12.5 % leak | closer: the real router does index plugin skills |
| strict framing, owner absent | **0 %** | closest on scope reasoning: the real router may decline, it is not forced to pick the nearest match |

The real Claude Code router indexes plugin skills — `superpowers:dispatching-parallel-agents` is
live in this very session — and is not compelled to choose a nearest neighbour. So the two
conditions nearer production are the two where the leak largely or entirely disappears.

**That is not a licence to push.** It is the reason the next step changed: the failing measurement
is now dominated by a known, documented, already-ticketed instrument defect
(corpus under-inclusion vs `rubric.md:7`; framing fidelity = AI-330) rather than by the skill.
Editing the description further would be tuning the skill against a proxy the repo's own rubric
says is mis-configured — and the one edit made so far already moved the two production-nearer
conditions in the right direction while doing nothing for the mis-configured one.

## 6. Recommended next step (Victor's call)

1. **Keep `f7f7904`.** Confirmed on two axes, zero positive regression.
2. **Fix the instrument before touching the description again** — the corpus union `rubric.md:7`
   already mandates (`--corpus` exists): `~/.claude/skills` + plugin skill trees + command stubs,
   still excluding the target's own installed copy. Then re-measure `neg-16` at n≥8 per model.
3. **Do not tune "Agentic" yet.** It is the next candidate if a corrected instrument still leaks,
   but changing it now would confound the one clean attribution this session bought.
4. Carry the debts already listed in `FINDINGS.md` §7 (supersede `neg-12`'s phantom owner; n≥5 not
   n≥3 on release blockers in the rubric).

## Artifacts added by run #8

| File | What it is |
|---|---|
| `run8-loading_matrix_3models.json` | the post-fix n=1 matrix, 3 models × 31 fixtures |
| `run8-GRADE.txt` | that matrix graded against the pre-registered policy |
| `run8-verify.txt` | blockers n=8 × 3 models · at-risk positives n=5 · framing diagnostic re-run |
| `run8-corpus-ab-postfix.txt` | post-fix corpus A/B, n=8, sonnet |
| `repeat_fixtures.py` | generalised repeater (any fixture ids), cache bypassed, flock held |
