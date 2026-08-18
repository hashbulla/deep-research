# Run #9 — the bar is met on a rubric-faithful instrument

> Measured 2026-08-18 against `SCORING-POLICY.md` (pre-registered 2026-08-17, before any of this
> data existed). **Verdict: PASS on all three models, both release blockers clean at n=8, zero
> leaks in 48 live calls.** This is the measurement runs #7 and #8 were missing, and it closes the
> question they left open.

## 1. What changed since run #8: the instrument, not the skill

`SKILL.md` is byte-identical to run #8. The only change is the corpus the router is shown.

`evals/rubric.md:7` requires the eval to present the skill *"and its territorial neighbors …
`superpowers:dispatching-parallel-agents` for fan-out probes"*, and `:9` states the principle
outright: **"a neighbour that does not exist cannot be a test condition."** Runs #6-#8 all violated
it — `run_evals.py` indexes `DEFAULT_CORPUS = ~/.claude/skills` only, and the owner `neg-16` names
lives under `~/.claude/plugins/`.

Run #9 supplies the corpus the rubric asks for: **60 entries — 30 user-scope skills + 30 plugin
skills**, the latter resolved from `~/.claude/plugins/installed_plugins.json`, the authoritative
record of *active* versions. (The cache holds 146 `SKILL.md` across stale versions; choosing by sort
order or mtime would have been a guess.) Manifest: `run9-corpus-manifest.txt`.

**Nothing was fabricated.** User-scope *commands* (`/research`, `/scrape`) are a different surface
from skills and remain unrepresented — inventing `SKILL.md` stubs for them would inject made-up
descriptions into the measurement. Stated as a residual gap, not papered over.

## 2. Full suite, 31 fixtures × 3 models

| Model | Positives | Negatives | NO_VERDICT | `neg-07` | `neg-16` |
|---|---|---|---|---|---|
| opus | **15/15** | **16/16** | 0 | `research` | **`dispatching-parallel-agents`** |
| sonnet | **15/15** | **16/16** | 0 | `research` | **`dispatching-parallel-agents`** |
| haiku | **15/15** | **16/16** | 0 | `research` | **`superpowers:dispatching-parallel-agents`** |

On `neg-16` the models do not merely abstain — they **name the legitimate owner**. That is the
sharpest possible pass on a territorial negative.

**Coverage note, recorded rather than hidden.** The first pass returned **15 `NO_VERDICT`**, every
one of them an *empty* reply (subprocess timeout), never prose — plausibly the 64% larger system
prompt (25,646 vs 15,617 chars) under contention with another session's run. Per `SCORING-POLICY.md`
rule 4 that made all three columns **unmeasurable, not failed**, and no push could follow. Empty
replies are never cached, so a second invocation retried exactly those 15 and replayed the other 72.
The table above is the completed pass.

## 3. Release blockers at n=8, cache bypassed — the test run #7 failed

n=1 is what made run #7's matrix wrong: it drew the clean side of a ~40% coin. `repeat_fixtures.py`
calls `router_query` directly (going through `run_evals.py` would replay the cache and print a
fabricated "stable"), holding the backend flock:

| Fixture / model | n=8 result | Leaks |
|---|---|---|
| `neg-07` / opus | `research` ×6, `none` ×2 | **0/8** |
| `neg-07` / sonnet | `research` ×8 | **0/8** |
| `neg-07` / haiku | `research` ×8 | **0/8** |
| `neg-16` / opus | `dispatching-parallel-agents` ×8 | **0/8** |
| `neg-16` / sonnet | owner ×2, `none` ×6 | **0/8** |
| `neg-16` / haiku | `superpowers:dispatching-parallel-agents` ×8 | **0/8** |

**48 live calls, 0 leaks.** Sonnet on `neg-16` goes from **7/18 (~39%)** to **0/8**. Were the true
rate still 39%, eight clean draws would occur in **1.9%** of runs — so the improvement is not a
lucky sample.

## 4. The finding: the fix and the corpus are complementary, never alternatives

Four conditions were measured across runs #7-#9, one variable at a time. Read together they
overturn *both* single-cause explanations this chantier argued in turn:

| Description | Owner in index | `neg-16` / sonnet |
|---|---|---|
| no clause | absent | leak ~38% |
| no clause | **present** | leak 2/5 — the router has nowhere to defer |
| **clause** | absent | leak ~52% — **worse**: vocabulary supplied, escape hatch withheld |
| **clause** | **present** | **0/8, and the owner is named** |

Neither half works alone, and the description fix *without* a reachable owner is worse than doing
nothing. That is why the two earlier A/Bs — each correctly varying a single variable — both
concluded "not this one": **they were testing the two halves of a conjunction.**

> The generalisation, extending `rubric.md:9`: **a neighbour that does not exist cannot be a
> deferral target either.** A `Do NOT … use X` clause is worth exactly what the router can reach of
> `X`. Name an unreachable owner and the clause supplies the vocabulary without the alternative —
> measurably worse than silence.

## 5. Bar check (`evals/rubric.md:17`)

- ≥14/15 positives per model — **15/15 on all three.**
- ≥15/16 negatives per model — **16/16 on all three.**
- Zero failure on `neg-07` and on the `neg-08`→`neg-15`→`neg-16` succession, graded on `neg-16` —
  **0/8 leaks per model, on both.**

**The bar is met.**

## 6. Limits that travel with this verdict

1. **The corpus is reconstructed, not the real router.** It is strictly more faithful than
   `~/.claude/skills` alone (which the rubric forbids), but it is still a proxy.
2. **Commands are unrepresented.** `neg-07` passes because the models name `research` from ambient
   knowledge of their environment, not because it is on the menu they were given.
3. **The proxy's framing is uncalibrated** (AI-330). Run #8 measured that the strict-framing arm is a
   *diagnostic for description overclaim* — its direction identifies the layer at fault — but the
   default framing's fidelity to the real router remains unverified.
4. **Corpus mutability.** Another session installed a skill mid-measurement on 2026-08-17 at 19:13:10.
   The cache key hashes the system prompt, so any corpus change silently invalidates every cached
   reply. Pin or snapshot the corpus before a graded run.

## Artifacts

| File | What it is |
|---|---|
| `run9-union-matrix.json` | the completed 3-model matrix on the union corpus |
| `run9-GRADE.txt` | that matrix graded against the pre-registered policy |
| `run9-blockers-n8.txt` | 48 live calls, cache bypassed — the decisive repetition |
| `run9-corpus-manifest.txt` | the 60 corpus entries and their real targets, reproducible |
| `repeat_fixtures.py` | the repeater, now taking a corpus argument |
