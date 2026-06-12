# Eval rubric — deep-research

> Scoring rules for the three fixture sets. Run loading evals against any model change or description edit; run e2e evals before any release tag. Record run results (date, model, pass-rate) as entries in `../gotchas-log.md`.

## 1. Loading evals (`loading.jsonl`)

For each fixture, present the prompt in a fresh session with this skill (and its territorial neighbors — the Tavily MCP tools, the user-scope `/research` command, the plugin-namespaced `deep-research` sibling) available, and observe whether the skill activates.

| Outcome | Score |
|---|---|
| `expect: load` and the skill activates | pass |
| `expect: skip` and the skill stays silent | pass |
| Anything else | fail — record fixture id + observed routing |

**Pass bar:** ≥ 12/13 positives AND ≥ 12/13 negatives. A single negative failure on `neg-07` or `neg-08` (territorial neighbors) is a release blocker regardless of the aggregate — those two boundaries are the documented conflict surface.

**Failure-mode mapping** (the five activation failure modes):

- **Silent** — positives fail: the description lost its trigger semantics.
- **Hijacker** — negatives fail broadly: the description overclaims.
- **Drifter** — loads correctly, then ignores phases (caught by e2e, not loading).
- **Fragile** — `pos-01`-style exact phrases pass but `pos-07`/`pos-11`-style paraphrases fail.
- **Overachiever** — the skill answers a `neg-*` prompt itself instead of deferring to the named tool.

## 2. Progressive-disclosure evals (`progressive.jsonl`)

Trace which files the skill reads at each pipeline moment. A fixture passes when every `expect_read` file is read at (or after) the stated moment AND no `expect_not_read` file is read before it.

**Pass bar:** 9/9. The load-tier discipline (prog-01) and the hash-before-trust rule (prog-03) are non-negotiable; their failure is a release blocker.

## 3. End-to-end evals (`e2e.jsonl`)

Run each invocation live (Tavily MCP required; results vary — only the **mechanical checks** are scored, never the prose quality). Every mechanical check is a deterministic command or transcript predicate.

**Pass bar:** every mechanical check in every fixture. The human-gate check in `e2e-01` (no Tavily call before approval) is the skill's first non-negotiable; its failure invalidates the entire run regardless of artifact quality.

## Adding fixtures

Every new feature (flag, retrieval source, gate) adds:

1. ≥1 positive loading fixture exercising its trigger surface (if it changes the description),
2. ≥1 negative fixture for its nearest territorial neighbor,
3. ≥1 mechanical e2e check proving its DoD.

Append-only — existing fixtures are never edited to make a failing run pass; that is eval laundering. Fix the skill or document the waiver in `../gotchas-log.md`.
