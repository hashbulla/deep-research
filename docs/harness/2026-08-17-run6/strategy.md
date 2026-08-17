# Test-execution strategy — deep-research @ chantier/AI-372-v1x-dettes

## Process deviations, declared up front

1. **Authored by the orchestrator, not the `skill-harness-strategist` agent.** The four
   harness agents exist as definition files under `~/.claude/skills/skill-harness/agents/`
   but are **not registered as agent types in this session** (the session's agent roster does
   not contain them). Phases that involve *judgement* are still run as isolated agents, with
   their full definition inlined into a `general-purpose` spawn — that preserves both the
   context isolation and the structural Analyst/Critic separation the oracle requires. This
   file, by contrast, records a decision the **human already made at Gate 1**, so no agent had
   any latitude left to exercise.
2. **Gate 3 folded into Gate 1.** The Gate-1 question explicitly presented the matrix scope
   options with their costs, and the user chose. Re-asking "approve this strategy?" would
   re-litigate a decision already taken — house rule: never re-pose a settled decision.
3. **The target is a git worktree**, so the folder is named `AI-372-v1x-dettes`, not
   `deep-research`. Consequence to carry into grading: `lint_skill.py` check#1 (folder name
   kebab-case) fires an ERROR that is an **artifact of the evaluation setup**, not a defect of
   the skill. The real folder is `20-engineering/skills/deep-research`. Do not score it.

## What is being graded, and why this branch

Branch `chantier/AI-372-v1x-dettes`, 5 commits, **not pushed**. It carries the v1.x package
ratified under AI-372 / PRD-refonte R6+R8. The branch — not `main` — is the object of the
grade, because it is the state awaiting a merge decision.

The three changes with **no mechanical oracle**, i.e. the reason this harness run exists:

- **SKILL.md 209 → 150 lines**, done by densifying and never deleting. A 32-marker presence
  sweep passed (all 7 grading steps, all 13 edge cases, all 16 reference files). But a marker
  sweep proves *content* survived — it says nothing about whether the routing prompt still
  works, nor about structure.
- **The routing `description` changed**: the clause deferring to a non-existent
  "plugin-namespaced deep-research sibling" was removed. The description is the routing
  surface, so this is the highest-risk edit in the package.
- **A new Phase-6 step** (run-accounting emission) absorbed at **net-zero lines**.

## Suites and models

| Suite | Run? | Models | Rationale |
|---|---|---|---|
| `loading` (31 fixtures: 15 positive, 16 negative) | **YES** | **opus only** | User's Gate-1 decision. Lifts the D1 coverage-gap ceiling of 5.0 — the false positive this harness exists to prevent |
| `progressive` (13 fixtures) | No | — | Traces which files are read per phase; needs a real run, not a router probe |
| `e2e` (16 fixtures) | No | — | Requires live Tavily + a full ~38 min run. Out of scope for a design grade |

Caching enabled (default). Backend `cli` (`claude -p`, OAuth, no API key).

## Runner prerequisite — fixed immediately before this run

`run_evals.py` carried two defects that would have corrupted this very grade. Both were fixed
and merged into `skill-generator` before launching (commit `89e9c8d`, 2 tests added,
red-ability proven by restoring each defect):

- `_KEBAB_RE` admitted no colon, so a plugin-namespaced reply such as
  `superpowers:dispatching-parallel-agents` fell through to `NO_VERDICT`. That is the exact
  reply the router gave on `neg-08`/`neg-15` in runs #4 and #5, and `neg-16` — the fixture
  this package *adds* — expects the same owner. Ungated, D1 would have been graded against
  three spurious non-verdicts on the rubric's own release-blocker boundary.
- The row builder read `expected_skill`, a key absent from this skill's fixtures (their key
  union is exactly `id`/`prompt`/`expect`/`boundary`), recording `expected_skill: null` on
  every row — indistinguishable from "nothing should fire". `derive_oracle()` now handles both
  conventions and splits the oracle into `expected_fire` + `expected_skill` + `oracle_source`,
  with a loud `MISSING` when no convention matches.

## Coverage gaps this strategy accepts

1. **No sonnet, no haiku signal.** Single-model coverage. This is the sharpest gap: a weakened
   description degrades on the *weaker* routers first, and sonnet is precisely where the
   `neg-08`/`neg-15` leak appeared in run #4. A clean opus matrix therefore does **not**
   establish that the compression left routing intact — it establishes that opus still routes
   correctly. Say so in the report; do not let a clean opus column read as "routing verified".
2. **No progressive suite.** The compression moved reference pointers around
   (`Examples` folded into `References`); progressive fixtures are what would catch a
   load-tier regression. Untested here.
3. **No e2e.** The new run-accounting step (`e2e-16`) is unexercised — including its
   load-bearing negative assertion that no cost figure appears in the output.
4. **n=1 per cell.** Single-run routing measurements are known to lie on this target: the
   repo's own gotchas-log records `neg-08`≡`neg-15` as unstable in baseline (haiku
   `NO_VERDICT` ×2) and closes an ablation with "re-open only with an n>=3-per-cell run".

## Known instrument caveats to hand the Critic

- **`token_budget.py` FILES TIER over-counts.** It sums `scripts/__pycache__/*.pyc`
  (~37k tokens across 5 files), which are **gitignored and untracked** (`.gitignore:25`) and
  never ship. Verified: `git ls-files | grep -c __pycache__` = 0. Grade the index and load
  tiers, treat the files tier as inflated by a local build artifact.
- **`lint_skill.py` check#17** flags the name `deep-research` as matching a forbidden
  substring in `forbidden_names.txt`. Pre-existing, and plausibly deliberate given the
  same-name collision this package just removed from the description. Not introduced by these
  5 commits.
- **The evaluator is historically too severe on this target.** The repo's CHANGELOG records
  calibration logs for runs #4 and #5, the latter titled "evaluator too severe AGAIN". This is
  run **#6**, and the rubric itself ships UNCALIBRATED. Scores are indices, not marks.
