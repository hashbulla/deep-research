# Strategy — skill-harness run #5 on `deep-research`

> **Deviation recorded:** the Strategist agent was NOT spawned. The strategy was
> decided by the human (Victor) at Gate 1/Gate 3 before this phase would have run,
> so an agent re-deriving it would produce no information. This file records the
> executed strategy, not an inferred one.

## Executed

| Item | Value |
|---|---|
| Suite | `loading` only |
| Models | opus, sonnet, haiku |
| Backend | `cli` (`claude -p` subprocess — **no API key**) |
| Cache | `--no-cache` (fresh measurement, not a replay) |
| Corpus | merged symlink farm, **32 skills** — user-scope (`~/.claude/skills`) + project-scope (`second-brain/.claude/skills`) |
| Rows | 30 (15 `expect: load`, 15 `expect: skip`) |
| Result | 90/90 cells returned; 1 `NO_VERDICT` (haiku) |
| Raw output | `loading_matrix.json` in this staging dir |

## Why this corpus

The default corpus (`~/.claude/skills`) omits project-scope siblings, so the real
over-fire neighbours are absent and the measurement comes out **too lenient**.
The farm merges both scopes. `deep-research` itself resolves inside it.

## Why `loading` only

`run_evals.py` reads `entry["prompt"]`. `progressive.jsonl` keys on `when` and
`e2e.jsonl` on `invocation`, so both suites skip every row and report `[]` with
zero failures — **structurally indistinguishable from a perfect score**. Running
them would manufacture a false green. This is already recorded as a known
limitation in the skill's own CHANGELOG.

## Static checks executed

`lint_skill.py` → `lint.txt` · `token_budget.py` → `budget.txt` ·
`conflict_check.py --corpus <merged>` → `conflict.txt`.

## Coverage gaps — what this run does NOT test

1. **`progressive` and `e2e` suites are ungraded by execution.** Their fixtures
   are read statically only. No behavioural claim in this review rests on them.
2. **`evals/sycophancy-probes.jsonl` and `evals/benchmark-testset.jsonl` are
   executed by nothing** — `--suite` accepts only `loading|progressive|e2e`.
3. **The D1 oracle is self-referential.** `hero-queries.md` is absent, so
   `loading.jsonl` prompts were author-authored *from* the description. The
   harness guide's stated mitigation for the description-self-grading failure
   mode is therefore unavailable for this skill. Human decision (Gate 2): grade
   D1 from the matrix, but label the self-reference explicitly.
4. **Single-run routing.** One matrix per model. Recorded methodology holds that
   n=1 lies on routing; this run is paired against run #4's archived matrix as a
   drift control, but neither run is n≥3.
5. **Rule 7c/7b verify query *shape*, not that GitHub was actually queried.** A
   stdlib-only, zero-network gate cannot verify a retrieval act.
6. **`__pycache__` contamination.** A CI `py_compile` step executed during this
   session wrote `.pyc` files into `scripts/` and `suggest-tooling/scripts/`
   (~88 KB). They are gitignored and never ship, but `token_budget.py` counts
   them into the FILES tier. Any files-tier number must exclude them.
