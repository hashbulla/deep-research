# Eval rubric — suggest-tooling

> Scoring rules for the two fixture sets. Run loading evals against any description edit or
> trigger-phrase change; run e2e evals before any release tag. Record run results (date,
> model, pass-rate) as entries in `../../gotchas-log.md`.

## 1. Loading evals (`loading.jsonl`)

For each fixture, present the prompt in a fresh session with this skill (and its territorial
neighbors — the `deep-research` skill, the `/research` command, the `update-config` skill)
available, and observe whether `suggest-tooling` activates.

| Outcome | Score |
|---|---|
| `expect: load` and the skill activates | pass |
| `expect: skip` and the skill stays silent | pass |
| Anything else | fail — record fixture id + observed routing |

**Pass bar:** >= 11/12 positives AND >= 11/12 negatives. A single negative failure on
`neg-01` (install action) or `neg-02` (deep-research territorial) is a release blocker
regardless of the aggregate — those two boundaries define the headline supply-chain risk
and the territorial conflict surface.

**Failure-mode mapping:**

- **Silent** — positives fail: the description lost its trigger semantics or paraphrase coverage.
- **Hijacker** — negatives fail broadly: the description overclaims, firing on install actions or concept questions.
- **Drifter** — loads correctly, then wanders (caught by e2e, not loading).
- **Fragile** — `pos-01`/`pos-04`-style slash/exact phrases pass but `pos-07`/`pos-08`-style paraphrases fail.
- **Overachiever** — the skill executes an install command or writes outside the run CWD (caught by e2e, not loading).

## 2. End-to-end evals (`e2e.jsonl`)

Run each fixture live (Tavily MCP required for channel queries; `gh` CLI required for
GitHub channel; results vary — only **mechanical checks** are scored, never prose quality).
Every mechanical check is a deterministic predicate or command.

**Pass bar:** every mechanical check in every fixture. The hijacker check in `e2e-hijacker`
(empty ranking for non-work-relevant run) is the skill's first non-negotiable; its failure
is a release blocker regardless of other results.

### Fixture summary

| Fixture id | Failure mode tested | Key invariant |
|---|---|---|
| `e2e-hijacker` | hijacker | Empty `ranking` array + "no work-relevant topics" note when run has zero work-relevant topics |
| `e2e-silent` | silent | At least one candidate in `ranking` for a clearly work-relevant run |
| `e2e-fragile` | fragile | Semantic mapping fires on near-miss phrasing ("retrieval evaluation" → `eval`/`rag` categories) |
| `e2e-drifter` | drifter | `work_relevant_topics` scoped to work-relevant topic only; non-work topic absent from banner and ranking |
| `e2e-overachiever` | overachiever | Zero install commands executed; zero files written outside run CWD |

### Ranker-script unit tests (do not duplicate here)

The deterministic ranker invariants — totality (every pre-classified candidate appears in
output), deduplication by `dedup_key`, small-N stability (single candidate, empty input),
and order-independence — are already covered by `../../tests/check-marketplace-rank.sh`.
The e2e evals cover the skill-orchestration layer (topic extraction, classification,
channel dispatch, artifact rendering); they do not re-test the ranker internals.

### Output well-formedness checks (apply to every e2e fixture)

These checks are implicit pass conditions for every fixture, regardless of which failure
mode the fixture targets:

- `research-toolbox.md` exists in the run CWD and contains the mandatory scope banner
  (`grep -q 'Proposals only, never auto-installed' research-toolbox.md`).
- `research-toolbox.json` is valid JSON with the required top-level keys (`run_dir`,
  `work_relevant_topics`, `degraded_channels`, `effective_weights`, `dropped_components`,
  `ranking`): `python3 -c "import json; r=json.load(open('research-toolbox.json')); [r[k] for k in ['run_dir','work_relevant_topics','degraded_channels','effective_weights','dropped_components','ranking']]"`.
- Every `trust_tier` value in `ranking` is one of `VERIFIED`, `MAINTAINED`, `COMMUNITY`,
  `CAUTION`.
- No `fake_signal_flag` field is pre-populated in the skill's candidate JSON before
  the ranker runs (the ranker computes it; the skill must not set it).

### Trust-tier correctness checks (apply to e2e-silent and e2e-fragile)

- Every candidate with `official=true` AND `verified_namespace=true` in `trust_evidence`
  must carry `trust_tier=VERIFIED`.
- No candidate with `last_activity_days > 365` may carry `trust_tier=MAINTAINED` or
  higher.
- No candidate in a non-CAUTION tier may have `fake_signal_flag=true`.

## Adding fixtures

Every new feature (flag, connector, category) adds:

1. >= 1 positive loading fixture exercising its trigger surface (if it changes the description).
2. >= 1 negative fixture for its nearest territorial neighbor.
3. >= 1 mechanical e2e check proving its definition of done.

Append-only — existing fixtures are never edited to make a failing run pass; that is eval
laundering. Fix the skill or document the waiver in `../../gotchas-log.md`.
