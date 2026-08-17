# Eval rubric — deep-research

> Scoring rules for the three fixture sets. Run loading evals against any model change or description edit; run e2e evals before any release tag. Record run results (date, model, pass-rate) as entries in `../gotchas-log.md`.

## 1. Loading evals (`loading.jsonl`)

For each fixture, present the prompt in a fresh session with this skill (and its territorial neighbors — the Tavily MCP tools, the user-scope `/research` command, and `superpowers:dispatching-parallel-agents` for fan-out probes) available, and observe whether the skill activates.

**A neighbor that does not exist cannot be a test condition.** Until 2026-08-17 this line named a "plugin-namespaced `deep-research` sibling" as a neighbor to make available — an unsatisfiable setup: run #4 proved the sibling absent by grep over 133 installed `SKILL.md` files, zero hits. Every negative graded against that boundary was therefore graded against an unreachable owner. Corrected with `neg-16`; `neg-08`/`neg-15` stay unedited as the record of the contract at their date.

| Outcome | Score |
|---|---|
| `expect: load` and the skill activates | pass |
| `expect: skip` and the skill stays silent | pass |
| Anything else | fail — record fixture id + observed routing |

**Pass bar:** ≥ 14/15 positives AND ≥ 15/16 negatives (counts realigned to the fixture file — positives 2026-08-04, negatives 2026-08-17 with `neg-16`; appended fixtures raise the bar with them, tolerance stays at one miss per side). A single negative failure on `neg-07`, or on the `neg-08`→`neg-15`→`neg-16` succession (territorial neighbors) is a release blocker regardless of the aggregate — those boundaries are the documented conflict surface. **Grade the succession on `neg-16`**: it carries the only reachable owner.

**Failure-mode mapping** (the five activation failure modes):

- **Silent** — positives fail: the description lost its trigger semantics.
- **Hijacker** — negatives fail broadly: the description overclaims.
- **Drifter** — loads correctly, then ignores phases (caught by e2e, not loading).
- **Fragile** — `pos-01`-style exact phrases pass but `pos-07`/`pos-11`-style paraphrases fail.
- **Overachiever** — the skill answers a `neg-*` prompt itself instead of deferring to the named tool.

## 2. Progressive-disclosure evals (`progressive.jsonl`)

Trace which files the skill reads at each pipeline moment. A fixture passes when every `expect_read` file is read at (or after) the stated moment AND no `expect_not_read` file is read before it.

**Pass bar:** 13/13 (count realigned to the fixture file 2026-08-04; appended fixtures raise the bar with them — the stale `9/9` predated `prog-10`). The load-tier discipline (prog-01), the hash-before-trust rule (prog-03) and the conditional solution-space read (prog-11 / prog-12) are non-negotiable; their failure is a release blocker.

## 3. End-to-end evals (`e2e.jsonl`)

Run each invocation live (Tavily MCP required; results vary — only the **mechanical checks** are scored, never the prose quality). Every mechanical check is a deterministic command or transcript predicate.

**Pass bar:** every mechanical check in every fixture. The plan-precedes-retrieval check in `e2e-01` / its successor `e2e-13` (no Tavily call before `research-plan.md` exists) and the `e2e-10` companion (no Tavily call before a triggered AskUserQuestion refinement resolves) are the skill's first non-negotiable (anti-pattern A1); their failure invalidates the entire run regardless of artifact quality. The five-artifact + `check-solution-space` PASS contract is carried by `e2e-11`; the top-of-report obligations header by `e2e-12`; the GitHub-native OSS sweep (topic facet before star bands, gate Rule 7b firing on its own mutation) by `e2e-15`.

## Adding fixtures

Every new feature (flag, retrieval source, gate) adds:

1. ≥1 positive loading fixture exercising its trigger surface (if it changes the description),
2. ≥1 negative fixture for its nearest territorial neighbor,
3. ≥1 mechanical e2e check proving its DoD.

Append-only — existing fixtures are never edited to make a failing run pass; that is eval laundering. Fix the skill or document the waiver in `../gotchas-log.md`.

**Superseding a fixture whose contract changed.** When a deliberate contract change makes an existing fixture assert a superseded rule, do NOT edit it. Append a **successor** with the same probe intent and the corrected assertion, state `SUPERSEDES <id> (<date>)` in the successor's own rationale field (`boundary` for loading, `note` for progressive, the first `mechanical_checks` string for e2e — never a new key), and log the supersession in `../gotchas-log.md`. The superseded fixture stays in the file unedited: it is an accurate record of the contract at its date. Pairs currently live: `neg-08`→`neg-15`, `prog-09`→`prog-13`, `e2e-01`→`e2e-13`, `e2e-08`→`e2e-14` (all 2026-08-04, four→five artifacts) · `neg-15`→`neg-16` (2026-08-17, dead owner replaced by a reachable one — a **three-link chain**: grade the last link).
