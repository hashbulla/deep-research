# Skill Harness Review — deep-research — 2026-08-17

> Run **#6**. Target: branch `chantier/AI-372-v1x-dettes`, HEAD `3e715fa`, 5 commits, **not pushed**.
> Confidence **MEDIUM** — no `hero-queries.md`, so the spec is SKILL.md-anchored, with the
> 31-row live-measured `evals/loading.jsonl` as a strong secondary signal.
> **Verdict: PASS — 8.58/10, qualified.** Routing verified **on opus only**.

**Inferred spec, in one paragraph.** `deep-research` runs a fixed 7-phase pipeline over the open
web with the Tavily MCP suite as its mandatory retrieval spine, every other source (GitHub,
academic APIs, Context7, a local newsletter corpus, stealth OSINT) strictly optional and gated
per sub-question. Its one hard rule is plan-before-retrieval (A1) — and explicitly *not* a human
approval halt. Sources pass an ordered grading battery then an LLM rerank; every claim is routed
by its Admiralty credibility rather than uniformly. A run emits **exactly five artifacts**,
written atomically at the end of Phase 6, and answers with two deliverables rather than one (the
access-gate verdicts plus a universal solution-space manifest). It runs autonomously, pausing at
most once, verifies itself with decorrelated judges plus deterministic scripts whose JSON
verdicts must be quoted verbatim, and treats every retrieved byte as untrusted data.

Two spec facts govern how this run was scored: the body `Trigger` section is **not** a routing
surface (only the frontmatter `description` is), and `research-run-accounting.json` is **run
metadata, not a sixth artifact**.

## Scores

| Dim | Object | Weight | Score | |
|---|---|---|---|---|
| D1 | Description routing precision | 2.0× | **8.5** | PASS |
| D2 | Tax-test compliance | 1.5× | **7.5** | PASS |
| D3 | Token-budget hygiene | 1.5× | **7.0** | PASS |
| D4 | Eval coverage | 1.5× | **9.5** | PASS |
| D5 | Append-mostly hygiene | 1.0× | **9.5** | PASS |
| D6 | Cross-skill territorial conflicts | 1.0× | **9.5** | PASS |
| D7 | Description economy | 1.0× | **9.5** | PASS |

**Weighted overall = 81.50 / 9.5 = 8.58.** No dimension below 5.0; the D1 loading matrix ran, so
the rubric's "Incomplete" clause does not apply. **0 CRITICAL · 6 WARNING · 13 ADVISORY · 1
UNKNOWN.**

## The measurement that matters most

The branch is **−59 lines and +41 tokens**. Reconstructed commit by commit with the same encoder
`token_budget.py` uses:

| rev | what | lines | load tok |
|---|---|---|---|
| `origin/main` | branch point | 210 | 7,199 |
| `9831ce9` | dead-sibling clause removed | 210 | 7,199 |
| `8623fa3` | 209 → 150-line compression | 151 | **7,099** |
| `3e715fa` | HEAD (run-accounting step) | 151 | **7,240** |

The 28 % line reduction bought **1.4 % of tokens**; the accounting step then added **+141**. The
commit message's "net-zero lines" is true exactly as written — and the branch is its own
counter-example to the gate it introduced.

## Findings — WARNING (6)

Full text with all citations: `findings_cited.md` (staging). Condensed here.

**[DIM-1-01] Matrix covers opus only** — `loading_matrix.json:4-6`. The package's sharpest change
is the routing prompt, and this skill's historical leak lived on **sonnet** (run #4 `neg-08`;
gotchas-log.md:39 records the same cell leaking on sonnet *and* haiku under ablation). Fix: run
`--models opus,sonnet,haiku` before any release tag; require ≥14/15 positives and ≥15/16
negatives per model. **Do not publish "routing verified" — publish "verified on opus".**
> *Skills for enterprise*, platform.claude.com — "Require testing across the models your
> organization uses (Haiku, Sonnet, Opus), because Skill effectiveness varies by model."
> *Skill authoring best practices*, platform.claude.com — "What works perfectly for Opus might
> need more detail for Haiku." · *Demystifying evals*, anthropic.com — "we run multiple trials".

**[DIM-2-01] No `## Examples` section** — lint check#13, SKILL.md:7. Deliberate and documented
(the section was folded into `## References` during the compression, content verifiably intact at
`references/examples.md`, 1,481 tok, with its read-moment preserved). A body-contract deviation,
not content loss. Fix: restore `## Examples` carrying only the pointer sentence, and delete that
clause from the References bullet — pair with DIM-2-02, which frees the line.
> *Agent Skills overview*, platform.claude.com — the canonical SKILL.md template carries exactly
> two body headings, `## Instructions` and `## Examples`. · *The Complete Guide to Building
> Skills*, anthropic.com — "Examples provided" is a pre-upload checklist item.
> **Contradicting evidence (surfaced, not applied):** agentskills.io/specification — "There are
> no format restrictions", `Examples of inputs and outputs` sits under *Recommended sections*, and
> only `name`/`description` are Required. **No body section is required by the published spec.**
> Severity stays WARNING: the finding's authority is the generator's required-section contract,
> not the spec. **Victor adjudicates** whether a generator-local rule the spec does not mandate
> deserves WARNING weight.

**[DIM-3-01] The documented budget justification is stale** — CHANGELOG.md:21, :27 quote "7,199
tok … 301 tok of headroom"; HEAD measures **7,240 / 260**. The substance survives, the figures do
not — and that entry exists *because* of the run-#3 failure for not re-measuring. Fix: append one
line recording 7,240 (was 7,199 pre-branch, 7,099 post-compression).
> agentskills.io/specification — "Instructions (< 5000 tokens recommended)". ·
> research.perplexity.ai — "once you load a Skill, the rest of the conversation has to pay that".
> · agentskills.io/skill-creation/evaluating-skills — figures carried forward from a prior
> iteration are not evidence for the current one.

**[DIM-3-02] The new budget gate counts lines; nothing counts tokens** —
`tests/check-skill-length.sh:16` (`wc -l`, limit 150), wired at `validate.yml:30-31`. Verified:
`grep -rln "token_budget\|LOAD_HARD\|7500" tests/ .github/` returns **nothing**. A future
densification can pass 150 lines while pushing the load tier through 7,500 unobserved. Fix: add a
`token_budget.py --json` CI step after the length check; **keep** the line gate — it guards
attention, which a token gate does not.
> agentskills.io/specification and platform.claude.com/overview — both denominate the activated
> body in tokens ("Under 5k tokens"). · research.perplexity.ai — "the unit of account for what
> the model pays is the token".
> **Contradicting evidence (surfaced, not applied):** platform.claude.com best-practices titles
> its section **"Token budgets"** and states the rule in **lines** ("under 500 lines");
> agentskills.io/skill-creation/best-practices publishes both as **co-equal** ("under 500 lines
> **and** 5,000 tokens"). So a line gate has direct vendor backing. It does not rebut the
> finding: two caps are published, **one** is gated, and this branch proves they can move in
> opposite directions.

**[DIM-4-01] Two eval files are executed by nothing** — `sycophancy-probes.jsonl` and
`benchmark-testset.jsonl`; `run_evals.py --suite` accepts only `loading|progressive|e2e`. The
latter carries a declared 4-weekly re-validation cadence no runner reads, so its staleness can
never surface mechanically. Fix: relocate both to `evals/manual/` so non-executability is visible
from the path, and name in `rubric.md` who runs them and when.
> agentskills.io/skill-creation/evaluating-skills — assertions bind fixtures to execution and
> grading. · *Demystifying evals*, anthropic.com — "A grader is logic that scores…"; a fixture no
> runner names has no grader. · *Skills for enterprise* — "Evaluation results signal when to act".

**[DIM-6-01] The description names no skill peer at all** — SKILL.md:3 lists two tools and one
slash command. The peer the router *empirically chooses* on this skill's own release-blocker
boundary (`superpowers:dispatching-parallel-agents`) lives only in a fixture `boundary` and in
`rubric.md` — in the **test contract**, not on the **routing surface**. Fix: **do not edit on the
current n=1 evidence.** Run the n≥3 measurement DIM-1-02 owes; if `neg-16` leaks on any model at
≥1-in-3, add the peer by name (346 chars of headroom under the cap).
> *The Complete Guide*, anthropic.com — the published remedy for over-triggering names the
> competing **skill** on the description ("Do NOT use for … (use data-viz skill instead)"). ·
> *Skills for enterprise* — "Does adding this Skill degrade other Skills?" ·
> agentskills.io/skill-creation/optimizing-descriptions — "The most valuable negative test cases
> are near-misses."

## Findings — ADVISORY (13) and UNKNOWN (1)

Not repeated here; see `findings_cited.md`. The ones that change future work:

- **DIM-3-03** — "densifying" moved the budget 1.4 %. The lever that actually worked historically
  was **progressive disclosure** (10,036 → 7,199 by relocating three sections). Next reduction:
  relocate, don't densify.
- **DIM-4-02** — `run_evals.py` reads `entry["prompt"]`, absent from `progressive.jsonl` and
  `e2e.jsonl`, so both suites skip every row and report `[]` — indistinguishable from a perfect
  score. Consequence: **`e2e-16` is unexercised**, and its load-bearing half is the negative one.
- **DIM-5-01** — the same-day paperwork says "8 local gates PASS" (gotchas-log) and "9 local gates
  PASS" (CHANGELOG); the workflow runs 11 `tests/*.sh` plus 3 direct steps. A count in prose rots
  on every added test — replace both with the command that produces it.
- **DIM-7-02** — removing the dead clause left a parenthesis that opens at `(use /research` and
  never closes, so it now carries both the redirect target and the skill's positive
  self-description. Character-neutral fix proposed; **re-measure loading after it** — it touches
  the routing surface.
- **DIM-7-01 [UNKNOWN]** — is `calibrated to Perplexity Deep Research (100+ sources…)` a no-op?
  No fixture rides on it, but it is the only signal of *scale*, the discriminator against
  `/research`. Genuinely undecidable without a stub-ablation instrument. Settle it the way this
  repo settled the FR trigger: one ablation variant, full suite, n≥3.

## Coverage gaps

- **No sonnet, no haiku.** The single sharpest gap, and vendor-documented as a requirement.
- **n=1 per cell**, against a router this repo has *measured* drifting (4 of 90 cells in 9 days on
  a byte-identical description).
- **Only `loading` executed.** `e2e` (16 fixtures) and `progressive` (13) are statically checked
  only, and DIM-4-02 explains why they cannot run at all today.
- **Self-referential oracle** — the 15 positives were authored from the description they grade.
- **Peer set is user-scope only** (20 skills); plugin- and project-scope peers are invisible to
  `conflict_check.py`, which is exactly why the dead-sibling debt needed a hand-rolled grep.
- **`token_budget.py` measures the body only** — the real Phase-0 floor is ~7,240 tok on a
  not-applicable geometry and ~**11,674** on an applicable one (body + `solution-space.md`).
  Neither figure is gated by anything.

## Fix-session instructions

Cheapest high-value first. An autonomous follow-up session can take 1–3 without further input.

1. **DIM-3-01** — append the re-measured load-tier line to the `[Unreleased]` accounting entry.
   Restores the measurement property that entry exists to carry. One line.
2. **DIM-2-01 + DIM-2-02, paired** — delete the redundant Artifact sentence at SKILL.md:14 (it
   duplicates :118 and :124, which each do distinct work), then restore `## Examples` with the
   pointer sentence. Line-neutral by construction, so the 150-line gate still passes.
3. **DIM-3-02** — add a `token_budget.py --json` step to `validate.yml` after the length check.
   Keep the line gate. This closes the gap the branch itself demonstrated.
4. **DIM-1-01 (needs a decision, not just execution)** — run the 3-model loading suite. It also
   settles DIM-1-02 (n≥3), DIM-6-01 (peer naming) and DIM-7-01 (the Perplexity clause).
5. **DIM-4-01** — relocate the two unexecuted eval files to `evals/manual/` and name their owner
   and cadence in `rubric.md`.

**Do not** edit the description on n=1 evidence (DIM-6-01, DIM-7-01 both defer to measurement).
**Do not** commit this REVIEW.md as part of the feature branch without deciding where run #6 gets
archived — the repo's convention is `docs/harness/<date>-run<N>/`.

## Recursion check

Not applicable — the target is `deep-research`, not `skill-generator` or `skill-harness`.

## Process deviations, declared

1. **The four harness agents are not registered as agent types in this session.** Each judgement
   phase was run as an isolated `general-purpose` agent with its full definition inlined; the
   Critic ran under `isolation: worktree`. Context isolation and the structural Analyst/Critic
   separation are preserved; the invocation path is not the nominal one.
2. **The Critic could not write its own findings file** — two independent guards refused (subagent
   report-file policy, and worktree isolation for a redirect outside the worktree). The
   orchestrator materialised it verbatim from the Critic's return value.
3. **Gate 3 was folded into Gate 1**, and `strategy.md` was authored by the orchestrator: the user
   had already decided the only question the Strategist had latitude over (matrix scope).
4. **The matrix's oracle was defective at first run and fixed mid-flight.** `derive_oracle` took
   the *folder* name; the router only ever answers the *frontmatter* name. Grading a worktree made
   the two diverge, so a perfect 15/15 matrix would have scored 0/15. Fixed in `skill-generator`
   (`b175c5f`) before any D1 evidence was read.

## Calibration log entry

Run **#6**. Trajectory: 6.6 (FAIL) → 8.94 → 6.84 (FAIL) → 7.61 → 7.97 → **8.58**.

The rubric ships **UNCALIBRATED** (`critic-rubric.md:156`) and the guide still records
`calibration_runs: 0`. **This entry increments no counter — the manual human review of run #6 is
owed**, and per Anthropic's harness-design guidance scores are trusted at face value only from
iteration ≥3.

Two consecutive human reviews found this evaluator **too severe** on judgement-heavy dimensions
(run #4 on D3/D4, run #5 on D2/D7), diagnosed as "reads risk *location* well, over-weights risk
*magnitude*". The Critic applied that operationally rather than citing it: D4 graded at its
literal presence tier instead of departing downward for executability (the exact departure a human
overturned at run #4), D7 counting zero slips instead of re-litigating the ablation-closed FR
trigger, and every downward move anchored to a measured defect rather than a worry.

**Prerequisite discovered by this run, for whoever reads the next loading score:** the runner's
`_KEBAB_RE` rejected plugin-namespaced names, so a correct reply fell to `NO_VERDICT` — the exact
defect that produced 3 spurious non-verdicts across runs #4 and #5, on the rubric's own
release-blocker boundary. Fixed in `skill-generator` `89e9c8d` before this run; `neg-16` is
therefore the first link of that succession ever scored on a working instrument.

Scores are indices for comparison against runs #2–#5 on the same uncalibrated rubric, not marks.
