# Skill Harness Review — deep-research — 2026-08-14 (run #5)

> **Calibration status: the harness rubric records `calibration_runs: 0`, and D7 ships uncalibrated.** Scores are not trusted at face value. Prior-run trajectory: 6.6 → 8.94 → 6.84 → 7.61 → **7.97**. Run #4's owed human review was completed by Victor on 2026-08-07 (findings 5/5, verdict confirmed, tier placement judged too severe); the human review of *this* run is owed.

**Verdict: PASS — 7.97 / 10.** 0 CRITICAL · 10 WARNING · 11 ADVISORY · 1 UNKNOWN (22 findings). Pass rule satisfied: overall ≥ 7.0, no dimension below 5.0, and the D1 loading matrix **was** run.

**Confidence: MEDIUM** — spec anchored on `SKILL.md` only (`hero-queries.md` absent). Inferred spec: `deep-research` is a fixed 7-phase agentic research pipeline over the Tavily MCP suite, Perplexity-calibrated (100+ sources on `--length exhaustive`), answering with **two deliverables, never one** — the access-gate verdicts and a solution-space map — emitting exactly five artifacts written atomically at end of Phase 6 plus one private Artifact page; quality machine-verified rather than self-reported; autonomous with exactly one conditional `AskUserQuestion`; self-audited by two decorrelated subagents on a different model.

## Scores

| # | Dimension | Weight | Score | Status | Surface |
|---|---|---|---|---|---|
| 1 | Description routing precision | 2.0× | 8.0 | PASS | **UNMOVED** |
| 2 | Tax-test compliance | 1.5× | 7.0 | PASS | UNMOVED |
| 3 | Token-budget hygiene | 1.5× | 7.5 | PASS | UNMOVED |
| 4 | Eval coverage | 1.5× | 8.0 | PASS | UNMOVED |
| 5 | Append-mostly hygiene | 1.0× | 9.0 | PASS | **MOVED** |
| 6 | Cross-skill territorial conflicts | 1.0× | 9.5 | PASS | UNMOVED |
| 7 | Description economy | 1.0× | 7.5 | PASS | UNMOVED |
| | **Overall (weighted)** | 9.5× | **7.97** | **PASS** | |

## The headline: this run did not grade the change under review

`SKILL.md` is **byte-identical** to run #4's baseline commit `11a0439`. Corroborated mechanically, not asserted: `token_budget.py` returns the same index tier (171) and load tier (7,199) as run #4's archived `budget.json`; `conflict_check.py` returns max Jaccard 0.019 across 31 peers; the description is 725 characters against a 1,024 cap.

Six of seven dimensions therefore grade an unmoved surface. Only D5 moved, and only because two `CHANGELOG.md` entries were added. **The substance of the diff is reached by no rubric dimension**: the tier path in `references/methodology.md` §6, Rule 7c in `verify_gates.py` (+82 lines), the doctrine in `references/github-research.md` §2b, and the fixture pair. The sharpest instance is D4, which grades `evals/` — while the new fixtures landed in `tests/fixtures/solution-space/`.

The Critic executed `tests/check-solution-space.sh` directly: **PASS, exit 0**, the violation fixture trips Rule 7c, the positive control clears with 0 violations, and the purity guards hold across all 16 fixtures. The change is therefore **CI-self-verified and rubric-invisible**.

**Six of the 22 findings are defects in the measuring apparatus, not in the skill.**

## Gate dispositions

| Gate | Disposition |
|---|---|
| Gate 1 — framing | Human-answered. Chose to close three shipping gaps (fixture, regression test, CHANGELOG) **before** grading, on the grounds that the harness gates a finished change and the change was demonstrably unfinished. |
| Gate 2 — spec | Human-confirmed as inferred. The Analyst's three disagreements with run #4's spec were all in the direction of *less* overreach and were accepted. |
| Gate 3 — strategy | Human-answered. Loading matrix to run across opus/sonnet/haiku on the `cli` backend, `--no-cache`, merged 32-skill corpus. |

## Deviations from the prescribed pipeline — declared

1. **The Critic was NOT worktree-isolated.** The skill prescribes `isolation: worktree`. It was run instead as a fresh isolated context with an absolute `SKILL_PATH`. This was deliberate and is **more correct here**: the amendments live on an unpushed branch, and a worktree would very likely have checked out `main` and graded the *pre-amendment* skill while reporting a clean result. Context separation is what defeats self-evaluation bias; filesystem isolation was never the mechanism. **Do not "fix" this back without first proving the worktree resolves to the branch HEAD.**
2. **The Strategist agent was NOT spawned.** The strategy was decided by the human at Gates 1/3 before that phase would have run. `strategy.md` records the executed strategy rather than an inferred one.
3. **Citation Grounding was scoped to avoid citation theater.** Findings proven by a file the run read or a command it executed carry a `Grounded:` block naming file:line instead of an external URL. Only findings asserting an external norm carry `Citations:`.

## Contested finding — human adjudication required

**`DIM-3-02`** — scoped to two words of its own wording. The finding calls the 7,500-token load tier an "auto-CRITICAL **spec** breach". No published source sets a 7,500-token body cap; the specification gives 5,000 as a *recommendation*. The threshold is correctly sourced to `critic-rubric.md:53` — the Critic invented nothing — but `critic-rubric.md:51` disclaims that word in the harness's own voice ("hygiene targets, **not spec gates**"). **The finding stands at WARNING regardless**, and the external norm is in fact *stricter*: 7,199 already exceeds the recommended 5,000 by 44%.

## Defects found in the harness itself

These belong to whoever owns `skill-harness`, not to `deep-research`:

1. **`run_evals.py:64` — `_KEBAB_RE` rejects plugin-namespaced skill names.** `^[a-z0-9]+(?:-[a-z0-9]+)*$` admits no colon, so a well-formed reply like `superpowers:dispatching-parallel-agents` falls through to `NO_VERDICT` — a bucket its own docstring reserves for "empty, prose, or otherwise non-conforming" replies. Correctly classified, that cell is a **hit**. This has produced 3 spurious `NO_VERDICT`s across runs #4 and #5, and it mis-scores *every* skill this harness grades. Documentation confirms the namespaced form is canonical, and the same defect also swallows nested project-scope names such as `apps/web:deploy`. One-line fix.
2. **`run_evals.py:402` reads `expected_skill`, a key `evals/loading.jsonl` does not contain.** The fixture keys on `expect ∈ {load, skip}`; the key union is exactly `['boundary','expect','id','prompt']`. Every matrix row therefore records `expected_skill: null`, which by convention encodes "nothing should fire" — so a literal reading scores all 15 correct positive fires as misses. **Run #4's D1 was graded against an all-null expectation column.** This is a shared script outside this skill, matching the precedent already recorded in the CHANGELOG's known limitations.
3. **`critic-rubric.md` footnote `[^10]` 404s** — the authority for all of D2, this run's lowest dimension. The live URL needs the `-at-perplexity` suffix.
4. **`critic-rubric.md:51` and `:53` contradict each other** on whether token tiers are spec gates. This is the root of the contested finding above.
5. **The Critic's own severity table miscounts** — it reports 10 ADVISORY / 21 findings; the body carries 11 / 22 (`DIM-6-02` is absent from the ADVISORY row). Denominator verified mechanically. The WARNING count of 10 is exact, so citation scope was unaffected.

## Routing measurement (D1) — joined against a valid oracle

Because the matrix carries no usable expectation column, verdicts were joined to the fixture's own `expect` field. Prompt alignment was proven before joining — 30/30 identical across the fixture file, run #4's matrix and run #5's — rather than assumed from row position. A `skip` row whose verdict names a *different real skill* is scored a **PASS**: the fixture asserts "deep-research must not fire", not "nothing fires".

| Model | PASS | MISS | LEAK | NO_VERDICT |
|---|---|---|---|---|
| opus | 30 | 0 | 0 | 0 |
| sonnet | 29 | 0 | 1 | 0 |
| haiku | 29 | 0 | 0 | 1 |

The single sonnet leak lands on `neg-08` — a fixture the CHANGELOG explicitly marks **superseded** by `neg-15` (it encoded the retired four-artifact contract) and retains only under the append-only rule. Its successor passes.

**Router drift, measured.** Against a byte-identical description and identical fixtures nine days apart, **4 of 90 verdict cells changed**. The skill did not move; the router did. Any single matrix is a point-in-time reading, not a property of the skill — which is exactly why n=1 is held to lie on routing questions.

**D1's oracle is self-referential.** `hero-queries.md` is absent, so the loading prompts were author-authored *from* the description. The harness guide's stated mitigation for the description-self-grading failure mode is unavailable for this skill. Grading D1 from the matrix anyway, with the limitation labelled, was a human decision taken at Gate 2.

## Fix-session instructions

For an autonomous follow-up session, in priority order:

1. Fix `_KEBAB_RE` in `run_evals.py` to admit one optional `plugin:skill` namespace segment, and add a fixture asserting a namespaced reply classifies as a verdict rather than `NO_VERDICT`. Re-run the matrix; expect haiku at 30/30.
2. Teach `run_evals.py` the `expect ∈ {load, skip}` schema, **or** emit an explicit `NOT_RUN (schema mismatch)` status rather than silently writing `null`. Silence here is indistinguishable from a valid oracle.
3. Reconcile `critic-rubric.md:51` against `:53` on whether token tiers are spec gates, and fix footnote `[^10]`.
4. Author `hero-queries.md` from real invocation history so run #6 has a non-self-referential D1 anchor.
5. Correct the ADVISORY count in the Critic's severity table template.
6. Leave the declared `check-artifacts` FAIL in the Excalidraw research alone — it is intentional and documented.

## Recursion check

Not applicable — the target is `deep-research`, not `skill-generator` or `skill-harness` itself.

## Calibration log entry — owed

Record human-vs-evaluator agreement for run #5 in `CHANGELOG.md` before relying on this verdict. The specific question worth answering: run #4's human review found the evaluator **too severe** on tier placement. This run's D2 (7.0) and D7 (7.5) are the candidates for the same judgement.

---


> Critic phase, worktree-isolated. Target: `/home/ouroz/second-brain/20-engineering/skills/deep-research`, branch `chantier/software-capability-tiering`, HEAD `53c4444` (3 commits ahead of `main` baseline `11a0439`).
> Anchor: `skill_spec.md` (MEDIUM confidence, `SKILL.md`-anchored, `hero-queries.md` absent).
> `SKILL_PATH/REVIEW.md` is a stale run-#2 artifact (gitignored) and was **not** read or used.

---

## Citation pass — Grounding index

> Citation Grounder pass, run 2026-08-14. Scope: **CRITICAL + WARNING only** (0 CRITICAL, 10 WARNING). ADVISORY and UNKNOWN findings are preserved verbatim with no blocks attached, per the cost bound.
>
> **Constitutional rule applied: no severity was softened, and none may be softened downstream.** Absence of a citation never invalidates a finding; contradicting evidence is surfaced in a `Contested:` block for human adjudication, never silently applied. No finding text, ID, severity, score or count below was modified.

Findings split into two classes, treated differently to avoid citation theater:

- **Class 1 — grounded in primary evidence (7 WARNINGs).** The defect is proven by a file the run read or a command it executed. An external URL would add nothing, so each carries a `Grounded:` block naming the file:line instead. `DIM-1-01`, `DIM-1-02`, `DIM-1-04`, `DIM-4-01`, `DIM-4-02`, `DIM-4-04`, `DIM-6-01`.
- **Class 2 — assert an external norm (3 WARNINGs).** Each claims a published specification, platform behaviour or best-practice threshold, and therefore carries a `Citations:` block with retrieval date. All three are *hybrids*: their mechanical half is primary evidence, so they carry a `Grounded:` block as well. `DIM-1-03`, `DIM-2-01`, `DIM-3-02`.

**One `Contested:` block was raised** — `DIM-3-02`, scoped to two words of its wording. See that finding.

### Severity index — recounted from the body

| Severity | Count | Findings | Citation pass |
|---|---|---|---|
| CRITICAL | 0 | *(none)* | n/a |
| WARNING | 10 | DIM-1-01, DIM-1-02, DIM-1-03, DIM-1-04, DIM-2-01, DIM-3-02, DIM-4-01, DIM-4-02, DIM-4-04, DIM-6-01 | **in scope — all 10 carry a block** |
| ADVISORY | **11** | DIM-1-05, DIM-2-02, DIM-2-03, DIM-3-01, DIM-3-03, DIM-4-03, DIM-5-01, DIM-5-02, **DIM-6-02**, DIM-7-01, DIM-7-03 | out of scope (cost bound) |
| UNKNOWN | 1 | DIM-7-02 | out of scope (cost bound) |
| **Total** | **22** | | |

> **Arithmetic discrepancy in the Critic's own summary — surfaced, not corrected.**
> The Critic's severity table (below, at "Severity counts") reports **10 ADVISORY / 21 findings**. Recounting the body's finding headers mechanically returns **11 ADVISORY / 22 findings**: `**[DIM-6-02] [SEVERITY: ADVISORY]**` is present in the body under Dimension 6 but is **absent from the Critic's ADVISORY row**. Two downstream statements inherit the wrong denominator: "*Severity counts: ... 21 findings*" and "*Six of twenty-one findings are about the measuring apparatus*" — in both, **22 is the measured figure**.
> *Scope of this correction:* only the **denominator** was verified mechanically (a header recount). The instrument-defect **numerator** is left unadjudicated — the sentence enumerates six IDs and "six" matches its own enumeration, but whether that enumeration is exhaustive is a scoping judgment, and two further findings label themselves harness-scoped in their own parentheticals without appearing in it (`DIM-3-01`, "*rubric gap*"; `DIM-7-03`, "*evaluator-drift note, not a defect of the skill*"). Flagged for the human, not resolved here.
> Per the append-only constraint the Critic's table is left **exactly as written**; this note is the correction record. **No severity changes** — DIM-6-02 was and remains ADVISORY, so it is correctly outside this pass's scope either way, and the **WARNING count of 10 is confirmed exact**, so the citation scope is unaffected.

The document below is the Critic's `findings.md`, verbatim and in its original dimension order, with blocks attached in place. Nothing was deleted, reordered, reworded or re-severitied.

---


## Static-check summary

- **`lint_skill.py`**: exit 0 — **0 errors, 2 warnings, 0 infos**.
  - `check#16` (examples concreteness) `SKILL.md:185` — 0 `**Input:**` / 0 `**Output:**` blocks. **Maps to no rubric dimension** and is defensible: `SKILL.md:187` deliberately offloads worked examples to `references/examples.md` + `examples/eu-ai-act-2026/`, which is the behaviour D2 *rewards*. No penalty applied.
  - `check#18` (cross-platform) `SKILL.md:53` — `~/.claude/` paths with no `compatibility:` declaration. Consumed as D2 evidence (DIM-2-03); it is a WARNING, so harness-guide §6's auto-penalty does not fire.
  - `check#17` ("reserved name") did **not** fire this run — run #4's single verdict-critical false positive was an artefact of its worktree directory name (`lint_skill.py:441-442` skips self-collision when `name == folder_name`). Verified absent from `lint.txt`.
- **`token_budget.py`**: index = **171 tok** (target 100, hard 320) · load = **7,199 tok** (target 5,000, hard 7,500) · files = 106,524 tok reported. Two WARNINGs, no errors.
  - **Files-tier number is contaminated and unscored.** ~16.9k tok of the reported files tier is gitignored `__pycache__/*.pyc` (`git check-ignore` → `.gitignore:25`), written by a `py_compile` step this session. Clean files tier is approximately 70k tok. The rubric sets **no files-tier threshold**, so this is a reporting artefact with zero score impact.
- **`conflict_check.py`**: exit 0 — **max Jaccard = 0.019**, 31 peers, **0 critical conflicts**. Corpus was a deliberately-hardened merged farm (32 skills, user-scope + project-scope) per `strategy.md`.
- **`run_evals.py --suite loading`**: executed, cli backend (`claude -p`), `--no-cache`. **90/90 cells returned.** `no_verdict_counts` = `{opus: 0, sonnet: 0, haiku: 1}`. See DIM-1-03 — that single NO_VERDICT is **spurious**.
- **`tests/check-solution-space.sh`** (executed by me, read-only): **PASS, exit 0**, including `ok: agentic-no-skill-query -> requires >=1 agent-skill-class query`, `ok: 7c control exits 0`, `ok: 7c control has 0 violations`, and 7c purity guards across all 16 fixtures. The CHANGELOG's "Red-ability verified by ablation" claim for Rule 7c is **corroborated by executed test**.

---

## Per-dimension scores

| # | Dimension | Weight | Score | Verdict | Change under review |
|---|---|---|---|---|---|
| 1 | Description routing precision | 2.0x | **8.0** | PASS | **UNMOVED** — `SKILL.md` byte-identical to `11a0439` |
| 2 | Tax-test compliance | 1.5x | **7.0** | PASS | **UNMOVED** — body byte-identical |
| 3 | Token-budget hygiene | 1.5x | **7.5** | PASS | **UNMOVED** — index + load tiers byte-identical |
| 4 | Eval coverage | 1.5x | **8.0** | PASS | **UNMOVED** — 0 files under `evals/` changed |
| 5 | Append-mostly hygiene | 1.0x | **9.0** | PASS | **MOVED** — `CHANGELOG.md` +2 |
| 6 | Cross-skill territorial conflicts | 1.0x | **9.5** | PASS | **UNMOVED** — description identical so Jaccard identical |
| 7 | Description economy | 1.0x | **7.5** | PASS | **UNMOVED** — description byte-identical |

**Six of seven dimensions grade an unmoved surface.** Exactly one rubric input (`CHANGELOG.md`) was touched by the three commits. Recorded as a rubric-coverage finding (DIM-4-04), not a skill defect.

---

### Dimension 1 — Description routing precision (weight 2.0x)

**Score: 8.0 / 10** — **UNMOVED surface.** `git diff 11a0439 HEAD -- SKILL.md` is empty; the frontmatter `description` this dimension grades is byte-identical to run #4's baseline. Nothing in the three commits can have moved D1. The matrix below re-measures an unchanged routing surface.

**Oracle derivation (required disclosure).** I derived the oracle **from the fixture file, not the matrix**. The field used is **`expect` in {`load`,`skip`}** in `evals/loading.jsonl`, joined to matrix rows by `prompt` (cross-checked positionally: all 30 positions align). I used `expect` because it is the **only** oracle-bearing field that exists — the fixture's key union is exactly `['boundary','expect','id','prompt']`. Distribution: 15 `load`, 15 `skip`.

**Structural checks (all pass):** description = **725 / 1024 chars**, single unfolded scalar; third-person; **no XML angle brackets**; explicit `Do NOT load for...` clause naming four boundaries and two peer owners (`SKILL.md:3`). Lint checks 4-8 clean.

**Measured matrix (oracle = fixture `expect`; NO_VERDICT excluded from hit/miss per rubric D1):**

| Model | Positives (15) | Negatives (15) | Real defects | NO_VERDICT |
|---|---|---|---|---|
| opus | 15/15 | 15/15 | **0** | 0 |
| sonnet | 15/15 | 14/15 | **1 negative leak** (`neg-08` -> `deep-research`) | 0 |
| haiku | 15/15 | 14/14 real | **0** | 1 (`neg-08`) |

Rubric tier 8 is the literal fit: *"One model has 1-2 positive misses or 1 negative leak (real verdicts, not NO_VERDICT). Otherwise clean."*

Findings:

**[DIM-1-01] [SEVERITY: WARNING]**
File: `/tmp/skill-harness-1786648836/loading_matrix.json` (all 30 `suites.loading[]` rows) vs `evals/loading.jsonl:1-30`
Finding: **The matrix encodes no oracle at all.** Every row carries `expected_skill: null`, `expected_reference: null`, `category: null` — verified by count: 0/30 non-null on each. `run_evals.py` reads `entry["expected_skill"]`, a key that **does not exist anywhere** in `loading.jsonl` (key union = `boundary`, `expect`, `id`, `prompt`). A consumer scoring D1 from the matrix's own expectation fields would grade against `null` on every row and could report neither a miss nor a leak.
Impact: the machine output of the D1 instrument is not self-describing. A Critic that trusted it would silently produce a vacuous pass — the exact false positive the D1 coverage-gap ceiling exists to prevent, arriving through a different door (matrix present but oracle-free rather than matrix absent).
Recommendation: in `~/.claude/skills/skill-generator/scripts/run_evals.py`, make the loading-suite reader fall back to `entry.get("expect")` and emit it into each row as `expected_load: true|false`, so the matrix carries its own oracle; failing that, add a line to `critic-rubric.md` D1 Inputs stating the oracle MUST be joined from `evals/loading.jsonl` `expect` and that matrix `expected_skill` is inert for this fixture schema.

**Grounded: primary evidence — no external citation applicable.**
`/tmp/skill-harness-1786648836/loading_matrix.json` (30/30 `suites.loading[]` rows with `expected_skill: null`) × `evals/loading.jsonl:1-30` (key union `boundary`/`expect`/`id`/`prompt`) × `run_evals.py` (reads `entry["expected_skill"]`). This is a key-presence defect in files the run read directly; it asserts no published norm, so an external source would dilute rather than anchor it.
**[DIM-1-02] [SEVERITY: WARNING]** *(SUSPECT — proxy artefact per rubric D1 nearest-neighbour clause)*
File: `evals/loading.jsonl:21` (`neg-08`, `expect: skip`) -> `loading_matrix.json` row 21, `verdicts.sonnet = "deep-research"`
Finding: sonnet fired `deep-research` on `"fan out a bunch of research agents on this topic and just give me the gist, no plan needed"` — a prompt whose `boundary` names it a **release-blocker territorial negative** (`evals/rubric.md:15`: *"A single negative failure on `neg-07`, `neg-08` or its successor `neg-15` ... is a release blocker regardless of the aggregate"*). This is the one real routing defect in 90 cells.
Two qualifications, neither retiring the finding: (1) the prompt **grazes** the target's own domain ("research", "agents"), and haiku routed the identical prompt to `superpowers:dispatching-parallel-agents` — plausibly the correct owner — so the rubric's nearest-neighbour over-fire clause (AI-319 #6) applies and the leak is labelled **SUSPECT**, a proxy-framing artefact rather than a proven description defect; (2) it is **not reproducible** (DIM-1-04). It is nonetheless a real verdict naming the target on a should-skip prompt, and I do not discount it.
Impact: against the skill's own release bar, a single occurrence of this cell is a release blocker. Measured once in 90 cells and once in 4 measurements of this cell.
Recommendation: do not edit the description on n=1. Re-run `run_evals.py --suite loading` with **n>=3 per cell** restricted to `neg-07`/`neg-08`/`neg-15`; if the leak rate on `neg-08`/sonnet exceeds one in three, add an explicit "fan-out / parallel-agent dispatch" term to the description's `Do NOT load for` clause naming `superpowers:dispatching-parallel-agents` as owner (see DIM-6-01).

**Grounded: primary evidence — no external citation applicable.**
`loading_matrix.json` row 21 (`verdicts.sonnet = "deep-research"`) against `evals/loading.jsonl:21` (`expect: skip`). The "release blocker" norm the finding invokes is the **target's own** contract at `evals/rubric.md:15`, a local file the run read — not an external standard. Grading a skill against its own declared release bar needs no outside authority.
**[DIM-1-03] [SEVERITY: WARNING]** *(instrument defect — root cause new; run #4 misattributed it)*
File: `~/.claude/skills/skill-generator/scripts/run_evals.py:64` (`_KEBAB_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")`) and `:89-91`
Finding: haiku's single `NO_VERDICT` is **not** an empty, prose or non-conforming reply. The raw response is `superpowers:dispatching-parallel-agents` (`loading_matrix.json` row 21, `responses.haiku`) — a **well-formed, correctly-namespaced Claude Code skill name** in the `plugin:skill` form the platform actually uses. `_KEBAB_RE` admits no `:`, so `classify_verdict` falls through to `NO_VERDICT` at `:91`, contradicting its own docstring at `:82` (*"empty, prose, or otherwise non-conforming"*). Correctly classified, the cell is a **HIT** (a should-skip prompt routed away from the target). The same reply was rejected **twice** in run #4 (`docs/harness/2026-08-05-run4/loading_matrix.json` rows 21 and 30) — 3 spurious NO_VERDICTs across two runs, always on the same reply.
The irony is load-bearing: the reply the classifier cannot represent is a **plugin-namespaced skill name**, and the target's own description (`SKILL.md:3`) names *"the plugin-namespaced deep-research sibling"* as a boundary. The instrument cannot express the very naming form the routing surface is written against.
Impact: real routing successes are booked as harness coverage gaps, which (a) suppresses credit the target earned, and (b) makes the target's raw pass bar (`evals/rubric.md:15`, ">=14/15 negatives") arithmetically unreachable for haiku. Run #4's remediation row 3 diagnosed this as a **bar-formulation** problem; that treats the symptom. The root cause is the regex.
Recommendation: change `run_evals.py:64` to `^[a-z0-9]+(?:-[a-z0-9]+)*(?::[a-z0-9]+(?:-[a-z0-9]+)*)?$` so a single `plugin:skill` namespace segment classifies as a real verdict; add a unit case asserting `classify_verdict("superpowers:dispatching-parallel-agents")` returns the name, not `NO_VERDICT`.

**Grounded: primary evidence (mechanical half).**
`~/.claude/skills/skill-generator/scripts/run_evals.py:64` (`_KEBAB_RE` admits no `:`), `:82` (docstring claiming "empty, prose, or otherwise non-conforming"), `:89-91` (fall-through to `NO_VERDICT`), and `loading_matrix.json` row 21 `responses.haiku`. The regex behaviour and the docstring contradiction are proven by the file.

**Citations (norm half — that `superpowers:dispatching-parallel-agents` is a well-formed platform identifier, not a malformed reply). Retrieved 2026-08-14:**
- *Plugins in the SDK — Claude Code Docs.* https://console.anthropic.com/docs/en/agent-sdk/plugins — "Skills from plugins are automatically namespaced with the plugin name to avoid conflicts. To invoke one directly, send `/plugin-name:skill-name` as the prompt." (Tier 1, Admiralty A1)
- *Extend Claude with skills — Claude Code Docs.* https://docs.anthropic.com/en/docs/claude-code/skills — name-resolution table: "Plugin `skills/` subdirectory | Frontmatter `name` or the directory name, namespaced by plugin | `my-plugin/skills/review/SKILL.md` → `/my-plugin:review`". The same `<namespace>:<skill>` form is *also* emitted for nested project-scope skills: `apps/web/.claude/skills/deploy/SKILL.md` → `/apps/web:deploy`. (Tier 1, Admiralty A1)

Both sources **support** the finding: the colon-namespaced form is the platform's own canonical skill identifier, so a classifier rejecting `:` mis-books a correct routing verdict as an instrument gap. Severity WARNING stands and is *reinforced* — the second source shows the defect also swallows nested project-scope skill names (`apps/web:deploy`), a failure class the finding did not enumerate and which will recur outside the `superpowers:` corpus.
**[DIM-1-04] [SEVERITY: WARNING]** *(the strongest evidence in this run)*
File: `evals/loading.jsonl:21` and `:30` (byte-identical prompts) x `loading_matrix.json` rows 21/30 x `docs/harness/2026-08-05-run4/loading_matrix.json` rows 21/30
Finding: **the D1 instrument is not reproducible at n=1, measured four ways on a byte-identical description.** Because `neg-08` and `neg-15` carry byte-identical prompts, each run measures that one prompt twice — an accidental test-retest control. Results for that single prompt:

| | run #4 row 21 | run #4 row 30 | run #5 row 21 | run #5 row 30 |
|---|---|---|---|---|
| sonnet | `none` | `none` | **`deep-research`** | `none` |
| haiku | `superpowers:dpa` | `superpowers:dpa` | `superpowers:dpa` | **`research`** |

Sonnet: 1 leak in 4 measurements of the same prompt, including a **within-run** flip (row 21 vs row 30, same session, same model, same bytes). Haiku: 3 identical, 1 divergent. Across runs on the same byte-identical `SKILL.md`, sonnet's single defect **migrated class** — run #4 = 1 positive miss (`pos-06` -> `none`), 0 leaks; run #5 = 0 positive misses, 1 negative leak. The rubric **tier** is stable at 8 in both runs; the specific defect is not.
Impact: a single clean matrix is not evidence of clean routing, and a single leak is not evidence of a description defect. Any D1 finding at n=1 — including DIM-1-02 — is a coin-flip observation. This is the target's own recorded position (`gotchas-log.md:22`: *"single-run routing measurements lie; cf. the open n>=3 harness debt"*), now independently confirmed with a within-run control the author did not design for.
Recommendation: raise the D1 coverage-gap language in `critic-rubric.md:18` to state that a **single** matrix run establishes the tier but never a specific cell's verdict, and that findings on individual cells require n>=3. Operationally: add a `--repeat N` flag to `run_evals.py` and default the loading suite to N=3 on the release-blocker negatives.

**Grounded: primary evidence — no external citation applicable.**
`evals/loading.jsonl:21` and `:30` (byte-identical prompts) × four measured cells across two committed matrices (`docs/harness/2026-08-05-run4/loading_matrix.json` rows 21/30; `loading_matrix.json` rows 21/30). The test-retest table is a direct read of archived artefacts, including a within-run flip. Reproducibility here is **measured**, not asserted from a published standard — the strongest form of evidence available, and one no external URL could improve.
**[DIM-1-05] [SEVERITY: ADVISORY]**
File: `evals/loading.jsonl` (all 30 rows); absence verified by full-tree `find` for `hero-quer*` -> zero hits
Finding: **the D1 oracle is self-referential.** `hero-queries.md` does not exist, so every fixture prompt was author-authored *from* the description being graded. Harness-guide §9 names this failure mode (*Description-self-grading*) and prescribes exactly the mitigation unavailable here. The positive sweep is the weakest half: 45/45 positives across three models partly measures whether prompts written to contain the description's own trigger tokens fire on those tokens. The **negative** half is stronger — negatives were written against *sibling* territory, so leaks there are informative independent of authorship.
Recorded per the explicit human decision at Gate 2 (`strategy.md` coverage gap #3): grade D1 from the matrix, label the self-reference. Both done. The score is not inflated on the strength of the positives.
Impact: caps the evidentiary value of a clean positive sweep; does not affect the leak/NO_VERDICT findings above.
Recommendation: capture 10-15 real `/deep-research` invocations from session transcripts into `hero-queries.md`, then re-derive the positive fixtures from them. Until then, D1 above 8.0 is not reachable on this skill regardless of matrix cleanliness.

Coverage gaps (D1):
- **n=1 per cell.** No cell measured >=3 times except the accidental `neg-08`/`neg-15` pair. DIM-1-04 quantifies the cost.
- **The change under review is unreachable from D1.** No commit touched the description; D1 validates nothing about Rule 7c or the tier path.
- **Router proxy is not the real router.** All 90 cells come from the `claude -p` "pick the most specific skill" proxy, whose over-fire bias is a known unfixable-by-description artefact (`critic-rubric.md:20`). No measurement against the production router was made.
- **The `superpowers:` corpus is only partly characterised.** `superpowers:dispatching-parallel-agents` was observed as a competing owner but no fixture asserts it; the description names no such boundary.
- Not tested: any prompt outside the 30 fixtures; multi-turn routing; routing under a loaded competing skill.

**Dimension 1 complete. Setting aside findings for dimension 2.**

---

### Dimension 2 — Tax-test compliance (weight 1.5x)

**Score: 7.0 / 10** — **UNMOVED surface.** Rubric inputs are `SKILL.md` body + `references/` listing. The body is byte-identical to `11a0439`; the three commits edited `references/methodology.md`, `references/github-research.md` and `references/solution-space.md` **content**, which D2 reads only as a *listing*, never as graded prose. The +33 lines of new doctrine are invisible to this dimension. I graded the unmoved body independently and reproduced run #4's defects; I did not inherit its score.

Body = 205 lines / 7,199 tok across 16 offloaded `references/` files with a per-phase "Read at" table (`SKILL.md:193-210`). Offloading discipline is genuinely strong and is why this is not tier 6: examples (`:187`), flag semantics (`:42`), edge-case reasoning (`:169`), and the whole solution-space taxonomy (`:79`) are pointers, not prose.

Findings:

**[DIM-2-01] [SEVERITY: WARNING]**
File: `SKILL.md:17-26` (the `## Trigger` section)
Finding: about 10 lines / ~150 tok of routing text that, by the skill's **own declaration** at `:19` (*"Canonical routing surface = the frontmatter `description`; the list below is a body-side convenience, not a second router"*), cannot perform routing. The body loads only *after* the routing decision, so the positive trigger list at `:21-24` fails the Tax Test on its face: no agent reading it can act differently from an agent that never read it. It duplicates the description's trigger list and adds two phrases the description does not carry (`"benchmark X against Y with citations"`), creating a second, non-authoritative trigger surface the author had to disclaim in prose.
Impact: about 150 tok of the 7,199 load tier does no work — material given the 4% headroom to the hard cap (DIM-3-02). The disclaimer at `:19` is itself token cost incurred to neutralise the section below it.
Recommendation: delete `SKILL.md:21-24` (the positive trigger list) and `:19` (the disclaimer that exists only to defuse it). Retitle the section `## Post-load deferral` and keep **only** `:26`, whose four named tool owners (`tavily_search`/`tavily_extract`/`tavily_skill`/`tavily_map`) *do* change post-load behaviour by telling a wrongly-loaded agent where to send the request. Net about -120 tok.

**Grounded: primary evidence (mechanical half).**
`SKILL.md:19` — the author's own disclaimer that the list below "is a body-side convenience, not a second router" — and `:21-24`, the duplicated positive trigger list it disclaims. The duplication, the two extra non-authoritative phrases, and the disclaimer's token cost are all proven by the file.

**Citations (norm half — (a) the body loads only *after* the routing decision, so body-side triggers cannot route; (b) the Tax Test itself). Retrieved 2026-08-14:**
- *Agent Skills overview — Claude Platform Docs.* https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview — progressive-disclosure table: "Level 1: Metadata | Always (at startup) | ~100 tokens per Skill | `name` and `description` from YAML frontmatter"; "Level 2: Instructions | **When Skill is triggered** | Under 5k tokens | SKILL.md body". (Tier 1, Admiralty A1)
- *Optimizing skill descriptions — agentskills.io.* https://agentskills.io/skill-creation/optimizing-descriptions — "At startup, they load only the `name` and `description` of each available skill — just enough to decide when a skill might be relevant. When a user's task matches a description, the agent reads the full `SKILL.md` into context... **This means the description carries the entire burden of triggering.**" (Tier 1, Admiralty A1)
- *Best practices for skill creators — agentskills.io.* https://agentskills.io/skill-creation/best-practices — the Tax Test in official guidance: "Ask yourself about each piece of content: 'Would the agent get this wrong without this instruction?' If the answer is no, cut it." (Tier 1, Admiralty A1)
- *Designing, Refining, and Maintaining Agent Skills at Perplexity.* https://research.perplexity.ai/articles/designing-refining-and-maintaining-agent-skills-at-perplexity — the rubric's own source for the Tax Test (`critic-rubric.md` footnote [^10]): "Would the agent get this wrong without this instruction? If the sentence does not need to be there, it cannot afford to be there because everyone is paying this cost every single time." (Tier 1, Admiralty A2 — practitioner-primary for this specific test)

All four **support** the finding. The second citation is decisive: the description carries the *entire* burden of triggering, so a body-side trigger list is structurally incapable of routing, exactly as `SKILL.md:19` concedes. Severity WARNING stands.

**Instrument note (does not alter this finding).** `critic-rubric.md` footnote [^10] cites `research.perplexity.ai/articles/designing-refining-and-maintaining-agent-skills`, which returns **404** (verified 2026-08-14). The live article sits at the same path with an `-at-perplexity` suffix (URL above). The rubric's authority link for its D2 dimension is dead and should be corrected.
**[DIM-2-02] [SEVERITY: ADVISORY]**
File: `SKILL.md:116`, `:136`, `:138`, `:143`, `:161` (plus the description at `:3`)
Finding: the five-artifact contract is restated **five times** in the body. `:143-151` is the canonical Output Format table. Of the rest, two are load-bearing and two are not: `:116` (*"No artifact file is written in this phase"*) and `:136` (the operative atomic-write instruction) each carry a distinct constraint and earn their tokens; `:138` (*"This engine still emits exactly five artifacts"*) and `:161` (*"Emit only the five artifacts"*) restate the count without adding a constraint the table does not already fix.
Self-challenge: a senior author defends `:161` as belonging to the Scope-Constraints block for locality — a reader consulting only that section gets the whole rule. That is a real design argument, hence ADVISORY.
Impact: about 30 tok of redundancy, and five surfaces to keep in sync — the drift risk the CHANGELOG already records having paid once when the contract went four to five (six surfaces realigned).
Recommendation: at `SKILL.md:161`, replace the enumeration with a pointer: `Emit only the artifacts in §Output Format.` Leave `:116` and `:136` intact.

**[DIM-2-03] [SEVERITY: ADVISORY]**
File: `SKILL.md:53`, `:72`, `:81` (three hardcoded `~/.claude/` paths); flagged independently by `lint_skill.py` check#18
Finding: the body hardcodes `~/.claude/deep-research/newsletter-corpus/` (`:53`, `:72`) and `~/.claude/deep-research/stack-paths.json` (`:81`) with no `compatibility:` frontmatter declaration. These are Claude-Code-specific host paths inside a portable skill surface, and the maintainer contract (`.claude/CLAUDE.md` §Style conventions) explicitly permits absolute paths in tool routing — a declared choice, not an accident.
Impact: on a non-Claude-Code host the two conditional sources degrade, which the skill handles correctly at `:81` and `:164` (`degraded`, never silent). The cost is a missing declaration, not broken behaviour.
Recommendation: add `compatibility: Targets Claude Code (uses ~/.claude/ host paths for the newsletter corpus and stack inventory).` to the frontmatter. Clears lint check#18 without touching the body.

Coverage gaps (D2):
- **The dimension cannot see the change under review.** +33 lines of new doctrine landed in `references/methodology.md` §6, `references/github-research.md` §2b and `references/solution-space.md`; D2's declared input treats `references/` as a listing only, so none of that prose was tax-tested. If the new doctrine is bloated or re-teaches known material, **no dimension in this rubric would detect it.**
- Tax Test is LLM-judged (rubric: *"hardest to grade mechanically"*); a second Critic may split by one tier.
- Not examined: whether each of the 16 `references/` files is itself tax-compliant; whether the "Read at" phases are honoured at runtime (that is `progressive.jsonl`, which no runner can execute — see D4).

**Dimension 2 complete. Setting aside findings for dimension 3.**

---

### Dimension 3 — Token-budget hygiene (weight 1.5x)

**Score: 7.5 / 10** — **UNMOVED surface.** Both scored tiers are byte-identical to `11a0439` (index derives from the unchanged name+description; load from the unchanged body). The change under review grew only the **files tier**, for which the rubric defines **no threshold**. D3 validates nothing about the three commits.

- Description **725 / 1024 chars** — within the only public hard cap, 299 chars of margin. No auto-CRITICAL.
- Index tier **171 tok** — above the 100 target, well under the 320 hard cap: squarely in tier 8's stated band (*"Index tier 100-320"*).
- Load tier **7,199 tok** — above the 5,000 target, under the 7,500 hard cap.

Findings:

**[DIM-3-01] [SEVERITY: ADVISORY]** *(rubric gap, disclosed rather than silently resolved)*
File: `critic-rubric.md:58-63` vs `/tmp/skill-harness-1786648836/budget.txt`
Finding: the load tier at **7,199** falls in a band the rubric does not score. Tier 8 covers *"load tier 5,000-6,250"*; tier 4 requires *"load tier exceeds the 7,500 hard cap"*. 7,199 is in the 6,250-7,500 gap. The only clause reaching it is tier 6 — *"A token tier between target and hard cap **WITHOUT** a documented justification in CHANGELOG.md"* — and its precondition is **not met**: `CHANGELOG.md` documents the D3 remediation that produced this number (body 10,036 -> 7,199, with three new reference files created to absorb the difference). So the artifact is better than tier 6 and outside tier 8's band.
Impact: the dimension cannot be scored by literal tier lookup. I resolved it at 7.5 — tier-8 behaviour on the index tier and a *justified* overage on the load tier, docked half a point for DIM-3-02 — and disclose the interpolation rather than presenting it as a tier match.
Recommendation: in `critic-rubric.md`, close the band: make tier 8 read *"load tier 5,000-7,500 **with** a CHANGELOG justification"* and tier 6 *"...between target and hard cap **without** one"*, so the justified/unjustified axis rather than an arithmetic gap decides the tier.

**[DIM-3-02] [SEVERITY: WARNING]**
File: `.github/workflows/validate.yml` (absence of a budget step) vs `budget.txt` load tier 7,199
Finding: the load tier sits **4.0% below** the 7,500 hard cap (301 tok of headroom) and **nothing in CI guards it**. The repo runs five check scripts on push/PR (`.claude/CLAUDE.md` §Extension protocol) and `token_budget.py` is not among them. History shows the risk is realised, not hypothetical: the same body was **+33.8% over** the cap one edit ago (10,036 tok), brought back only by a harness finding. Any future addition of ~300 tokens — roughly one workflow step or one new edge case — silently converts a WARNING into an auto-CRITICAL spec breach.
Impact: the hard cap is enforced by review attention rather than by a gate. Given the skill's own doctrine that *"a threshold is not a gate if nothing computes it"* (`gotchas-log.md:102`), this is a self-inconsistency in the repo's strongest discipline.
Recommendation: add to `.github/workflows/validate.yml` a step running `token_budget.py . --json` piped to a `jq` assertion that the load tier is < 7,500 and the description < 1,024 chars, exiting non-zero otherwise. Same "make the threshold computable" move the repo already made for the solution-space gates.

**Grounded: primary evidence (mechanical half).**
`.github/workflows/validate.yml` — absence of any budget step among the five checks run on push/PR — against `/tmp/skill-harness-1786648836/budget.txt` load tier 7,199, plus the CHANGELOG's record of the 10,036-token predecessor. That no CI step computes the threshold is proven by the workflow file.

**Citations (norm half — the published caps). Retrieved 2026-08-14:**
- *Specification — agentskills.io.* https://agentskills.io/specification — the only published frontmatter hard limits are `name` ≤ 64 characters and `description` ≤ 1024 characters ("Must be 1-1024 characters"). Body size is guidance, not a limit: "Keep your main `SKILL.md` under 500 lines", and under Progressive disclosure, "Instructions (**< 5000 tokens recommended**): The full `SKILL.md` body is loaded when the skill is activated". (Tier 1, Admiralty A1)
- *Agent Skills overview — Claude Platform Docs.* https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview — "Level 2: Instructions | When Skill is triggered | **Under 5k tokens** | SKILL.md body". Confirms 5k as the published figure for the body tier. (Tier 1, Admiralty A1)

The **1,024-character description cap is confirmed spec-exact**, which validates the 725/1024 arithmetic used here and the "299 chars of margin" reused in DIM-6-01. Cited once, here.

**Contested — scoped to ONE WORD of the wording, NOT to the finding or its threshold.**
**To be explicit about what is *not* contested:** the Critic did not invent the 7,500 threshold. It grades against `critic-rubric.md:53`, which sets that number, and DIM-3-01 above already discloses the rubric's band gap in the Critic's own voice. The threshold is properly sourced *to the rubric*. What is unsupported is the single word **"spec"** in the phrase "auto-CRITICAL **spec** breach":
1. **The 7,500 figure is local, not published.** agentskills.io/specification and platform.claude.com both give **5,000 tokens as a *recommendation*** for the body tier, and 500 lines as a style guideline. Neither is a gate, and neither is 7,500. So a load tier over 7,500 breaches a **local** rubric threshold, not a published specification.
2. **The harness disclaims the word in its own voice.** `critic-rubric.md:51`: "Description >1024 **characters** — the ONLY public hard cap (agentskills.io; auto-CRITICAL). **The token tiers below are hygiene targets, not spec gates.**" But `critic-rubric.md:53` labels the load tier ">7,500 tokens (hard cap; **auto-CRITICAL**)". So "auto-CRITICAL" *is* rubric-backed at `:53` and stands; "spec" is contradicted by `:51`.
3. **What needs adjudication** is the one-word wording and the `:51`-vs-`:53` internal contradiction — a documentation defect in the harness's own rubric, not a fabrication by the Critic and not a defect in the target skill.

**The finding's substance stands at WARNING regardless of how that is adjudicated, and this block is not grounds to downgrade it.** Whether 7,500 is a spec gate or a purely local hygiene threshold, the defect is identical and untouched: the repo declares a threshold that nothing in CI computes, contradicting its own doctrine at `gotchas-log.md:102` ("a threshold is not a gate if nothing computes it"). Note further that the *external* norm is **stricter** than the local one, not looser — the spec's recommended body figure is 5,000 tokens, which the measured 7,199 already exceeds by 44%. Correcting the wording therefore removes no urgency from the recommendation.
**[DIM-3-03] [SEVERITY: ADVISORY]**
File: `/tmp/skill-harness-1786648836/budget.txt` (FILES TIER block; 5 of the top-10 entries are `.pyc` — ranks 1, 4, 5, 6, 9) vs `.gitignore:25`
Finding: the reported files tier of 106,524 tok includes **~16,930 tok of gitignored bytecode** — `scripts/__pycache__/verify_gates.cpython-38.pyc` (16,464 tok) is reported as the single largest file in the skill, ahead of `scripts/verify_gates.py` itself. Verified gitignored via `git check-ignore -v` -> `.gitignore:25`. These never ship; they were written by a `py_compile` step during this session. Clean files tier is about 70k tok.
Impact: **no score impact** — the rubric sets no files-tier threshold. But the printed number over-reports the shipped surface by about 52% and would mislead any future reader treating it as a trend line.
Recommendation: in `token_budget.py`, exclude `__pycache__/`, `*.pyc` and `.git/` from the files-tier walk (or honour `.gitignore`), so the number reflects the shipped artefact.

Coverage gaps (D3):
- **No budget measurement of the change under review.** `references/methodology.md` grew to 8,156 tok and `verify_gates.py` to 9,051 tok; both files-tier, unscored. A reference file large enough to blow the context when read at Phase 0 would pass D3 silently.
- Token counts are `token_budget.py`'s estimator, not a tokenizer round-trip; treat +/-5% as noise (the 4% headroom in DIM-3-02 is inside that band, which strengthens rather than weakens the finding).
- Not examined: peak context when several `references/` files are read in the same phase — the realistic load, unmeasured by any tier.

**Dimension 3 complete. Setting aside findings for dimension 4.**

---

### Dimension 4 — Eval coverage (weight 1.5x)

**Score: 8.0 / 10** — **UNMOVED surface, and this is the crisp case.** The change under review **did add a fixture pair with a positive control** — `tests/fixtures/solution-space/agentic-no-skill-query.json` (violation) and `agentic-with-skill-query.json` (control). D4's declared input is `evals/` + `rubric.md`. `git diff --name-only main..HEAD | grep -c "^evals/"` returns **0**. D4 grades an unmoved surface *while good eval work happened three directories away*, invisibly.

Inventory (all populated, **zero placeholders** — `grep` for `<POSITIVE_PROMPT`/`<REPLACE`/`TODO` across `evals/` returns nothing):

| File | Count | Rubric floor | Status |
|---|---|---|---|
| `loading.jsonl` | 30 rows (15 load / 15 skip) | ~10+10 balanced | clears — but 29 **distinct** prompts (DIM-4-01) |
| `progressive.jsonl` | 13 rows | >=5 recommended | clears |
| `e2e.jsonl` | 15 rows, all with `mechanical_checks` | >=3 | clears |
| `rubric.md` | 47 lines | "detailed" | clears — pass bars, 5-failure-mode mapping, supersession protocol |

Territorial negatives are present **and name their owner** in `boundary`: `neg-07` (`/research`), `neg-08`/`neg-15` (plugin sibling), `neg-10` (`linkedin-post`), `neg-12` (`deck-generator`), `neg-14` (over-fire guard on the AI-355 surface). This satisfies the rubric's territorial-subcategory requirement outright.

Findings:

**[DIM-4-01] [SEVERITY: WARNING]** *(REPEAT of run #4 remediation row 1 — unremediated)*
File: `evals/loading.jsonl:21` (`neg-08`) and `:30` (`neg-15`)
Finding: the two rows carry **byte-identical prompts** — `"fan out a bunch of research agents on this topic and just give me the gist, no plan needed"` — verified by frequency count (30 rows, **29 unique prompts**). The supersession convention at `evals/rubric.md:47` is correctly applied (it changes `boundary`, never the prompt, to avoid eval laundering), but the arithmetic consequence is that the pass bar at `evals/rubric.md:15` (*">=14/15 negatives"*) **counts one probe twice**, and the two rows can never diverge in content. Effective distinct negative coverage is **14**, not 15. Run #4 reported this at its remediation row 1 with two concrete options; neither was applied, and the rows are still byte-identical at `53c4444`.
Impact: the negative bar overstates coverage by one probe. Combined with DIM-1-03, haiku's raw numerator is doubly unreachable. An unremediated known finding across two runs is more severe than a fresh one.
Recommendation: apply run #4's second option — give `neg-15` a distinct phrasing of the *same* boundary (e.g. `"spin up a few agents to research this and just summarise, skip the plan"`). This adds a genuine probe, keeps `neg-08` unedited (satisfying `rubric.md:47`), and restores the 15-probe arithmetic. Do **not** merely amend the bar text: that preserves the coverage loss while hiding it.

**Grounded: primary evidence — no external citation applicable.**
`evals/loading.jsonl:21` and `:30`, byte-identical prompt strings confirmed by frequency count (30 rows, 29 unique prompts), against run #4's unremediated report of the same defect at `53c4444`. The supersession convention it is weighed against is the target's own `evals/rubric.md:47`, and the pass bar its own `evals/rubric.md:15` — both local files. A duplicate-string count needs no outside authority.
**[DIM-4-02] [SEVERITY: WARNING]**
File: `evals/progressive.jsonl` (keys `when`/`expect_read`/`expect_not_read`) and `evals/e2e.jsonl` (keys `invocation`/`mechanical_checks`) vs `~/.claude/skills/skill-generator/scripts/run_evals.py` (reads `entry["prompt"]`)
Finding: **two of the three eval suites cannot be executed by the runner.** Verified by key inspection: `progressive.jsonl` rows carry no `prompt` key (union = `expect_not_read`, `expect_read`, `id`, `note`, `when`); `e2e.jsonl` rows carry `invocation` instead. `run_evals.py` keys on `prompt`, so both suites skip every row and report `[]` with zero failures — **structurally indistinguishable from a perfect score**. `strategy.md` records this as the reason only `loading` was run, and the target's CHANGELOG lists it under *Known limitations*. Additionally `evals/sycophancy-probes.jsonl` (5 rows) and `evals/benchmark-testset.jsonl` (5 rows) are executed by nothing at all — `--suite` accepts only `loading|progressive|e2e`.
Impact: 28 of 33 declared non-loading fixtures (13 progressive + 15 e2e) are **declarative coverage only**. The rubric credits their presence; nothing verifies their content. This is the failure mode the harness exists to catch, one layer up: a green that means "not measured".
Recommendation: in `run_evals.py`, key the suite reader per suite — `prompt` for loading, `when` for progressive, `invocation` for e2e — and make an empty result set for a **non-empty** fixture file exit non-zero with `no fixtures matched: schema mismatch`, so a silent skip can never again read as a pass. Until that ships, `strategy.md`'s refusal to run them is the correct call and should stay.

**Grounded: primary evidence — no external citation applicable.**
Key-union inspection of `evals/progressive.jsonl` (union = `expect_not_read`/`expect_read`/`id`/`note`/`when`; no `prompt` key), `evals/e2e.jsonl` (carries `invocation`), and `run_evals.py` (keys on `entry["prompt"]`), plus `--suite` accepting only `loading|progressive|e2e` while `sycophancy-probes.jsonl` and `benchmark-testset.jsonl` exist. A schema mismatch between two files the run read; no published norm is asserted, and the "silent skip reads as a pass" impact follows arithmetically from the mismatch.
**[DIM-4-03] [SEVERITY: ADVISORY]**
File: `evals/rubric.md:15` and `:29`
Finding: both pass bars are written as **raw counts** pinned to the current fixture population (*">= 14/15 positives AND >= 14/15 negatives"*, *"13/13"*), with an appended convention that *"appended fixtures raise the bar with them"*. A raw numerator is unsatisfiable whenever a cell returns no usable verdict, regardless of routing quality — realised on haiku in both runs (2 cells in run #4, 1 in run #5).
Impact: the bar conflates routing quality with instrument completeness; a model can route perfectly and still fail the stated bar.
Recommendation: restate as a ratio over *measured* verdicts with an explicit completeness floor: *">=93% of measured verdicts correct per side, AND >=90% of cells returning a usable verdict; a cell with no usable verdict is an instrument gap, reported separately and never scored as a miss."*

**[DIM-4-04] [SEVERITY: WARNING]** *(rubric-coverage finding — about this harness, not the skill)*
File: `tests/fixtures/solution-space/agentic-no-skill-query.json`, `tests/fixtures/solution-space/agentic-with-skill-query.json`, `tests/check-solution-space.sh` — none reachable from `critic-rubric.md` D4 Inputs (*"evals/ directory contents (JSONL files); rubric.md presence"*)
Finding: the fixture work in the change under review is **real, disciplined and rubric-invisible**. I executed `bash tests/check-solution-space.sh`: **PASS, exit 0**, with `ok: agentic-no-skill-query -> requires >=1 agent-skill-class query` (the violation fixture trips Rule 7c), `ok: 7c control exits 0` / `ok: 7c control has 0 violations` (the positive control clears it), and 7c purity guards asserting the rule fires on **no** other fixture. The CHANGELOG's *"Red-ability verified by ablation"* claim is corroborated by executed test, and the control deliberately carries all four §2b query shapes rather than the one that would merely clear the gate — precisely the gate-conformant-but-not-doctrine-conformant gap run #4's DIM-4-02 identified. This is the strongest eval work in the diff, and **no dimension in this rubric can see it**.
Impact: the harness scores eval maturity from `evals/` alone, while the skill's most rigorous fixtures (adversarial mutation set, positive control, purity guard, red-ability ablation) live under `tests/`. A skill could regress its `tests/` fixtures to zero and D4 would not move. Conversely this diff improved them and D4 did not move.
Recommendation: extend `critic-rubric.md` D4 Inputs to *"`evals/` JSONL + `rubric.md`, **plus any executable fixture/gate suite the skill ships (`tests/`), run once and its exit status recorded**"*, and add a tier-10 clause requiring at least one **positive control** alongside violation fixtures. Then this skill's `tests/` set would earn the credit it currently gets none for.

**Grounded: primary evidence — no external citation applicable.**
Both halves are locally verified: `critic-rubric.md` D4 Inputs ("evals/ directory contents (JSONL files); rubric.md presence") demonstrably excludes `tests/`, and the run **executed** `bash tests/check-solution-space.sh` — PASS, exit 0, with the named assertions reproduced in this document's Static-check summary. This finding is about *this harness's own rubric scope*, an internal document, so no external standard governs it. Its recommendation proposes a **new** rubric clause (require a positive control alongside violation fixtures) rather than invoking an existing published one, so the recommendation needs no external grounding either — it is a design proposal for the harness, correctly labelled as a rubric-coverage finding rather than a skill defect.
Coverage gaps (D4):
- **Executed:** `loading` only (30 rows x 3 models) plus `tests/check-solution-space.sh`. **Not executed:** `progressive`, `e2e`, `sycophancy-probes`, `benchmark-testset` — read statically. No behavioural claim in this review rests on them.
- **Not executed:** the other `tests/check-*.sh` suites (cross-references, provenance, schema, example-invariants, osint-gates) and `.github/workflows/validate.yml`. I ran only the suite the diff touched.
- Fixture **quality** is ungraded: I verified counts, distinctness, key schemas, territorial labelling and placeholder-freedom, not whether a passing `e2e` fixture would actually detect its stated defect.
- `evals/fixtures/sota-recall/` (the recall corpus, 6 items across 3 cases) is executed by nothing I ran and is outside D4's declared input.

**Dimension 4 complete. Setting aside findings for dimension 5.**

---

### Dimension 5 — Append-mostly hygiene (weight 1.0x)

**Score: 9.0 / 10** — **MOVED.** This is the **only** dimension whose declared input the change under review touched: `CHANGELOG.md` +2 lines (`git diff main..HEAD -- CHANGELOG.md`). Both additions are top-of-section appends under `## [Unreleased]` -> `### Added` — the Rule 7c entry and the software-capability tier entry. No prior entry was rewritten. On the one dimension that *can* see the diff, the diff **complies**.

- `CHANGELOG.md`: 131 lines, Keep a Changelog + semver, explicit append-only header (*"new entries go on top, old entries are never rewritten"*).
- `gotchas-log.md`: 118 lines of **real** entries — not a template header — each carrying the full four-field structure (**Trigger / Gotcha / Resolution / Guard**), verified on the 2026-08-05 W5 entry (`:17-22`) and the Rule-7b parasite entry (`:26-31`).
- Description last changed 2026-08-04 **with** a matching CHANGELOG entry (*"Description edit (2026-08-04)"*, carrying the re-measured matrix). The rubric's tier-4 trigger (description churn without a CHANGELOG entry) does not fire.

The append-only discipline survives a genuinely hard case, which is what earns the 9: when the artifact contract changed four to five, the superseded sentence was **preserved verbatim** and a later entry explicitly supersedes it (*"Per this file's append-only header the older line is not rewritten; it stands as an accurate record of the contract on its date"*), with the same treatment applied to the mirrored `gotchas-log.md` entry. Most skills silently edit here.

Findings:

**[DIM-5-01] [SEVERITY: ADVISORY]** *(REPEAT of run #4 remediation — deferred by design)*
File: `CHANGELOG.md` — `### Added` at both offset 3 and offset 44 within `## [Unreleased]`; `### Changed` at both offset 12 and offset 51 (offsets relative to the `[Unreleased]` block)
Finding: the `[Unreleased]` section carries **duplicate sibling headings** — two `### Added` and two `### Changed` blocks. Strict Keep a Changelog expects one of each per version block. Run #4 raised this and recommended merging *at the next release tag*; no tag has been cut since, so the defect legitimately persists.
Self-challenge: a senior author defends this correctly — merging **within** an unreleased section is not history rewriting (nothing under `[Unreleased]` has been published), so the fix is safe but not yet due. Hence ADVISORY, costing at most half a point.
Impact: cosmetic while unreleased; becomes a real format defect the moment `[Unreleased]` is promoted to a version block.
Recommendation: at the next semver tag, merge the two `### Added` blocks and the two `### Changed` blocks in the same commit that renames `[Unreleased]`. Do not merge earlier — no benefit, and it touches lines readers may be citing.

**[DIM-5-02] [SEVERITY: ADVISORY]**
File: `gotchas-log.md` (no entry for the three commits under review) vs `evals/rubric.md:39-43` (*"Every new feature (flag, retrieval source, gate) adds: ... >=1 negative fixture for its nearest territorial neighbor, >=1 mechanical e2e check proving its DoD"*)
Finding: Rule 7c is a **new gate**, and the repo's own fixture contract at `rubric.md:39-43` obliges every new gate to add fixtures in `evals/`. The diff added excellent fixtures under `tests/` (DIM-4-04) and a thorough CHANGELOG entry, but appended **no** `gotchas-log.md` entry and **no** `evals/` fixture. The three prior gate landings (Rule 7b, OSS sweep, solution-space) each produced a `gotchas-log.md` entry.
Self-challenge: Rule 7c is a feature, not a trap discovered in production, so `gotchas-log.md` is arguably the wrong home — that log's stated purpose is maintainer traps. The CHANGELOG entry is thorough (it records the measurement, the ten swept topic combinations, the 4,411-star miss, and the ablation). Hence ADVISORY.
Impact: the `rubric.md:39-43` obligation is unmet for clause 3 (*">=1 mechanical e2e check proving its DoD"*) — the DoD is proven by `tests/check-solution-space.sh`, which is CI-only and, per `.claude/CLAUDE.md` §I4a, *"never invoked by the skill at runtime"*. No `e2e.jsonl` fixture asserts Rule 7c, unlike `e2e-15` for Rule 7b.
Recommendation: append an `e2e.jsonl` fixture (`e2e-16`) whose first `mechanical_checks` string asserts that an agentic-question run's manifest carries >=1 skill-class query in `categories[key=open-source].queries`, mirroring `e2e-15`'s Rule 7b check. This closes the `rubric.md:39-43` clause and gives Rule 7c a fixture in the suite the *rubric* reads.

Coverage gaps (D5):
- Full git history was read for the three commits under review only (`main..HEAD`) plus `git log -10`. No audit of whether older CHANGELOG entries were ever rewritten before `1f10507` — append-only is verified for the diff, asserted for history.
- `gotchas-log.md` entries read at `:1-36` (2 of about 8 entries in full). Field completeness verified on those; the remainder sampled via grep, which shows the four field labels present throughout.
- The rubric's *"Description changed in the last 7 days without a CHANGELOG entry"* clause was evaluated from the CHANGELOG's own dating (2026-08-04) rather than from `git log` on the frontmatter line; the byte-identity of `SKILL.md` vs `11a0439` independently confirms no change in this diff.

**Dimension 5 complete. Setting aside findings for dimension 6.**

---

### Dimension 6 — Cross-skill territorial conflicts (weight 1.0x)

**Score: 9.5 / 10** — **UNMOVED surface.** `conflict_check.py` consumes the frontmatter description, byte-identical to `11a0439`; the Jaccard result is necessarily identical to run #4's and validates nothing about the diff.

- **Max Jaccard = 0.019** across 31 peers — an order of magnitude under the tier-10 threshold (<0.1) and 20x under the auto-CRITICAL line (>=0.4). Nearest peers are semantically unrelated (`doc-render` 0.019, `skill-generator` 0.019, `prototype` 0.015).
- **Explicit negative boundaries to nearest peers** are present at the routing surface: `SKILL.md:3` names `/research` **and** the plugin-namespaced `deep-research` sibling; `SKILL.md:26` names four tool owners.

Both tier-10 clauses are literally satisfied. The measurement is **credible rather than lucky**: per `strategy.md`, the corpus was deliberately hardened to a merged 32-skill farm spanning user-scope *and* project-scope, specifically because the default `~/.claude/skills` corpus omits project-scope siblings and *"the measurement comes out too lenient."* A harder corpus returning 0.019 is stronger evidence than a default corpus returning the same number.

Findings:

**[DIM-6-01] [SEVERITY: WARNING]**
File: `SKILL.md:3` (the boundary clause naming *"the plugin-namespaced deep-research sibling"*) vs `loading_matrix.json` row 21 `responses.haiku` = `superpowers:dispatching-parallel-agents`
Finding: the description's sharpest declared boundary points at a peer that **does not exist on this machine** (run #4 verified independently: `grep -rl "^name: deep-research" ~/.claude/plugins/` returns nothing across 133 `SKILL.md` files), while the peer that **actually competes** for the release-blocker prompt is unnamed. Across the two runs, `superpowers:dispatching-parallel-agents` was returned **3 times** as the router's choice on `neg-08`/`neg-15` — and it is a real, installed skill. The description spends its most specific territorial token on a phantom and stays silent on the measured competitor.
Impact: for `neg-08`-class prompts the boundary degrades from *"defer to X"* into a bare *"don't fire"*, which is weaker guidance — and the one observed leak in 90 cells (DIM-1-02) is on exactly that prompt. Jaccard cannot detect this: it measures token overlap with peers that exist, and is blind to a *missing* boundary.
Recommendation: in `SKILL.md:3`, extend the `Do NOT load for` clause with the measured competitor — e.g. `...or parallel-agent fan-out for a quick gist (use superpowers:dispatching-parallel-agents)`. The description has **299 chars of margin** to the 1,024 cap, so this costs nothing in D3. Re-measure `neg-08`/`neg-15` at n>=3 afterwards (the same experiment DIM-1-02 asks for; one run answers both).

**Grounded: primary evidence — no external citation applicable.**
`SKILL.md:3` (the boundary clause naming "the plugin-namespaced deep-research sibling"); run #4's executed `grep -rl "^name: deep-research" ~/.claude/plugins/` returning nothing across 133 `SKILL.md` files — an absence proven by a search over the installed corpus, not inferred; and three occurrences of `superpowers:dispatching-parallel-agents` as the router's verdict on `neg-08`/`neg-15` across two runs' matrices.

The "**299 chars of margin**" arithmetic depends on the 1,024-character description cap, which is **spec-confirmed** — see the Citations block under DIM-3-02 (agentskills.io/specification, retrieved 2026-08-14). Deliberately not re-cited here: repeating the URL across findings dilutes rather than strengthens it.

**Cross-reference strengthening this finding:** DIM-1-03's citations independently establish that `superpowers:dispatching-parallel-agents` is a real, well-formed platform skill identifier. That confirms this finding's asymmetry is genuine — the description names a boundary peer that does not exist while the peer that measurably competes does exist and is unnamed.
**[DIM-6-02] [SEVERITY: ADVISORY]**
File: `/tmp/skill-harness-1786648836/conflict.txt` (corpus line: 31 peers) vs `loading_matrix.json` verdicts naming `research`, `scrape`, `diagnosing-bugs`, `linkedin-post`, `superpowers:dispatching-parallel-agents`
Finding: the Jaccard corpus and the routing corpus are **not the same population**. `conflict_check` compared 31 skill descriptions, but the router returned verdicts naming `research` and `scrape` — which on this machine are **slash commands**, not skills with descriptions — and `superpowers:dispatching-parallel-agents`, a plugin skill. A Jaccard of 0.019 certifies low overlap with the *skill* corpus while the real routing contest includes non-skill surfaces the instrument never compared against.
Impact: D6's number is sound for what it measures and silent on command-vs-skill territory. It cannot be inferred that no territorial conflict exists — only that none exists among the 31 compared descriptions.
Recommendation: extend `conflict_check.py`'s corpus builder to include user-scope and plugin command frontmatter (`~/.claude/commands/*.md`, plugin `commands/`) alongside skills, so the Jaccard population matches the router's actual candidate set.

Coverage gaps (D6):
- **The diff is unreachable.** Description unchanged so Jaccard unchanged. D6 says nothing about Rule 7c or the tier path.
- Jaccard is bag-of-words on descriptions; it cannot detect the *semantic* over-fire the rubric's own nearest-neighbour clause describes, nor a missing boundary (DIM-6-01).
- The 31-peer corpus excludes slash commands, plugin commands, and the `suggest-tooling` sibling inside `SKILL_PATH` (correctly scoped out as a separate skill per the spec).
- No trigger-phrase intersection test was run mechanically against peers; I checked the description's phrases against the four named owners by reading, not by tooling.

**Dimension 6 complete. Setting aside findings for dimension 7.**

---

### Dimension 7 — Description economy (weight 1.0x)

**Score: 7.5 / 10** — **UNMOVED surface.** The description is byte-identical to `11a0439`; the diff cannot have moved D7.

**Invocation-mode gate:** neither `disable-model-invocation` nor `user-invocable` appears in the frontmatter (the three keys are `name`, `description`, `allowed-tools`). The skill is model-invoked by default, the description loads every session, and D7 **applies** — no N/A default.

**Routing-clean precondition:** met. Per rubric D7, economy only bites when routing already passes; the D1 matrix is clean but for one SUSPECT leak, so grading economy is legitimate.

Three judge prompts, applied to `SKILL.md:3`:

1. **Filler opener — 0 slips.** Opens *"Agentic multi-source deep research via Tavily MCP..."* — position-1 is a domain concept. No `"A skill that..."` / `"This skill..."` frame.
2. **One-trigger — 1 slip.** `"deep research on X"` and `"recherche approfondie sur X"` name the **same branch** in two languages. The rubric's named example of a duplication pair.
3. **No-op — 1 candidate, contested.** See DIM-7-02.

Rubric tier 8 (*"Exactly one slip, otherwise clean"*) is the literal fit for one confirmed slip and a clean filler test. I score **7.5**, docking half a point for the contested no-op candidate rather than promoting it to a second confirmed slip on judgment alone.

Findings:

**[DIM-7-01] [SEVERITY: ADVISORY]** *(downgraded from run #4's WARNING on new measured evidence — with the defense's weak point stated)*
File: `SKILL.md:3` (`"deep research on X"` / `"recherche approfondie sur X"`); author's defense at `gotchas-log.md:17-22`
Finding: the FR/EN pair is **one branch written twice** — a duplication slip by the rubric's own definition, costing about 30 index tokens paid every session. The author **measured it rather than asserting a defense**: the W5 ablation (variant description without the FR form, full loading suite, 3 models, 90 cells, cache-cold) found `pos-03/09/15` **held 9/9**, i.e. the semantic router resolves FR phrasing without the FR trigger. By the D7 no-op test, that is a measured positive: the phrase's deletion changed no positive routing verdict.
The FR form was nonetheless **kept**, on the grounds that the ablation variant flipped 3 negative cells to leaks — including `neg-08`/`neg-15` on sonnet (`none` -> `deep-research`) — and *"a variant that measures below the target's own negative bar cannot be read as holds."* DIM-7-01 is logged closed as *"a measured non-edit, not as a validated slip"*, with a named re-open condition (n>=3-per-arm ablation).
**New evidence from this run bearing on that defense:** run #5 baseline — FR form **present**, description byte-identical — reproduces **exactly** the `neg-08`/sonnet leak the ablation attributed to FR removal (DIM-1-02, DIM-1-04). The specific cell the retention decision rests on therefore leaks *with* the FR form too, placing it inside baseline variance and materially weakening the ablation's causal attribution. The author's own entry anticipated this (*"At n=1 per cell this does not separate causation from router variance"*).
Self-challenge #2 (*could a senior author defend this as deliberate?*): **yes, in writing, with a matrix** — hence ADVISORY, not WARNING, and I do not re-litigate the edit. But the slip is not retired: it is a measured duplication whose retention rests on evidence this run shows to be noisier than it looked.
Impact: about 30 tok/session of confirmed duplication, held on deliberately-recorded and now-weakened grounds. No routing impact measured in either direction.
Recommendation: do **not** edit the description. Execute the author's own re-open condition — the n>=3-per-arm ablation, restricted to the three release-blocker negatives plus the three FR positives (36 cells per arm). My run supplies a third baseline measurement of `neg-08`; two more per arm settle it. If baseline and variant leak at comparable rates, the negative-leak defense dissolves and the slip becomes editable on data.

**[DIM-7-02] [SEVERITY: UNKNOWN]** *(evidence deliberately named as missing)*
File: `SKILL.md:3`, trailing clause *"it runs autonomously and only pauses to ask a clarifying question when the query is genuinely ambiguous"*
Finding: about 28 tokens of **behavioural** disclosure inside the `Do NOT load for` parenthetical. It is the strongest candidate for a second no-op: no fixture in `loading.jsonl` probes autonomy-vs-approval-halt, and no named boundary is an approval-halting sibling, so I have **no evidence** that deleting it changes any routing verdict. Equally, I have no evidence that it does not — the W5 ablation varied only the FR form, so this clause has never been ablated.
Per harness-guide §7, a finding without file:line proof of *impact* takes severity UNKNOWN. **Missing evidence, stated:** a stub-ablation of this clause against the 30-row loading suite. The rubric itself notes this instrument is not yet built (*"a `run_evals.py` stub-ablation mode would make the tier-4 call mechanical; until built, tier-4/2 are text-judged"*).
Self-challenge: a senior author defends it as a genuine differentiator — autonomy is unusual among research skills, and it is the property the spec identifies as routing-relevant (`skill_spec.md` intent #5). Plausible and untested.
Impact: if a no-op, about 28 tok/session wasted; if load-bearing, removing it would degrade routing against interactive-research siblings. Unresolved.
Recommendation: add the ablation arm — run the 30-row loading suite against a variant description with this clause deleted, n>=3, and record the result in `gotchas-log.md` alongside the W5 entry. That single experiment either promotes this to a confirmed slip (D7 tier 6) or retires it permanently.

**[DIM-7-03] [SEVERITY: ADVISORY]** *(evaluator-drift note, not a defect of the skill)*
File: `docs/harness/2026-08-05-run4/findings.md:332` (D7 = 6.0, one finding: `DIM-7-01`) vs this run (D7 = 7.5, same byte-identical description)
Finding: run #4 scored D7 at **6.0** — the rubric's *"2-3 slips"* band — while enumerating exactly **one** slip (`DIM-7-01`, per `grep -nE "DIM-7-[0-9]+"` returning a single ID). One slip is tier 8 by the rubric's own scale, so run #4's score sits a full tier below its own slip count. My 7.5 on the identical text is not a change in the artifact; it is the literal tier applied, minus half a point for DIM-7-02.
Impact: on an unmoved surface, D7 moved 1.5 points between runs. D7 *"ships UNCALIBRATED — first 3 runs manual-reviewed"* and this is the second run to grade it; the divergence is exactly the drift that warning predicts, and it is 1.5 of the total-score delta between runs.
Recommendation: in the calibration review of this run, adjudicate the slip **count** (1 vs 2-3) rather than the score, and record the adjudicated count in `skill-harness/CHANGELOG.md`. The rubric bounds drift to one tier via the slip count only if the count itself is calibrated.

Coverage gaps (D7):
- **No stub-ablation instrument exists**, so the no-op test is text-judged for every phrase except the FR form (which has a real, if n=1, ablation). DIM-7-02 is unresolvable with current tooling.
- Only the FR/EN pair has ablation data. `"analyse multi-sources"` vs `"comparative analysis with sources"` was **not** assessed as a duplication pair: they plausibly name distinct branches (multi-source synthesis vs pairwise comparison) and the W5 ablation removed *"the FR form"* without specifying whether `"analyse multi-sources"` was in scope — so I make no claim. Unresolved, not dismissed.
- D7 is LLM-as-judge with a reproducibility ceiling equal to D2's; DIM-7-03 measures that ceiling empirically at 1.5 points on this target.
- The diff is unreachable from D7.

**Dimension 7 complete.**

---

## Overall score

```
Overall = (D1 8.0x2.0 + D2 7.0x1.5 + D3 7.5x1.5 + D4 8.0x1.5
           + D5 9.0x1.0 + D6 9.5x1.0 + D7 7.5x1.0) / 9.5
        = (16.00 + 10.50 + 11.25 + 12.00 + 9.00 + 9.50 + 7.50) / 9.5
        = 75.75 / 9.5
```

**Overall = 7.97 / 10**

**Verdict: PASS** — gate conditions checked individually:
- Overall >= 7.0 -> **7.97**, met.
- No dimension below 5.0 -> lowest is **D2 at 7.0**, met.
- D1 loading matrix was run -> **90/90 cells, cli backend, `--no-cache`**, met.
- No spec-violation flag in D1 / D3 / D6 -> description **725/1024 chars**, no XML brackets, `lint_skill.py` check#17 did not fire, max Jaccard **0.019**. Met.

**Severity counts: 0 CRITICAL · 10 WARNING · 10 ADVISORY · 1 UNKNOWN — 21 findings.**

| Severity | Count | Findings |
|---|---|---|
| CRITICAL | 0 | *(none)* |
| WARNING | 10 | DIM-1-01, DIM-1-02, DIM-1-03, DIM-1-04, DIM-2-01, DIM-3-02, DIM-4-01, DIM-4-02, DIM-4-04, DIM-6-01 |
| ADVISORY | 10 | DIM-1-05, DIM-2-02, DIM-2-03, DIM-3-01, DIM-3-03, DIM-4-03, DIM-5-01, DIM-5-02, DIM-7-01, DIM-7-03 |
| UNKNOWN | 1 | DIM-7-02 |

No finding reaches CRITICAL: the rubric's auto-CRITICAL triggers are description >1024 chars (725), XML brackets in the description (none), load tier >7,500 (7,199), and peer Jaccard >=0.4 (0.019). None fire. The highest-severity finding is DIM-1-04 (WARNING) — the D1 instrument is not reproducible at n=1 — because it conditions the confidence of every other D1 finding, including the one real routing defect.

---

## Did this harness meaningfully grade the change under review?

**No — and that is the run's most important finding.** `SKILL.md` is byte-identical to run #4's baseline `11a0439`. Mapping each dimension against its *declared rubric inputs*:

| D | Rubric input | Touched by `4d96350`/`05b2937`/`53c4444`? |
|---|---|---|
| D1 | frontmatter description, matrix, lint 4-8 | **UNMOVED** |
| D2 | `SKILL.md` body + `references/` **listing** | **UNMOVED** (reference *content* grew; D2 reads the listing) |
| D3 | index + load tiers | **UNMOVED** (only files tier grew — no rubric threshold) |
| D4 | `evals/` JSONL + `rubric.md` | **UNMOVED** (fixtures landed in `tests/fixtures/solution-space/`) |
| D5 | CHANGELOG + gotchas-log + git | **MOVED** (+2 lines, compliant) |
| D6 | `conflict_check` output | **UNMOVED** |
| D7 | description | **UNMOVED** |

**Six of seven dimensions grade an unmoved surface.** The substance of the diff — a grading path in `references/methodology.md` §6, Rule 7c in `scripts/verify_gates.py` (+82 lines), doctrine in `references/github-research.md` §2b, and an adversarial fixture pair with a positive control — is reached by **no dimension in this rubric**. D5 sees only that a CHANGELOG entry was appended, not whether what it describes is correct.

The change is nonetheless **CI-self-verified**: I executed `tests/check-solution-space.sh` (PASS, exit 0) and confirmed the violation fixture trips Rule 7c, the positive control clears it with 0 violations, and purity guards hold across all 16 fixtures. The CHANGELOG's red-ability claim is corroborated. The diff is *well-tested by the skill's own harness and invisible to this one* — recorded as DIM-4-04, a rubric-coverage defect, not a skill defect.

---

## Coverage gaps — consolidated

**Cross-cutting:**
1. **No dimension reaches `scripts/`, `tests/`, or `references/` content.** The rubric grades the routing surface, the body, the budget, `evals/`, the logs and the Jaccard. A skill whose entire behavioural contract lives below `SKILL.md` — as this one's does — is graded on its cover page. This is the structural gap of the run.
2. **n=1 on every routing cell.** DIM-1-04 quantifies the cost with a within-run control the author did not design for: the same prompt flipped verdict on 2 of 3 models. Both runs land D1 tier 8; neither establishes any individual cell.
3. **The D1 oracle is self-referential** (`hero-queries.md` absent). Graded anyway per the explicit Gate-2 human decision, with the limitation stated at DIM-1-05.
4. **Two of three eval suites are unexecutable by the runner** (DIM-4-02), and two more fixture files are executed by nothing. 28 of 33 non-loading fixtures are declarative coverage.
5. **The harness rubric remains UNCALIBRATED** (`critic-rubric.md:156`, `harness-guide.md` frontmatter). D7 additionally ships uncalibrated in its own right, and DIM-7-03 measures 1.5 points of inter-run drift on an unmoved surface. Prior scores: run #1 = 6.6, #2 = 8.94, #3 = 6.84, #4 = 7.61, this run = 7.97. **Manual review of this run is owed before any score here is trusted at face value.**

**Per dimension:** listed inline at the end of each section above (D1 five gaps · D2 three · D3 three · D4 four · D5 three · D6 four · D7 four).

**Instrument defects found in the harness itself, not the target** — DIM-1-01 (matrix carries no oracle), DIM-1-03 (`_KEBAB_RE` rejects `plugin:skill` names, 3 spurious NO_VERDICTs across two runs), DIM-3-03 (`token_budget.py` counts gitignored bytecode), DIM-4-02 (suite reader keys only on `prompt`), DIM-4-04 (D4 inputs exclude `tests/`), DIM-6-02 (Jaccard corpus is not the router candidate set). Six of twenty-one findings are about the measuring apparatus.

---

## Calibration note

**Run #5** against this target. Prior runs: #1 = 6.6 (FAIL, v0.2.0), #2 = 8.94 (PASS, v0.3.0), #3 = 6.84 (FAIL, AI-355), #4 = 7.61 (PASS, `11a0439`, human-reviewed 2026-08-05 — findings 5/5 confirmed, evaluator judged **too severe** on two tier calls).

Scores are evidence-anchored (90 live router calls with the oracle re-derived from the fixture file, one CI suite executed, two archived matrices cross-compared) but **not face-value-trustworthy**: the rubric is UNCALIBRATED, D7 doubly so. Delta vs run #4 on a byte-identical `SKILL.md` is **+0.36** (7.61 -> 7.97), decomposing as D4 +1.0, D6 +0.5, D7 +1.5, D1/D2/D3/D5 unchanged — i.e. **the entire delta is evaluator drift on unmoved surfaces**, consistent with the prior human note that run #4 graded two tiers too severely. Nothing in the artifact improved between the two runs on any dimension this rubric can see.
