# Strategy — `deep-research` (worktree `github-topic-facet`, commit `11a0439`)

> Strategist artifact. A plan, not a verdict — no grading here. Every number below was measured
> this session by reading `run_evals.py` and the fixture files; none is inherited from the
> agent definition's examples (which are stale — see §Models).

## Fixture inventory

Measured by parsing each `.jsonl` with the **runner's own admission rules**
(`run_evals.py:384-398`: skip blank / `//` / unparseable / `_comment` rows, then
`prompt = entry.get("prompt")` — a row with no `prompt` key, or a `prompt` containing `<`,
is silently dropped).

| Suite | Path | Exists | Rows | Keys per row | Rows the runner will execute | Notes |
|---|---|---|---|---|---|---|
| loading | `evals/loading.jsonl` | yes | 30 | `id`, `prompt`, `expect`, `boundary` | **30 / 30** | 15 `expect:load` + 15 `expect:skip`. Only **29 unique prompts** — `neg-08` and `neg-15` are byte-identical. |
| progressive | `evals/progressive.jsonl` | yes | 13 | `id`, `when`, `expect_read`, `expect_not_read`, `note` | **0 / 13** | No `prompt` key on any row ⇒ every row dropped at `run_evals.py:396`. Emits `"progressive": []`. |
| e2e | `evals/e2e.jsonl` | yes | 15 | `id`, `invocation`, `mechanical_checks` (+`rationale` on 1) | **0 / 15** | No `prompt` key on any row ⇒ every row dropped. Emits `"e2e": []`. |
| sycophancy | `evals/sycophancy-probes.jsonl` | yes | 5 | `id`, `version`, `prompt`, `false_premise`, `expected` | **not selectable** | Has `prompt` keys, but `--suite` only accepts `{loading,progressive,e2e,all}` (`:323`). Unreachable. |
| benchmark | `evals/benchmark-testset.jsonl` | yes | 5 | `id`, `version`, `question`, `profile`, `date_pin`, `notes` | **not selectable** | Keys on `question`; unreachable for the same reason. |

**`NOT RUN ≠ PASS` — mechanically confirmed, not merely quoted.** `CHANGELOG.md:40` is accurate.
`--suite all` *does* iterate all three suites (`:344`), and each writes a key into
`matrix["suites"]`. `progressive` and `e2e` therefore appear in the output JSON as
`"progressive": []` and `"e2e": []` — structurally identical to "ran, zero failures".
The Critic must treat both as **NOT RUN**, and `no_verdict_counts` for those suites
(`{opus:0, sonnet:0, haiku:0}`) as vacuous, not clean.

## Execution plan

- **Suites to run**: `loading` only — via `--suite loading`, **not** `--suite all`.
  Rationale: `--suite all` adds zero coverage (0 executable rows in the other two) while
  emitting two empty arrays that read as passes. Running `loading` alone makes the
  non-coverage explicit in the plan instead of hiding it in the artifact.
- **Models**: `opus,sonnet,haiku` — the runner's own `DEFAULT_MODELS` (`run_evals.py:51`),
  passed straight through to `claude --model` (`:241`).
- **Caching**: cache-first (default). **Measured cold** — see §Cache state.
- **cli backend (`claude`) available**: **yes** — `/home/ouroz/.local/bin/claude`, v2.1.222.
  `ANTHROPIC_API_KEY` is **unset**, which is irrelevant: it is needed only for `--backend sdk`
  (`:196-202`). No coverage gap on this axis.
- **Estimated router calls**: **~87 fresh** + 3 same-run cache hits = 90 (prompt, model) cells.
  (29 unique prompts × 3 models fresh; `neg-15` replays `neg-08`'s cache entry written earlier
  in the same run, since the cache key is `sha256(model + system + user_message)` and the two
  prompts are identical — `:186-193`, `:300-317`.)
- **Estimated runtime**: **~15-25 min wall clock**, uncached. Calls are `claude -p` subprocesses
  serialized under a **global** advisory flock (`:105-132`) — the lock is skill-independent, so a
  concurrent `run_evals` anywhere on this machine blocks this one. Per-call timeout is 120 s
  (`:54`); a pathological run is bounded at ~2.9 h. Cached re-run: seconds.
- **Estimated $ cost**: **zero API spend** — the cli backend consumes the OAuth (Claude Max)
  session, not metered API credits.

### Canonical commands for the Critic

```bash
SKILL=/home/ouroz/.cache/dr-worktrees/github-topic-facet
GEN=/home/ouroz/.claude/skills/skill-generator/scripts

# Static (deterministic, fast, run first — harness-guide §6)
python3 $GEN/lint_skill.py     $SKILL --json
python3 $GEN/token_budget.py   $SKILL --json
python3 $GEN/conflict_check.py $SKILL --json

# Dynamic routing matrix (the only executable suite)
python3 $GEN/run_evals.py $SKILL --suite loading --models opus,sonnet,haiku
```

Both static scripts were checked for false-positive risk against **this** target and are safe:

- `conflict_check.py:109` skips self on `peer_dir.resolve() == target_path` **or**
  `peer_dir.name == target_name`. The corpus contains a deployed `~/.claude/skills/deep-research`
  (symlink → `second-brain/20-engineering/skills/deep-research`) whose dir name equals the
  worktree's frontmatter `name` ⇒ **the second clause fires and self-comparison is skipped**.
  No spurious jaccard≈1.0 against dimension 6.
- `token_budget.py:90` walks only `references/`, `scripts/`, `assets/`, `evals/`. The bundled
  **second skill** `suggest-tooling/` is *not* walked, so it cannot inflate the files tier.
  Minor noise: 2 `.pyc` files under `scripts/` are read with `errors="replace"` and counted
  (files tier only; no hard cap applies).
- `run_evals.py:145-183` builds the synthetic index from the worktree's SKILL.md **first**, then
  dedupes peers by name (`:168`) — verified: the index contains **exactly one** `deep-research`
  entry, and it is the worktree's description, not the deployed copy's.

## Cache state

**Cold. 0 reusable entries. Budget the full ~87 fresh calls.**

- The cache root is `$XDG_CACHE_HOME/skill-harness/run_evals/<skill_path.name>` (`:94-102`) —
  keyed on the **directory basename**, not the frontmatter name. For this worktree that is
  `~/.cache/skill-harness/run_evals/**github-topic-facet**/`, which **does not exist**.
- A prior worktree of this same skill left 78 entries in
  `~/.cache/skill-harness/run_evals/AI-355-sota-research-hardening/` (= 26 rows × 3 models, i.e.
  the suite before `pos-14/15` and `neg-14/15` were appended). I tested key compatibility
  directly — rebuilt the system prompt with `build_skill_index()`, recomputed
  `cache_key(routing_user_message(prompt), system, model)` for all 30 rows × 3 models, and probed
  the old directory: **0 / 90 hits**. Cause: commit `1f10507` (2026-08-04 19:54, the D3 token
  surgery / description edit) post-dates that cache (16:43), so the `system` component of every
  key changed. Seeding the new cache dir from the old one would be a no-op — do not bother.
- Two consequences the Critic should know: (1) the matrix header will read
  `"skill": "github-topic-facet"`, not `deep-research` — do not report that as the skill's name;
  (2) this run's cache lands under the worktree basename and will not be reused by a run against
  the deployed path.

## Coverage gaps

Enumerated as first-class output (harness-guide §4). Ordered by how much they should temper a score.

1. **The commit's own DoD is only partly verifiable.** `e2e-15` — the fixture this commit adds to
   carry contract Rule 7b — lands in the **one suite the runner cannot execute**. Of its five
   mechanical checks: checks **1, 2, 3** (≥1 GitHub-native query in the emitted manifest;
   ≥3 distinct `topic:` combinations; topic sweep ordered *before* the first star-band shard in
   the transcript) require a **live `/deep-research` invocation** and are unverified by anything
   in this plan. Checks **4 and 5** (gate exits 0 PASS on a conformant manifest; the same gate
   exits 1 naming "GitHub-native query" on a mutation that drops every native query) **are**
   mechanically executable today — see §Substitute coverage.
2. **`progressive` (13 rows) and `e2e` (15 rows) are graded statically or not at all.** The load-tier
   discipline (`prog-01/03/11/12`, rubric-designated non-negotiable) and every runtime contract
   (`e2e-01/10/13` invalidate a run on failure) rest on author assertion. The commit message's
   "Suite complète verte" refers to the **CI shell tests**, not these suites.
3. **The matrix carries no expected value.** `run_evals.py:403-404` reads `entry.get("expected_skill")`
   and `entry.get("category")`; this suite uses **`expect: "load" | "skip"`** and `boundary`.
   Every row will therefore show `"expected_skill": null, "category": null`. A Critic that
   compares `verdicts` against `expected_skill` scores 0/30 against a null. **The matrix must be
   re-joined to `evals/loading.jsonl` on the `prompt` string**, and graded as:
   `expect:load` ⇒ pass iff verdict == `deep-research`; `expect:skip` ⇒ pass iff verdict ≠ `deep-research`.
4. **Negatives can only prove non-firing, never correct ownership.** `evals/rubric.md:15` calls
   `neg-07` (`/research`) and `neg-08`/`neg-15` (the plugin-namespaced `deep-research` sibling)
   **release blockers** on the grounds that they are "the documented conflict surface" — but
   neither owner exists in the synthetic index: `/research`, `/scrape`, `/fetcher-pick` are
   **user-scope commands** (`~/.claude/commands/*.md`), never skills. And the
   **plugin-namespaced `deep-research` sibling does not exist on this machine at all**: of the
   **133** `SKILL.md` files installed under `~/.claude/plugins/`, **zero** carry
   `name: deep-research`; the only such file on disk is the deployed copy of this same skill
   (`second-brain/20-engineering/skills/deep-research/SKILL.md`). Because `expect` is binary, this
   does not invalidate the rows — but a "pass" on them means only *deep-research stayed silent*,
   never *the right neighbour took it*. Do not read those three as evidence the boundary routes.
   Worth a look in its own right (dimensions 1 and 6): the shipped description instructs the router
   to defer to a sibling that is not installed, so `neg-08`/`neg-15` can never be satisfied the way
   their `boundary` field describes.
5. **`neg-08` ≡ `neg-15` verbatim.** The supersession convention (`rubric.md:47`) appends a
   successor while retaining the original unedited — correct by that contract, but the two rows
   share a prompt, so they are guaranteed to return the identical verdict and cannot diverge.
   30 rows carry **29 bits**; the "≥14/15 negatives" bar counts one probe twice.
6. **`NO_VERDICT` is a harness artifact, not a routing miss.** The runner documents that only opus
   reliably obeys the one-token format guard; sonnet/haiku often return "" or prose
   (`:26-29`, `:73-91`). Read `no_verdict_counts` before scoring dimension 1, and exclude
   NO_VERDICT cells from the denominator rather than counting them as misses.
7. **The synthetic corpus is far easier than production.** The index built for this run has
   **28 entries** (`~/.claude/skills/*/SKILL.md` + the target). The live session index is roughly
   **6× larger**: 133 further `SKILL.md` files are installed under `~/.claude/plugins/`, plus
   project-local skills and 5+ user-scope commands — none of them in the index the router sees
   here. Routing precision measured this way is **optimistically biased**: fewer competitors means
   fewer chances to mis-route. A clean 30/30 licenses no claim about real-session routing.
8. **`sycophancy-probes.jsonl` (5) and `benchmark-testset.jsonl` (5) are executed by nothing**
   (`CHANGELOG.md:41`, author-declared). Not reachable via `--suite`; no substitute proposed —
   the benchmark set is a 4-weekly manual cadence by design.
9. **This run measures the pre-existing description, not the commit.** `11a0439` does not touch
   `SKILL.md`, so dimensions 1, 2, 3 and 7 grade the state left by `1f10507`. That makes the
   loading run a *re-measurement* (the spec noted none exists dated 2026-08-05), not a test of
   this change. Token budget is likewise author-reported (index 171 tok, load 7,199 tok vs a
   7,500 hard cap — **4 % headroom**); `token_budget.py` should re-measure rather than inherit.
10. **The bundled sibling `suggest-tooling/` is ungraded.** It is a separate skill with its own
    `SKILL.md`, `evals/{loading,e2e}.jsonl` and rubric, out of scope per the spec. Neither the
    static scripts (verified above) nor this plan touch it.
11. **README/SKILL.md drift unassessed.** The 40 KB `README.md` was deliberately not read by the
    Analyst (harness-guide §3 makes it supplementary). Unchanged by this commit; still unmeasured.

## Substitute coverage — the target's own deterministic layer

The e2e suite is unexecutable by the harness runner, but the **target ships its own CI**, and it
covers the substance of this commit's checks 4 and 5. The Critic should run it and cite the
result as dimension-4 evidence — it is real, deterministic, and cheap (~seconds, no model calls,
no network except where noted):

```bash
cd /home/ouroz/.cache/dr-worktrees/github-topic-facet
bash tests/check-solution-space.sh          # 12 expectation rows; the row added by this commit is
                                            #   oss-prose-only|open-source: status 'swept' requires
                                            #   >=1 GitHub-native query
bash tests/check-osint-gates.sh
bash tests/check-cross-references.sh
bash tests/check-provenance.sh
bash tests/check-example-invariants.sh
bash tests/check-newsletter-search.sh
bash tests/check-marketplace-rank.sh
python3 -m py_compile scripts/*.py suggest-tooling/scripts/*.py
python3 scripts/verify_gates.py check-solution-space \
        --manifest examples/eu-ai-act-2026/research-solution-space.json
```

Confirmed present: **13 fixtures** under `tests/fixtures/solution-space/` (1 golden `valid.json`
+ 12 single-mutation violations, `oss-prose-only.json` being this commit's addition), and
**12 expectation rows** in `check-solution-space.sh` — the header comment's "twelve" and the
fixture count agree.

**Conditional:** `bash tests/check-schema.sh` shells out to `npx ajv-cli` and needs network on a
cold npx cache. If it fails, record it as an environment gap, **not** a schema violation.

## Static-only fallback

Not applicable here — `claude` is on PATH and the cli backend needs no API key, so dimension 1
gets real cross-model data. Retained for completeness: were dynamic testing skipped, the Critic
would grade dimensions 1, 2, 4, 5, 6 from static signals only (lint, budget, conflict, file
inventory), and dimension 1 would have to be scored conservatively.

## Skill-specific variations for the Critic

- **Dimension 4 (Eval coverage, 1.5×) is the crux of this commit.** Grade the **executability** of
  the new fixture, not its presence. `e2e-15` is well-formed, specific and mechanically worded —
  and lands in a suite the shipped runner drops on the floor. Presence of a fixture that nothing
  executes is a weaker guarantee than the row's wording implies.
- **Adjudicate the edited golden fixture; do not merely restate it.** `tests/fixtures/solution-space/valid.json`
  was **edited** (a prose query replaced by two GitHub-native ones) so it would keep passing under
  the new Rule 7b. `evals/rubric.md:45` forbids editing existing fixtures to make a failing run
  pass ("that is eval laundering"); `evals/rubric.md:3` scopes that document to the three fixture
  sets **under `evals/`**, and the edited file lives under `tests/`. The author documents the
  reasoning in `gotchas-log.md` ("the golden fixture carried the defect itself"). Both readings are
  defensible — harness-guide §8.2 applies. Reach a verdict with file:line on both sides; do not
  assert a violation without engaging the scope argument, and do not dismiss the shape of the
  action because a directory boundary technically exempts it.
- **Dimension 5 (Append-mostly hygiene, 1.0×): a self-declared waiver is present.** The
  `gotchas-log.md` Guard field states outright that items 1 and 2 of the rubric's "Adding fixtures"
  contract (a positive loading fixture; a territorial-neighbour negative) were **not** added,
  arguing the change alters no routing surface. Check that against `rubric.md:39-43`, whose item 1
  is conditioned on "*if it changes the description*" — and the description is verifiably unchanged
  by this commit. Grade the waiver's validity, not its existence.
- **Dimension 1 (Routing precision, 2.0×): apply the pass bars from the target's own rubric**
  (`evals/rubric.md:15`) — ≥14/15 positives **and** ≥14/15 negatives, with `neg-07`/`neg-08`/`neg-15`
  failures blocking regardless of aggregate — but temper any conclusion with gaps 4, 5, 6 and 7
  above. Per-model breakdown, never a pooled average: pooling 3 models hides a single-tier collapse.
- **Do not score this commit on dimensions it does not touch.** `SKILL.md`, `loading.jsonl`,
  `progressive.jsonl`, `references/solution-space.md`, the schema and the CI workflow are all
  untouched by `11a0439`. Findings there are pre-existing state — label them as such rather than
  attributing them to this change.
- **Verify the commit's own claim.** The message asserts "Suite complète verte, schémas valides";
  the Analyst explicitly did not execute it. The §Substitute-coverage block is exactly the
  evidence needed to confirm or refute that sentence.
