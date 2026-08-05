# Findings — deep-research

> Critic phase, worktree-isolated. Target `/home/ouroz/.cache/dr-worktrees/github-topic-facet`,
> branch `chantier/github-topic-facet`, HEAD `11a0439`. Graded against `skill_spec.md` (intent
> anchor, MEDIUM confidence) and `critic-rubric.md` (7 dimensions). Each dimension graded in an
> isolated reasoning pass; no carry-over.

> **Citation pass (skill-harness-citation-grounder, 2026-08-05).** Appended to the Critic's
> findings without altering a single character of finding text, severity, or score. Grounding is
> attached to the **5 WARNING** findings only; the 17 ADVISORY findings are skipped by contract to
> bound cost, and their absence of a Citations block carries no meaning. Sources are Tavily results
> from six searches restricted by `include_domains` to `agentskills.io` · `anthropic.com` ·
> `platform.claude.com` · `github.com/agentskills` · `github.com/anthropics` · `research.perplexity.ai`;
> the `anthropic.com` entry matched the `www.` and `docs.` subdomains, which is why
> `docs.anthropic.com` and `www.anthropic.com` URLs appear below. Every URL was returned by a live
> search this run — none constructed. Citations ground the **rule** that makes each observation a
> finding, never the target's subject-matter facts.
> **Constitutional:** a citation never softens a severity, an empty citation block never invalidates
> a finding, and contradicting evidence is surfaced in its own block for the user to adjudicate —
> never applied.

## Static-check summary

- `lint_skill.py`: **exit 0**, 0 errors, 3 warnings, 0 infos
- `token_budget.py`: **exit 0**, index=**171 tok** (soft 100 / hard 320) / load=**7,199 tok** (soft 5,000 / hard 7,500) / files=**85,934 tok**
- `conflict_check.py`: **exit 0**, max Jaccard=**0.019** (peer `skill-generator`), **0** critical conflicts
- `run_evals.py --suite loading --models opus,sonnet,haiku`: **exit 0**, 87 fresh router calls (cache cold, as the Strategist measured). NO_VERDICT counts: **opus 0, sonnet 0, haiku 2**

### Instrument notes (the instrument lies too)

- **lint check 17 is a FALSE POSITIVE against this target.** It reports `name 'deep-research' matches forbidden substring`. `skill-generator/scripts/forbidden_names.txt:25-40` is a list of names *already taken in this corpus* (`claude-init`, `critical-harness`, `deck-generator`, `humanize-fr`, `impeccable`, …) — a guard against scaffolding a NEW colliding skill. Its remediation ("choose a different name") is incoherent when linting the incumbent. **Not charged to the target.**
- **lint check 16** ("0 `**Input:**` / `**Output:**` blocks") is an instrument-vs-design tension, not a defect: `CHANGELOG.md:84` records the worked examples being moved to `references/examples.md` *specifically* to get under the token cap. Inlining two Input/Output blocks would re-breach D3. **Not charged.**
- **lint check 18 IS a real signal** and is carried as a finding under D2 below.

**Load-bearing consequence of the check-17 dismissal.** D1 rubric tier 2 reads "Description has XML brackets **OR contains a reserved name**" — a spec-violation flag which, under the rubric's Fail clause, would flip this run to CRITICAL/FAIL. It does **not** fire here: `forbidden_names.txt` keeps its genuinely reserved entries under a separate `# Anthropic-reserved per Complete Guide PDF` header (`:5-6`, holding `claude`), while `deep-research` sits at `:33` inside the taken-names block. The dismissal above is therefore not cosmetic — it is what keeps D1 off tier 2, and the Overall-score gate check below cross-references it explicitly.

**Read-only integrity.** Running the target's own `python3 -m py_compile scripts/*.py suggest-tooling/scripts/*.py` (a step the approved strategy listed under §Substitute coverage) refreshed gitignored `__pycache__/*.pyc` files inside the target tree. `git status --short` on the target reports only the untracked `.harness-staging/` — **no tracked content changed**, so the read-only-on-the-artifact constraint holds at tracked-content level. Stated rather than left for a reviewer to notice.

### Substitute coverage executed (Strategist §Substitute coverage)

The target's own CI suite was run in full. **The commit message's claim "Suite complète verte, schémas valides" is CONFIRMED empirically**, not taken on assertion:

| Command | Result |
|---|---|
| `tests/check-solution-space.sh` | **PASS** — 30 assertions incl. the new `oss-prose-only → open-source: status 'swept' requires >=1 GitHub-native query` |
| `tests/check-osint-gates.sh` | **PASS** |
| `tests/check-cross-references.sh` | **PASS** — 85 references, 0 failures |
| `tests/check-provenance.sh` | **PASS** — SHA-256 matches `cb2fe20dced3c4bb` |
| `tests/check-example-invariants.sh` | **PASS** — 16 sources / 15 claims |
| `tests/check-newsletter-search.sh` | **PASS** — 14 assertions |
| `tests/check-marketplace-rank.sh` | **PASS** — T1–T6 + T9 |
| `tests/check-schema.sh` (5 files, workflow args) | **PASS** |
| `python3 -m py_compile scripts/*.py suggest-tooling/scripts/*.py` | **PASS** |
| `verify_gates.py check-solution-space --manifest examples/…` | **PASS** |

`tests/fixtures/solution-space/oss-prose-only.json` was verified to be a **genuine single mutation** of `valid.json` (structural diff: only `categories[open-source].queries` differs) and its mutated content is byte-identical to the *pre-commit* golden — the old golden became the violation fixture. Clean fixture design.

### Adversarial probes run against the new gate (Critic-authored, scratchpad only)

Three probe manifests derived from `valid.json`, run through the shipped `verify_gates.py check-solution-space`. All three returned **verdict PASS, zero violations**:

| Probe | `categories[open-source].queries` | Gate verdict |
|---|---|---|
| A — star-band only, zero topic facets | `["instagram dm python stars:>200", "<prose>"]` | **PASS** |
| B — one prose query carrying a `topic:` token | `["best instagram dm library topic:instagram blog comparison 2026"]` | **PASS** |
| C — exactly one topic combination | `["gh search repos --topic instagram-api --sort stars"]` | **PASS** |

These are the empirical basis for findings DIM-4-01 and DIM-4-05.

### Process note

The ritual `advisor()` pre-completion consult was attempted **four times** across this run and returned `temporarily overloaded` on every attempt. This grading was therefore not escalated. Recorded, not silently skipped.

> **Correction (2026-08-05, appended post-run by the orchestrator on the Critic's own attestation — the note above is kept unedited to preserve the audit trail; the Grounder's zero-modification diff claim describes its own earlier pass and remains true of it).** The note was accurate when first written and is stale by exactly one attempt: a **fifth** `advisor()` call landed after findings.md was first staged. Its four corrections plus one self-caught arithmetic fix were applied — prose, counts and attribution only; **no dimension score changed** (verified identical pre/post at their file positions). The advisor saw both the scores and the prose, recalculated the overall independently, and concluded "PASS stands." This grading WAS therefore escalated, one attempt later than the note records.

---

## Per-dimension scores

### Dimension 1 — Description routing precision (weight 2.0×)

**Score: 8.0 / 10**

Empirical anchor present: the loading matrix ran (87 fresh `claude -p` calls, no API key, cli backend). The matrix carries no `expected_skill` (this suite keys on `expect`/`boundary`), so it was re-joined to `evals/loading.jsonl` on the prompt string per Strategist gap 3: `expect:load` ⇒ pass iff verdict == `deep-research`; `expect:skip` ⇒ pass iff verdict ≠ `deep-research`. NO_VERDICT cells excluded from the denominator.

**Per-model, never pooled:**

| Model | Positives | Negatives | NO_VERDICT |
|---|---|---|---|
| opus | **15 / 15** | **15 / 15** | 0 |
| sonnet | **14 / 15** | **15 / 15** | 0 |
| haiku | **15 / 15** | **13 / 13** | 2 |

**Zero negative leaks across 43 real negative verdicts.** No prompt fired `deep-research` when it should not have — including `neg-14`, the over-fire guard added for the solution-space surface. Against the target's own bar (`evals/rubric.md:15`, ≥14/15 each side), opus and sonnet clear it; release-blocker negatives `neg-07`/`neg-08`/`neg-15` did not fail on any model. Description is **725 / 1024 characters** (99 words) with margin, third-person, no XML brackets, explicit `Do NOT load for…` clause naming four boundaries. Rubric tier 8 is the literal fit: *"One model has 1–2 positive misses … Otherwise clean."*

Findings:

- **[DIM-1] [SEVERITY: WARNING]**
  File: `evals/loading.jsonl:6` (`pos-06`) — cross-ref `SKILL.md:3` vs `SKILL.md:24`
  Finding: the run's **only** positive miss (sonnet returned `none` on *"benchmark Postgres vs DuckDB for analytics workloads with citations"*) lands on a trigger phrase that exists **only in the body's Trigger list** (`SKILL.md:24`: *"benchmark X against Y with citations"*) and **not in the routing `description`** (`SKILL.md:3`, whose nearest phrase is *"comparative analysis with sources"*). `SKILL.md:19` states outright that the body list "is not a second router" — so `pos-06` probes a surface that structurally cannot route. `pos-05`, which uses the description's verbatim phrase, passed 3/3. This is precisely the **Fragile** activation failure mode the target itself defines at `evals/rubric.md:22`.
  Impact: a real user phrasing ("benchmark … with citations") is one model-tier away from silently not loading the skill. The fixture file advertises a trigger the router was never given.
  Recommendation: pick one — (a) add the benchmark/citations branch to the `description` at `SKILL.md:3` (there are 299 characters of headroom under the 1024 cap) and re-run the matrix; or (b) amend `pos-06`'s `boundary` field to state that it rides on *"comparative analysis with sources"* semantics rather than on the body-only phrase, so the fixture stops implying a routing surface that does not exist.

  Citations:
  - Agent Skills — Claude Platform Docs. Level 1 metadata (`name` + `description`) is "Always (at startup)"; Level 2 (the SKILL.md body) is loaded "When Skill is triggered". "The `description` is what Claude matches your request against when determining whether to trigger the Skill". https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview. (Tier 1, Admiralty A1)
  - Optimizing skill descriptions — agentskills.io. "The `description` field in your `SKILL.md` frontmatter is the primary mechanism agents use to decide whether to load a skill for a given task… This means the description carries the entire burden of triggering. If the description doesn't convey when the skill is useful, the agent won't know to reach for it." https://agentskills.io/skill-creation/optimizing-descriptions. (Tier 1, Admiralty A1)
  - Extend Claude with skills — Claude Code Docs. Troubleshooting "Skill doesn't trigger": "Check the description includes keywords users would naturally say." https://docs.anthropic.com/en/docs/claude-code/skills. (Tier 1, Admiralty A1)

- **[DIM-1] [SEVERITY: ADVISORY]**
  File: `evals/loading.jsonl:8` and `evals/loading.jsonl:30` (`neg-08`, `neg-15`)
  Finding: the two rows carry **byte-identical prompts** (verified by prompt-frequency count: 30 rows, 29 unique prompts). The supersession convention at `evals/rubric.md:47` is correctly applied — it changes the `boundary` rationale, never the prompt — but the arithmetic consequence is that the ≥14/15 negative bar counts **one probe twice**, and the two rows can never diverge.
  Impact: the negative side of the pass bar is 15 rows carrying 14 bits of information. A real regression on this boundary costs two "failures" instead of one, and a pass overstates coverage.
  Recommendation: in `evals/rubric.md:15`, state that `neg-08`/`neg-15` share a prompt and count as one probe for the bar (i.e. the negative bar is effectively ≥13/14 distinct probes), or give `neg-15` a semantically equivalent but distinct phrasing of the same boundary.

- **[DIM-1] [SEVERITY: ADVISORY]**
  File: `evals/loading.jsonl:2,5,7,13` (`neg-02`, `neg-05`, `neg-07`, `neg-13`) — measured against the corpus at `~/.claude/skills/` (28 indexed skills, enumerated this run)
  Finding: **9 of the 43 real negative verdicts name a skill that is not in the index the router was shown.** `research` (neg-04/06/07/13) and `scrape` (neg-02/05) do **not** exist as skill directories — verified: `ls /home/ouroz/.claude/skills/` contains neither; they are user-scope *commands*, never indexed by `run_evals.build_skill_index` (`run_evals.py:156-169`, which walks `corpus_root.iterdir()` only). `classify_verdict` (`run_evals.py:73-91`) accepts any kebab-case token, "may name a wrong/hallucinated skill". Sharpest case: `neg-07` (`/research koyeb custom domain peering`) returned `research` on **all three models** — the target's own description (`SKILL.md:3`) literally instructs *"use /research"*, so the router is echoing the artifact's text back rather than a competing skill winning the prompt.
  Impact: those negatives prove **deep-research stayed silent**, which is what `expect: skip` asserts and is a genuine pass. They do **not** prove correct ownership, contrary to how `evals/rubric.md:15` frames `neg-07` as "the documented conflict surface". Only `neg-11` (`diagnosing-bugs`, 3/3) and `neg-10` (`linkedin-post`, sonnet) name skills that actually exist.
  Recommendation: add a sentence to `evals/rubric.md:7` recording that `/research`, `/scrape` and `/fetcher-pick` are user-scope commands absent from any synthetic skill index, so a `neg-07` pass certifies silence only. Do not weaken the fixture — the boundary is real; only the inference from a pass is over-claimed.

- **[DIM-1] [SEVERITY: ADVISORY]**
  File: `evals/rubric.md:15` — measured against `loading_matrix.json` `no_verdict_counts`
  Finding: haiku returned **2 NO_VERDICT** cells, both on the `neg-08`/`neg-15` duplicated prompt. Under the rubric's own rule (NO_VERDICT is a harness coverage gap, never a routing miss) haiku scores 13/13 on negatives. But the target's bar is written as a **raw count** — "≥14/15 negatives" — a numerator haiku cannot reach when two rows are unmeasured, regardless of routing quality.
  Impact: the target's release bar is unsatisfiable for any model whose format compliance is imperfect, which `run_evals.py:76-79` documents as expected for sonnet/haiku. A maintainer applying the bar literally would block a release on a harness artifact.
  Recommendation: restate the bar at `evals/rubric.md:15` as a ratio over *measured* verdicts ("≥14/15 of rows returning a usable verdict"), with an explicit note that NO_VERDICT rows are excluded from both numerator and denominator.

Coverage gaps for D1:

1. **The synthetic corpus is ~6× easier than production.** The index built for this run holds **28** entries (`~/.claude/skills/*/SKILL.md` + target). A live session additionally carries **133** plugin `SKILL.md` files under `~/.claude/plugins/`, plus 4 user-scope commands and project-local skills. A clean 44/45 licenses **no** claim about real-session routing.
2. **The plugin-namespaced `deep-research` sibling does not exist on this machine.** Independently verified: `grep -rl "^name: deep-research" ~/.claude/plugins/` returns nothing across 133 `SKILL.md` files; no plugin directory of that name exists. `neg-08`/`neg-15` can therefore never be satisfied the way their `boundary` field describes.
3. **Router-proxy framing.** `run_evals.py:352` instructs "pick the most specific one" — the documented nearest-neighbour over-fire framing. No leaks were observed here, so the artifact is not implicated; but a clean run under this framing is not equivalent to a clean run under the real router.
4. **This run measures the description left by `1f10507`, not by `11a0439`.** The commit under review does not touch `SKILL.md`. D1 is a **re-measurement** (the spec noted none existed dated 2026-08-05), not a test of this change.
5. **No description-ablation was run.** Whether any individual trigger phrase is load-bearing is unmeasured (see D7).

**Dimension 1 complete. Setting aside findings for dimension 2.**

---

### Dimension 2 — Tax-test compliance (weight 1.5×)

**Score: 7.0 / 10**

The body has just been through deliberate token surgery (10,036 → 7,199 tok, `CHANGELOG.md:18-24`) with heavy content offloaded to **16** reference files, each carrying an explicit read-gate in the References table (`SKILL.md:193-210`). Workflow prose is intent-level and parameterised, not command-prescriptive. That is genuine Tax-Test discipline actively applied. The score is held at 7.0 by one instruction in the reference layer that now **actively misleads** — a sentence that fails the Tax Test in its strongest form, because the agent would do better without it.

> Scope note: the rubric lists D2's inputs as "SKILL.md body, references/ **directory listing**". The finding below concerns reference *contents*. It is attached here as the nearest dimension rather than dropped on a technicality, and cross-referenced to D4, which owns the fact that no executable eval catches it. Graded once, not twice.

Findings:

- **[DIM-2] [SEVERITY: WARNING]** *(see D4-01 — one root, two properties)*
  File: `references/solution-space.md:38` (primary); `references/solution-space.md:21`; `references/anti-patterns.md:85`
  Finding: `SKILL.md:79` mandates reading `references/solution-space.md` at Phase 1b whenever the geometry is applicable. That file's `open-source` **prescribed query vocabulary** (`:38`) is four prose templates — `"<capability> client library"`, `"<protocol> SDK"`, `"self-hosted <capability> bridge"`, `"CLI for <capability>"` — and its anti-example is `"<platform> scraper github"`. **An agent following line 38 verbatim writes a manifest that now FAILS the commit's own Rule 7b** (`scripts/verify_gates.py:552-560`). The commit did not touch this file (`git show --stat HEAD`: `references/solution-space.md` absent). Compounding it, the `open-source` **Instrument** cell at `:21` still summarises `github-research.md` as *"star-band sharding, composite ranking, fake-star gate"* — the topic-facet sweep, now step **2** and the *only gated* step, is absent from the pointer's headline. Meanwhile `github-research.md` itself is read-gated on "a tooling-discovery sub-question" (`SKILL.md:69`, `SKILL.md:205`), while Rule 7b fires on **every** applicable-geometry run whose `open-source` status is `swept`/`empty` — a strictly wider set. `B14` (`references/anti-patterns.md:85`, the "on doubt" surface) likewise still lists prose-only capability vocabulary with no mention of the topic facet.
  Impact: on an applicable-geometry run without a tooling-discovery sub-question, the agent's entire mandated read-path prescribes exactly the query form the Phase-6 gate rejects. It discovers the requirement only when `verify_gates.py` fails — after the retrieval budget is spent — forcing a re-sweep or a `waived` category. The violation string does name the accepted forms, so the agent can recover; that mitigation is why this is WARNING and not CRITICAL. `tests/check-cross-references.sh` cannot catch this: it verifies that link *targets exist* (header lines 3-6), never semantic agreement.
  Recommendation: (1) at `references/solution-space.md:38`, prepend the GitHub-native forms to the "use" column — `gh search repos --topic <class-a> --topic <class-b> --sort stars`, `api.github.com/search/repositories?q=topic:<class>&sort=stars` — and move `site:github.com` into the "never" column; (2) rewrite `:21`'s Instrument cell to lead with "**topic-facet sweep first (≥3 combinations)**, then star-band sharding, composite ranking, fake-star gate"; (3) append one sentence to `B14` at `references/anti-patterns.md:85` naming the topic facet as the language-independent axis.

  Citations:
  - Skill authoring best practices — Claude Platform Docs. Content guidelines §"Use consistent terminology"; pre-share Core-quality checklist carries "Consistent terminology throughout" as an explicit ship gate. The finding is exactly a terminology/vocabulary divergence between the mandated reference (`references/solution-space.md:38`, prose query forms) and the shipped gate (Rule 7b, GitHub-native forms). https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices. (Tier 1, Admiralty A1)
  - Best practices for skill creators — agentskills.io. On progressive disclosure: "The key is telling the agent when to load each file. 'Read `references/api-errors.md` if the API returns a non-200 status code' is more useful than a generic 'see references/ for details.'" Directly supports the read-gate-scope half of the finding — `github-research.md` is gated on "a tooling-discovery sub-question" while Rule 7b fires on a strictly wider set. The same page warns that poor scoping risks "conflicting instructions". https://agentskills.io/skill-creation/best-practices. (Tier 1, Admiralty A1)

- **[DIM-2] [SEVERITY: ADVISORY]**
  File: `SKILL.md:17-26` (the `## Trigger` section)
  Finding: ~10 lines (~150 tokens of the always-loaded body) restate the routing surface, prefaced by the author's own disclaimer at `:19`: *"Canonical routing surface = the frontmatter `description`; the list below is a body-side convenience, not a second router."* The body is loaded **after** routing has already resolved, so this block cannot influence the decision it describes.
  Impact: ~150 tokens against 301 tokens of remaining headroom under the 7,500 hard cap.
  Ambiguity documented, per self-challenge §8.2: a senior author defends this as a **post-load self-check** — an agent that loaded on a borderline prompt can read `:26` and back out — which is a real function the description cannot perform. That defence is why this is ADVISORY, not a violation. It does not survive as *routing* documentation, only as a back-out gate.
  Recommendation: if kept, retitle the section `## Post-load self-check` and drop the positive trigger list at `:23-24` (which does nothing post-load), keeping only the "Do NOT activate for" line at `:26`. That reclaims ~90 tokens and removes the surface that produced the `pos-06` fixture confusion (DIM-1-01).

- **[DIM-2] [SEVERITY: ADVISORY]**
  File: `SKILL.md:116`, `SKILL.md:136`, `SKILL.md:143`, `SKILL.md:160`
  Finding: the atomic-five-artifact write contract is stated **four times** in the body — "No artifact file is written in this phase (B11)" (`:116`), "the first and only artifact write of the run" (`:136`), "Five files, written to the invocation CWD atomically at the end of Phase 6" (`:143`), "artifacts are written atomically at end of Phase 6" (`:160`). The Artifact-skip rule is stated three times (`:139`, `:153`, `:182`).
  Impact: modest token cost on a body at 96% of its hard cap.
  Ambiguity documented: `CHANGELOG.md:36` records **four** fixtures that had encoded the superseded four-artifact contract, which is direct evidence that this contract is empirically the most drifted-from in the skill's history. Deliberate defence-in-depth on the most-violated invariant is defensible and is why this is ADVISORY.
  Recommendation: if headroom is needed, collapse `:160` (Scope Constraints) into a pointer to the `## Output Format` table, keeping `:116` (the Phase-4 negative) and `:136` (the Phase-6 positive), which are the two that fire at decision time.

- **[DIM-2] [SEVERITY: ADVISORY]**
  File: `SKILL.md:53` (lint check 18)
  Finding: the body hardcodes `~/.claude/deep-research/newsletter-corpus/` (and, at `:81`, `~/.claude/deep-research/stack-paths.json`) with **no `compatibility:` frontmatter declaration**. The target ships as a public repo (`LICENSE`, `README.md`, `.github/workflows/validate.yml`), so a consumer on another Agent-Skills host silently gets a dead gate rather than a declared incompatibility.
  Impact: the newsletter-signal and own-stack sources degrade silently off Claude Code. `SKILL.md:164` covers degradation generically ("absent … credential → degrade to Tavily-only, record it"), which limits the blast radius — but the host-specificity itself is undeclared.
  Recommendation: add `compatibility: Targets Claude Code (user-scope paths under ~/.claude/).` to the frontmatter, or rewrite both paths as configurable with a documented default.

- **[DIM-2] [SEVERITY: ADVISORY]**
  File: `references/solution-space.md:53` vs `SKILL.md:83`
  Finding: the sweep-breadth table at `references/solution-space.md:53` is headed **"Web queries across the five web categories"** (short 4–6 / standard 6–12 / exhaustive 12–20), while `SKILL.md:83` scopes the same numbers to **"Tavily calls"**. The two units disagree.
  Impact: the ambiguity was inert until this commit; it is now load-bearing, because the `open-source` category's newly-mandated instrument (≥3 `gh`/`api.github.com` topic queries, `references/github-research.md:2`) is **not** a Tavily call. Read as "web queries", a `--length short` run would spend 3 of its 4–6 total on one category — colliding head-on with the very next sentence at `:57` ("Breadth is spent across categories, not concentrated"). Read as "Tavily calls", there is no conflict. `SKILL.md` is the operative surface, so a senior author defends the Tavily reading — hence ADVISORY, not an asserted contradiction. But note that `e2e-15` pins exactly the tight combination (`--length short` **and** ≥3 topic combinations).
  Recommendation: change the table header at `references/solution-space.md:53` to "**Tavily** queries across the five web categories", and add one sentence stating that GitHub-native queries (`gh`, `api.github.com/search`) are outside this budget.

Coverage gaps for D2:

1. **`README.md` (40 KB) was not read** — the Analyst deliberately skipped it (harness-guide §3), and I did not read it either. Any README/SKILL.md drift is unassessed by this run.
2. **12 of the 16 reference files were not Tax-Tested line by line.** Only `solution-space.md`, `github-research.md`, `anti-patterns.md` (B14/B17) and the diff hunks were read in full. The remaining ~26,000 tokens of reference prose are ungraded.
3. **`suggest-tooling/SKILL.md` (a separate bundled skill) is out of scope** and was not graded.
4. **No runtime evidence.** Whether the body's 7-phase prose actually produces the described behaviour is an e2e question; no live `/deep-research` invocation was run.

**Dimension 2 complete. Setting aside findings for dimension 3.**

---

### Dimension 3 — Token-budget hygiene (weight 1.5×)

**Score: 7.5 / 10**

Consumed directly from `token_budget.py` (re-measured this run, not inherited from the author's report) plus lint check 4.

| Tier | Measured | Soft | Hard | Verdict |
|---|---|---|---|---|
| description | **725 chars** / 99 words | — | **1024 chars** (the only public hard cap) | **under, 299 chars margin** |
| index | **171 tok** | 100 | 320 | over target, well under cap |
| load | **7,199 tok** | 5,000 | 7,500 | **over target, 301 tok (4.0%) under the hard cap** |
| files | 85,934 tok | — | — | no cap applies |

No spec violation: the description is comfortably inside the 1024-char cap and lint reports 0 errors. The score sits between rubric tiers by construction — the **index** tier at 171 lands squarely in tier 8's band (100–320), while the **load** tier at 7,199 is worse than tier 8's second disjunct (5,000–6,250). Tier 6 ("a token tier between target and hard cap **without** a documented justification in `CHANGELOG.md`") is **not** reached: `CHANGELOG.md:24` carries a specific, non-boilerplate context-budget justification, and `CHANGELOG.md:18` documents the index tier explicitly. 7.5 is the honest interpolation. **This commit does not touch `SKILL.md`; the +16 lines it adds land in `references/github-research.md`, a conditional read, so the load tier is unchanged by the change under review.**

Findings:

- **[DIM-3] [SEVERITY: ADVISORY]**
  File: `CHANGELOG.md:18` (measurement of record) — re-measured this run at `.harness-staging/budget.json`
  Finding: the load tier stands at **7,199 / 7,500 tok — 4.0% headroom** — one day after (`CHANGELOG.md:18`, 2026-08-04) the same tier was measured at 10,036 tok, a **+33.8% breach** of the hard cap that shipped with no re-measurement and no waiver. The remediation is real and well-argued, but the operating margin is now ~301 tokens: roughly two Scope Constraints, or one new Phase step.
  Impact: the next body-touching feature re-breaches the cap unless it is preceded by an offload. There is no automated guard — `token_budget.py` is not in `.github/workflows/validate.yml` (13 steps, verified; none invokes it).
  Recommendation: add a CI step to `.github/workflows/validate.yml` running `python3 <skill-generator>/scripts/token_budget.py . --json` and failing the build when the load tier exceeds 7,500 — the only mechanically enforceable guard against a repeat of the 2026-08-04 breach. Absent that, make the 301-token headroom an explicit line in `CHANGELOG.md`'s next entry.

- **[DIM-3] [SEVERITY: ADVISORY]**
  File: `.harness-staging/budget.json` (index tier), cross-ref `SKILL.md:3`
  Finding: index tier is **171 tok against a 100-tok target** (71% over). Driven by a 99-word, 725-character description. Per the rubric, length **per se** is not penalised (Anthropic endorses detailed descriptions up to the 1024-char cap) and no waiver is required below the hard cap of 320. The overage is nonetheless real always-loaded cost paid on every turn of every session, and D7 finds two slips inside it.
  Impact: hygiene only; no spec violation.
  Recommendation: none required on D3 grounds. If the D7 slips are fixed, re-measure — removing the no-op autonomy clause alone would return roughly 25 index tokens.

Coverage gaps for D3:

1. **`token_budget.py` is structurally blind to the reference layer's runtime cost.** It measures the body only. `CHANGELOG.md:25` (author-declared) puts the real Phase-0 floor at **~11,633 tok** on an applicable geometry (7,199 body + 4,434 `solution-space.md`). That figure is **not** graded here and deliberately so: the conditional read *is* correct progressive disclosure, and the author already fixed the unconditional version. Recorded so the number is not mistaken for 7,199 in operation.
2. **The `files` tier (85,934 tok) includes 19,915 tok of `.pyc` bytecode** (`verify_gates`, `github_rank` `__pycache__` entries) read with `errors="replace"`. No cap applies, but the headline number overstates the real reference surface by ~23%.
3. **`suggest-tooling/` is not walked** by `token_budget.py` (`token_budget.py:90` covers only `references/`, `scripts/`, `assets/`, `evals/`). The bundled second skill's budget is unmeasured.

**Dimension 3 complete. Setting aside findings for dimension 4.**

---

### Dimension 4 — Eval coverage (weight 1.5×)

**Score: 7.0 / 10**

By **shape**, this is a tier-10 eval suite: `loading.jsonl` 30 rows perfectly balanced 15 pos / 15 neg (rubric floor ~10+10), negatives carrying the territorial subcategory with named owners, `e2e.jsonl` 15 rows of mechanically-worded checks, `progressive.jsonl` 13 rows, plus `sycophancy-probes.jsonl` (5) and `benchmark-testset.jsonl` (5). `evals/rubric.md` is 48 lines and unusually strong — per-suite pass bars, a five-mode activation failure taxonomy, an "Adding fixtures" contract, and a supersession convention. Zero placeholder text. The deterministic layer is the best I have seen on a skill: **12 single-mutation fixtures each asserted to fire its own violation** (`tests/check-solution-space.sh:6` — "a gate that fails everything is worth as little as one that fails nothing"), all verified green this run.

The score is 7.0 because two **skill-owned** defects were measured, both of which mean the gate this commit ships is weaker than the doctrine it was built to enforce. Per Strategist directive, executability was graded, not presence.

> Scope note (parallel to D2's, stated for the same reason). The rubric lists D4's inputs as "evals/ directory contents; rubric.md presence". The two WARNING findings below anchor on `scripts/verify_gates.py` and `tests/fixtures/solution-space/valid.json` — **neither lives under `evals/`**. No dimension in this rubric owns spec-internal consistency between a gate, its golden fixture and the reference doctrine they encode; D4 is the least-bad home, because the reason the divergence is invisible *is* an eval-coverage fact (the check that would catch it, `e2e-15` #2, is unexecutable). Both findings are measured, not inferred. Attribution stated so it is visible downstream rather than silently absorbed.

Findings:

- **[DIM-4] [SEVERITY: WARNING]** *(see D2-01 — one root, two properties)*
  File: `scripts/verify_gates.py:104` (`GITHUB_NATIVE_QUERY`) and `scripts/verify_gates.py:552-560` (Rule 7b) — measured against `references/github-research.md:2`
  Finding: `references/github-research.md:2` mandates *"Derive **≥3 topic combinations** from the capability classes … each sorted by stars"*, ordered **before** star-band sharding, which the same commit demoted to step 3. Rule 7b enforces **≥1** query matching an alternation that includes `stars:` bands and `gh api`/`gh search`. **Measured, not inferred:** probe A — a manifest whose `open-source.queries` are `["instagram dm python stars:>200", "<prose>"]`, i.e. **zero topic facets** — returns `{"verdict": "PASS", "violations": []}`. Probe C — a single topic combination — likewise PASSes. The gate therefore accepts precisely the retrieval shape the commit's own root-cause analysis identifies as insufficient: `gotchas-log.md:23` argues the fix works *because* "topics are author-assigned, language-independent … the one retrieval axis immune to *my query words encode my hypothesis*", a property a `stars:` band on a keyword query does not have.
  Impact: a manifest can still declare `open-source: swept` having never touched the topic facet — the exact class of miss (8 repos, ~200k stars, `Agent-Reach` 66,684★ with a Chinese-first README) the commit exists to prevent. The gate closes the measured *instance* (prose-only) but not the *class* its own rationale names. The one check that would close it — `e2e-15` mechanical check 2, "≥3 distinct `topic:` combinations" — lands in the suite `run_evals.py` cannot execute (`CHANGELOG.md:40`), so nothing enforces it anywhere.
  Recommendation: strengthen Rule 7b in `scripts/verify_gates.py:552-560` to match the doctrine it cites: require **≥3 distinct `topic:` facet values** (not merely ≥1 GitHub-native query) when `key == "open-source"` and `status in {"swept","empty"}`. Split the regex into `GITHUB_TOPIC_FACET` (`topic:[\w.\-]+`) and `GITHUB_NATIVE_QUERY` (the current alternation), count distinct topic slugs across `live_queries`, and emit a distinct violation string for the under-three case. Then add `probe-starband-only` as fixture #13 in `tests/fixtures/solution-space/` with its expectation row in `tests/check-solution-space.sh` — that turns e2e-15 check 2 into an executed assertion instead of an aspirational one.

  Citations:
  - Demystifying evals for AI agents — Anthropic. The code-based-grader table lists "String match checks (exact, regex, fuzzy, etc.)" as a *separate* method from "Outcome verification" and "Tool calls verification (tools used, parameters)", and names "Lacking in nuance" among their weaknesses — the precise gap between Rule 7b's regex alternation and the retrieval outcome `references/github-research.md:2` mandates. The same page: regression evals "should have a nearly 100% pass rate. They protect against backsliding", which a gate that PASSes the zero-facet probe cannot do. https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents. (Tier 1, Admiralty A1)

- **[DIM-4] [SEVERITY: WARNING]**
  File: `tests/fixtures/solution-space/valid.json:63-67` (the `open-source.queries` array)
  Finding: the corrected golden manifest now holds three queries carrying **exactly 2 distinct topic combinations** — `--topic instagram-api --topic python` (one) and `topic:instagram` (two) — against the ≥3 mandated at `references/github-research.md:2`. `gotchas-log.md:21` names this file as "the reference manifest, **the thing a maintainer copies**" and diagnoses the previous failure as exactly this shape: *"A golden fixture encodes what 'correct' looks like; when the bug is in the definition of correct, twelve adversarial mutation fixtures around it prove only that the mutations differ from the reference."* The trap the author identified one iteration ago **recurs at the next level of the same commit**: the golden was corrected from "prose" to "GitHub-native", but not to "doctrine-conformant".
  Impact: a maintainer copying `valid.json` reproduces a sub-doctrine sweep. Combined with the Rule 7b under-enforcement above, nothing in the executed layer will ever tell them.
  Recommendation: add a third distinct topic combination to `tests/fixtures/solution-space/valid.json:63-67` (e.g. `gh search repos --topic instagram --topic messaging --sort stars`), and — once Rule 7b counts distinct facets per the previous finding — add an assertion in `tests/check-solution-space.sh` that the golden carries ≥3, so the golden is pinned to the doctrine rather than merely to the gate.

  Citations:
  - Demystifying evals for AI agents — Anthropic. Automated evals "Can create false confidence if it doesn't match real usage patterns" and "Requires ongoing maintenance as product and model evolves to avoid drift" — the exact mechanism by which a green suite around a below-doctrine golden reads as coverage. The article's framing of ground truth ("ground truth shifts as reference content changes constantly") is the same failure class the target names at `gotchas-log.md:21`. https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents. (Tier 1, Admiralty A1)
  - Skill authoring best practices — Claude Platform Docs. Core-quality checklist: "Examples are concrete, not abstract"; §Common patterns documents the Examples pattern, the role `valid.json` plays as "the thing a maintainer copies". A reference example that encodes a weaker rule than the skill's own doctrine fails that role. https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices. (Tier 2, Admiralty B2 — supports the reference-artifact role, not the ≥3-facet threshold itself)

- **[DIM-4] [SEVERITY: ADVISORY]**
  File: `evals/e2e.jsonl:15` (`e2e-15`), cross-ref `CHANGELOG.md:40`
  Finding: of `e2e-15`'s five mechanical checks — the carrier of this commit's entire behavioural DoD (`evals/rubric.md:35`) — **checks 4 and 5 are covered by executed CI and verified green by me this run** (`tests/check-solution-space.sh` asserts `valid.json` exits 0 with verdict PASS, and `oss-prose-only` fires *its own* violation naming "GitHub-native query"). **Checks 1, 2 and 3 are executable by nothing shipped**: they require a live `/deep-research` invocation, and the suite they live in is skipped wholesale by `run_evals.py`, which reads `entry["prompt"]` while `e2e.jsonl` keys on `invocation`.
  Impact: 3 of 5 DoD assertions rest on author assertion. Note check 2 is the one that would have caught DIM-4-01 and check 3 the one that would have caught DIM-4-05 — the two unexecutable checks are precisely the two that matter most.
  Ambiguity documented per §8.2: the checks themselves are **well-formed, specific and genuinely mechanical**; the runner's inability to read this schema is a **harness** limitation, already author-declared at `CHANGELOG.md:40` and explicitly out of this skill's scope ("a change to a shared harness script"). It is not charged against the skill's fixture quality. It **is** charged against the claim that the DoD is proven.
  Recommendation: pending a runner fix, port checks 1 and 2 down into the deterministic layer as a fixture assertion (see DIM-4-01's recommendation) — the gate can verify facet count from the manifest alone, with no live run needed. Check 3 (transcript ordering) genuinely requires a live run; record it as such in `evals/rubric.md:35` so the fixture does not read as fully covered.

- **[DIM-4] [SEVERITY: ADVISORY]**
  File: `evals/fixtures/sota-recall/ground-truth.json` (case `wi`) and `evals/fixtures/sota-recall/wi-brief.md` (new, 25 lines)
  Finding: the commit adds a frozen regression case (`wi`: `Panniantong/Agent-Reach`, `jackwener/OpenCLI`, each with `expected_category`, `expected_mechanism`, `accept_when`, `validated`, `miss_root_cause`) and a 25-line replay brief. **No script reads either.** Verified by grep across `tests/`, `scripts/`, `.github/`: the only machine reference into `evals/fixtures/sota-recall/` is `tests/check-solution-space.sh:21` (which loads `stack-paths.fixture.json` for the own-stack sweep) and the `ig`/`unipile` recall property at `:84-86`. `wi`, `Agent-Reach` and `OpenCLI` appear only in a source comment (`scripts/verify_gates.py:548`) and in `e2e-15`'s prose `rationale`.
  Impact: the recall corpus grew from 4 items across 2 cases to 6 across 3, while its **executable** surface did not grow at all. The new case is a manual-replay artifact whose regression value depends on a human remembering to replay it.
  Recommendation: either add an assertion in `tests/check-solution-space.sh` that derives a topic query from the `wi` brief's capability classes and checks the ground-truth items are reachable (offline: assert the recorded `expected_mechanism` matches the topic-sweep form), or state in `evals/fixtures/sota-recall/README.md` that `wi` is a **manual** replay case with a named cadence, so its non-execution is visible rather than assumed.

- **[DIM-4] [SEVERITY: ADVISORY]**
  File: `scripts/verify_gates.py:104` (`GITHUB_NATIVE_QUERY`), cross-ref `gotchas-log.md:17`
  Finding: Rule 7b validates the **shape of an agent-authored string**, not that a GitHub call occurred. **Measured:** probe B — `open-source.queries` = a single Tavily prose query with the literal substring `topic:instagram` typed inside it (`"best instagram dm library topic:instagram blog comparison 2026"`) — returns `{"verdict": "PASS", "violations": []}`. The entry's own title is *"'OSS swept' was checkable only as a word, so it was true only as a word"*; Rule 7b raises the bar from "any word" to "a *shaped* word", which is a real improvement but not a change of kind.
  Impact: the failure mode named in the gotchas title survives one level up. `e2e-15` check 3 (the transcript predicate binding the manifest string to an actual retrieval act) is the only instrument that would close it, and it is unexecutable.
  Ambiguity documented per §8.2: a senior author defends this as **inherent** — a stdlib-only, zero-network script (invariant I4a, `CHANGELOG.md:100`) cannot verify that a network call happened. I agree the constraint is real. The defect is that the residual is **not recorded**: `CHANGELOG.md:38-42` "Known limitations" lists three items and this is not one of them.
  Recommendation: append a fourth bullet to `CHANGELOG.md` §"Known limitations": Rule 7b verifies query *shape*, not that GitHub was queried; the binding check is `e2e-15` check 3, which the current runner cannot execute. One sentence, no code change.

Coverage gaps for D4:

1. **`progressive.jsonl` (13 rows) and `e2e.jsonl` (15 rows) — 28 fixtures — are executed by nothing.** Independently confirmed against the runner's admission rules (`run_evals.py:394-397`: a row without a `prompt` key is silently dropped). `--suite all` emits `"progressive": []` and `"e2e": []`, **structurally identical to a perfect score**. Read as NOT RUN, never as clean. The load-tier non-negotiables (`prog-01/03/11/12`) and every runtime contract (`e2e-01/10/13`, which "invalidate a run on failure") rest on author assertion.
2. **`sycophancy-probes.jsonl` (5) and `benchmark-testset.jsonl` (5) are unreachable** — `--suite` accepts only `loading|progressive|e2e` (`run_evals.py:325`). Author-declared at `CHANGELOG.md:41`.
3. **No live `/deep-research` invocation was run.** Every runtime contract in the spec's list of 19 is unverified behaviourally; only the deterministic layer was exercised.
4. **The example manifest exercises none of this.** `examples/eu-ai-act-2026/research-solution-space.json` is a `not-applicable` geometry (all six categories `not-applicable`, verified: `check-solution-space` returns `applicable: false`), so the CI step at `.github/workflows/validate.yml:46` — the one that runs the gate on real shipped artifacts — **never reaches Rule 7b**. Only the synthetic fixtures do.
5. **`suggest-tooling/evals/`** (own `loading.jsonl`, `e2e.jsonl`, `rubric.md`) is out of scope and ungraded.

**Dimension 4 complete. Setting aside findings for dimension 5.**

---

### Dimension 5 — Append-mostly hygiene (weight 1.0×)

**Score: 9.0 / 10**

The strongest dimension. `git show --stat HEAD` confirms **`CHANGELOG.md +1/-0`** and **`gotchas-log.md +11/-0`** — pure appends, zero rewritten history, against a file that declares "new entries go on top, old entries are never rewritten" (`CHANGELOG.md:3`) and a log declaring "newest first" (`gotchas-log.md:3`). The new gotchas entry (`gotchas-log.md:17-24`) carries every template field plus two beyond it (a "Second-order trap" analysis and a "Why `topic:` and not more keywords" rationale), and its **Guard** field records a **known residual in the author's own words** rather than omitting it. The description-changed-without-CHANGELOG tier-4 clause does not fire: the 2026-08-04 description edit is documented at `CHANGELOG.md:17` with its re-measurement. CHANGELOG is semver-tagged (`[0.3.0]`, `[0.2.0]`, `[0.1.1]`, `[0.1.0]`) under an `[Unreleased]` block. This is what the rubric's tier 10 describes; two small blemishes hold it at 9.0.

Findings:

- **[DIM-5] [SEVERITY: ADVISORY]**
  File: `evals/rubric.md:42` vs `gotchas-log.md:24` (the Guard field's "Known residual")
  Finding: the Guard states that items **1 and 2** of the "Adding fixtures" contract were not added, on the grounds that "this change alters no routing surface and leaves `SKILL.md`'s description untouched". **Item 1 is validly waived**: `evals/rubric.md:41` conditions it explicitly — "≥1 positive loading fixture … **(if it changes the description)**" — and the description is verifiably unchanged (`git show --stat HEAD`: `SKILL.md` absent). **Item 2 carries no such condition**: `evals/rubric.md:42` reads flatly "≥1 negative fixture for its nearest territorial neighbor". The author's substitute argument — that the `valid.json` / `oss-prose-only.json` mutation pair "plays the positive/negative role at the layer where this feature actually lives" — is a good argument about *layer*, but item 2 is about *territory*, a different property.
  Impact: a genuine deviation from the skill's own contract. Its practical cost is near zero here (a gate rule has no territorial neighbour to defend against), and it was **recorded rather than silently skipped**, which is exactly what `evals/rubric.md:45` asks for. Severity is ADVISORY on that basis.
  Recommendation: amend `evals/rubric.md:42` to carry the condition the author is in practice applying — "≥1 negative fixture for its nearest territorial neighbour **(if the feature adds a routing surface)**" — so the contract states the rule that is actually being followed, rather than accumulating waivers against a rule nobody intends to meet.

- **[DIM-5] [SEVERITY: ADVISORY]**
  File: `CHANGELOG.md:7` and `CHANGELOG.md:44` (two `### Added`); `CHANGELOG.md:14` and `CHANGELOG.md:51` (two `### Changed`)
  Finding: the `[Unreleased]` section contains **two `### Added` blocks and two `### Changed` blocks**. Keep a Changelog 1.1.0 — which `CHANGELOG.md:3` names as the governing format — specifies one block per change type per release section.
  Impact: cosmetic but real: a reader scanning `[Unreleased] → Added` sees the first block and can miss the second (which holds the OSINT/SOCMINT and `suggest-tooling` entries). It is a structural by-product of strict prepend-only appending, not of rewritten history.
  Recommendation: at the next release tag, merge the duplicate headings when `[Unreleased]` is promoted to a version block — merging *within an unreleased section* is not history rewriting, since nothing under `[Unreleased]` has ever been published as a version.

Coverage gaps for D5:

1. **Only `git log -12` and `git show --stat HEAD` were consulted.** Whether older CHANGELOG or gotchas entries were ever edited in prior commits was not audited (`git log -p` on those two files was not run).
2. **The maintenance-cadence table (`gotchas-log.md:94-101`) was not verified against reality** — e.g. whether the tier registry was in fact reviewed quarterly since 2026-04-17, or the Perplexity benchmark set 4-weekly since 2026-06-12. The cadences are declared; compliance is unmeasured.
3. **`evals/rubric.md:3` requires run results (date, model, pass-rate) to be logged as `gotchas-log.md` entries.** The 39/39 measurement of 2026-08-04 is recorded in `CHANGELOG.md:17` but **not** as a gotchas entry. Not scored — the CHANGELOG record satisfies the spirit and the rubric's letter is arguably about *this* file only — flagged so the next maintainer picks one home.

**Dimension 5 complete. Setting aside findings for dimension 6.**

---

### Dimension 6 — Cross-skill territorial conflicts (weight 1.0×)

**Score: 9.0 / 10**

`conflict_check.py` returns **max Jaccard 0.019** against `skill-generator`, with an empty `critical` array — an order of magnitude below the 0.1 tier-10 threshold. Every overlapping trigram is boilerplate connective tissue ("when the user", "do not load", "load when the"), not domain vocabulary. The single domain-bearing overlap is `qualify-leads` at **0.005** sharing "research deep research" — negligible. The description carries explicit negative boundaries naming four distinct owners (`tavily_search`-class single-fact lookups, known-URL extractions, `tavily_skill` for docs, `/research` and the plugin sibling for ungraded research). Self-comparison was correctly avoided: the deployed `~/.claude/skills/deep-research` symlink is excluded by `conflict_check.py:109`'s name-equality clause, verified — no `deep-research` peer row appears in the output. This commit changes no routing surface, so D6 is unaffected by it.

Findings:

- **[DIM-6] [SEVERITY: ADVISORY]**
  File: `.harness-staging/conflict.json` (20 peers scanned) vs `evals/rubric.md:15`
  Finding: `evals/rubric.md:15` designates two specific peers as "the documented conflict surface" and makes failures against them release blockers: the user-scope `/research` command and the plugin-namespaced `deep-research` sibling. **Neither is in the corpus `conflict_check.py` scans.** Verified: `ls /home/ouroz/.claude/skills/` contains no `research`, `scrape` or `fetcher-pick` directory (they are user-scope *commands* under `~/.claude/commands/`, 4 files); and `grep -rl "^name: deep-research" ~/.claude/plugins/` returns nothing across **133** plugin `SKILL.md` files. The 0.019 is therefore measured against a corpus that **excludes both** of the author's own named neighbours.
  Impact: the clean Jaccard is real but under-scoped. It certifies no collision with the 27 user-scope skills; it says nothing about the two surfaces the author considers the actual risk.
  Recommendation: none against the target — this is an instrument scope limit (`conflict_check.py` walks a single skills corpus by design), not a defect in the skill. Recorded so the 0.019 is not read as "no territorial risk". If the collision matters, measure it by hand: compute the description Jaccard against `~/.claude/commands/research.md` once and record the figure in `evals/rubric.md`.

- **[DIM-6] [SEVERITY: ADVISORY]**
  File: `SKILL.md:3` (the `description`'s closing clause)
  Finding: the description instructs the router to defer to "**the plugin-namespaced `deep-research` sibling**" for quick research. That sibling **does not exist on this machine** (0 of 133 plugin `SKILL.md` files carry `name: deep-research`; no plugin directory of that name). The negative boundary names an owner the router cannot select.
  Impact: on this machine the clause degrades from "defer to X" into a bare "don't fire", which is weaker guidance. It cost nothing in the matrix — `neg-08`/`neg-15` returned `none` on opus and sonnet, i.e. the router fell back to no-route correctly — so the practical impact is nil today.
  Ambiguity documented per §8.2: the skill ships as a **public repo**, and the clause is written for the general consumer who *does* have the plugin installed. That is a legitimate authoring choice, and is why this is ADVISORY rather than a defect.
  Recommendation: no change required. If the clause is ever revised, prefer a capability description ("a lighter research skill in your plugin set") over a name the local index may not contain — a name the router cannot resolve is a weaker negative than a described class.

Coverage gaps for D6:

1. **`conflict_check.py` scanned 20 peers**, while `~/.claude/skills/` holds 28 SKILL.md files — the 8 not reported are presumably 0.0-Jaccard tail entries, but the truncation was not verified.
2. **133 plugin skills and 4 user-scope commands are outside the instrument entirely.** Real-session territorial pressure is ~6× what was measured.
3. **The bundled `suggest-tooling/SKILL.md` was not conflict-checked against its parent.** Two skills ship in one folder; whether their descriptions collide is unmeasured.
4. **Trigger-phrase intersection was checked only via trigram Jaccard**, not by exact-phrase matching against peer descriptions.

**Dimension 6 complete. Setting aside findings for dimension 7.**

---

### Dimension 7 — Description economy (weight 1.0×)

**Score: 6.0 / 10**

**Invocation-mode gate: D7 applies.** `SKILL.md` frontmatter carries no `disable-model-invocation`, so the skill is model-invoked and its description is always-loaded text paid every turn. D7 is graded, not defaulted.

**Precondition met:** D7 "only bites when routing already passes" — the D1 matrix is clean (44/45 positives, zero leaks), so economy is the live question. Grading the three LLM-judge prompts on the 725-character description at `SKILL.md:3`, counting **slips**:

| Prompt | Result |
|---|---|
| **Filler opener** | **0 slips.** Position 1 is "Agentic multi-source deep research via Tavily MCP" — a domain concept, no "A skill that…" / "Use this to…" frame. Clean. |
| **One-trigger** | **1 slip** — see below. |
| **No-op** | **1 slip** — see below. |

Two slips. That is the rubric's tier-6 band, and it is the rubric's **own worked example** of it: *"6: 2–3 slips (e.g. an FR/EN synonym block + one no-op sentence)"*. No rounding up: this is a 6.0, not "almost a 7". The tier is stable under a stricter reading too — a critic who additionally counted "calibrated to Perplexity Deep Research (100+ sources on exhaustive runs)" as a no-op would reach 3 slips, still tier 6.

Findings:

- **[DIM-7] [SEVERITY: WARNING]**
  File: `SKILL.md:3` — the trigger list `"deep research on X"` / `"recherche approfondie sur X"`
  Finding: the description's trigger list names the same branch in two languages. `"deep research on X"` and `"recherche approfondie sur X"` are a direct FR/EN synonym pair for one branch — the pattern the rubric names verbatim as a duplication slip ("the same branch phrased twice (FR/EN synonym pairs …). One trigger per branch"). The remaining triggers are distinct: `/deep-research` (slash form), `"analyse multi-sources"` (multi-source synthesis) and `"comparative analysis with sources"` (comparison + citation) each name a branch of their own.
  Impact: always-loaded index cost for a branch a semantic router very likely resolves from either form. Roughly 30 index tokens.
  Ambiguity documented per §8.2: a senior author defends this for a francophone operator — the skill ships FR positives (`pos-03`, `pos-09`, `pos-15`, all 3/3 in this run) and an FR output flag, and a lexical router genuinely would need both. **A pass does not prove necessity**; only an ablation does, and none exists (see coverage gap 1). The finding is recorded as the rubric specifies while the ambiguity is stated, not used to soften it.
  Recommendation: do **not** edit blind. Run the ablation first: build a variant description with `"recherche approfondie sur X"` removed, re-run `run_evals.py --suite loading` and compare the FR positives (`pos-03`, `pos-09`, `pos-15`) across all three models. If they hold, drop the FR synonym and record the measurement in `CHANGELOG.md`; if any drops, keep it and record **that** measurement — which converts this finding into a documented, evidence-backed non-slip. Either outcome closes it permanently.

  Citations:
  - Remove redundant phrasing from skill descriptions · Issue #327 · anthropics/claude-plugins-official. Anthropic's own official plugin repo tracks redundant description phrasing as a defect across 8 shipped skills, on the grounds that the field exists "to tell Claude when to invoke the skill" and anything beyond that "adds unnecessary verbosity". Establishes that description redundancy is a recognized authoring defect, not a Critic invention. https://github.com/anthropics/claude-plugins-official/issues/327. (Tier 2, Admiralty B2 — vendor issue tracker, not spec)
  - Agent Skills — Claude Platform Docs. Prices the finding: Level 1 metadata is loaded "Always (at startup)" at "~100 tokens per Skill", so every description token is paid on every turn whether or not the skill fires. https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview. (Tier 1, Admiralty A1)
  - Skill authoring best practices — Claude Platform Docs. Core principles open with "Concise is key". https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices. (Tier 1, Admiralty A1)

  Contradicting evidence:
  - Extend Claude with skills — Claude Code Docs. Troubleshooting "Skill doesn't trigger" instructs: "Check the description includes keywords users would naturally say." For a francophone operator — and this skill ships three FR positive fixtures, all 3/3 — *"recherche approfondie sur X"* **is** the keyword naturally said, which argues the FR form is a distinct triggering surface rather than a synonym of the EN one. https://docs.anthropic.com/en/docs/claude-code/skills. (Tier 1, Admiralty A1)
  - Skill authoring best practices — Claude Platform Docs. "Be specific and include key terms. Include both what the Skill does and specific triggers/contexts for when to use it." Endorses carrying explicit trigger phrasings in the description rather than minimising them. https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices. (Tier 1, Admiralty A1)
  - Issue #327 (same source as citation 1) additionally self-labels description redundancy "Low priority — cosmetic improvement that doesn't affect functionality", which cuts against WARNING severity — though it addresses a different redundancy class (a meta-commentary opener), not a synonym pair.

  *Adjudication is the user's. Severity stays WARNING; no citation above was applied to soften it. The Critic's own recommendation — run the ablation before editing — is the action both sides of this evidence support.*

- **[DIM-7] [SEVERITY: ADVISORY]**
  File: `SKILL.md:3` — the closing clause *"it runs autonomously and only pauses to ask a clarifying question when the query is genuinely ambiguous"*
  Finding: fails the no-op test. This is **behavioural documentation, not a trigger**: no plausible user prompt routes on "runs autonomously", and deleting it changes no routing verdict. The same fact is already stated twice in the body where it is actionable — `SKILL.md:52` (Phase 0 step 3, the conditional `AskUserQuestion` round) and `SKILL.md:61` (step 9, "no approval halt"). ~110 characters / ~25 tokens of always-loaded index text describing runtime behaviour.
  Impact: index tier is already 71% over its 100-token target (D3); this clause is pure cost inside that overage. It is the cleanest slip in the description.
  Recommendation: delete the clause from `SKILL.md:3`. The preceding phrase — "this skill is the 7-phase pipeline emitting five NATO-graded, script-verified artifacts" — already carries the full discriminator against the quick-research sibling, which is the invocation work this sentence region has to do. Re-measure the index tier and re-run the loading matrix afterwards; record both in `CHANGELOG.md` per `evals/rubric.md:3`.

Coverage gaps for D7:

1. **No ablation was run — the instrument does not exist.** The rubric names a `run_evals.py` stub-ablation mode as the mechanism that would make the no-op test mechanical, and records it as a **queued feature, not yet built**. Both slips above are therefore **text-judged, not measured**. A second Critic may legitimately split by one slip; the slip count bounds that drift to one tier.
2. **D7 ships UNCALIBRATED** (rubric: first 3 runs manual-reviewed). This dimension's score should not be trusted at face value.
3. **The `suggest-tooling` sibling's description was not graded** — out of scope.
4. **Cross-reference to D6 checked and cleared:** the FR/EN block is an internal duplication only; no peer shares those tokens (max Jaccard 0.019, no FR trigrams in the overlap set). It is one true signal, not two — graded on D7 alone, severity not compounded.

**Dimension 7 complete.**

---

## Overall score

```
Overall = (8.0×2.0 + 7.0×1.5 + 7.5×1.5 + 7.0×1.5 + 9.0×1.0 + 9.0×1.0 + 6.0×1.0) / 9.5
        = (16.00 + 10.50 + 11.25 + 10.50 + 9.00 + 9.00 + 6.00) / 9.5
        = 72.25 / 9.5
        = 7.61 / 10
```

| Dim | Name | Weight | Score |
|---|---|---|---|
| 1 | Description routing precision | 2.0× | **8.0** |
| 2 | Tax-test compliance | 1.5× | **7.0** |
| 3 | Token-budget hygiene | 1.5× | **7.5** |
| 4 | Eval coverage | 1.5× | **7.0** |
| 5 | Append-mostly hygiene | 1.0× | **9.0** |
| 6 | Cross-skill territorial conflicts | 1.0× | **9.0** |
| 7 | Description economy | 1.0× | **6.0** |

**Overall = 7.61 / 10**

**Verdict: PASS**

Gate check, all three conditions required:
- Overall ≥ 7.0 — **7.61**, met.
- No dimension below 5.0 — lowest is **D7 at 6.0**, met.
- The D1 loading matrix was run — **yes**, 87 fresh calls, exit 0, cli backend, no API key. Met.

No spec-violation flag fires in dimensions 1, 3 or 6: description is 725/1024 characters, contains no XML brackets, carries a when-to-use clause and explicit negative boundaries; load tier is under the 7,500 hard cap; max peer Jaccard is 0.019 against a 0.4 threshold. **The D1 tier-2 reserved-name flag does not fire — `lint_skill.py` check 17 is an instrument false positive, see §Instrument notes.** This is the one dismissal the PASS verdict depends on; had `deep-research` been a genuinely reserved name, the rubric's Fail clause would make this run CRITICAL/FAIL regardless of the 7.61.

**Finding counts:** 0 CRITICAL · 5 WARNING · 17 ADVISORY · 0 UNKNOWN.
(ADVISORY by dimension: D1 3 · D2 4 · D3 2 · D4 3 · D5 2 · D6 2 · D7 1.)

WARNING findings, ranked:
1. **DIM-4-01** — Rule 7b accepts a manifest with zero topic facets (measured); the doctrine it encodes mandates ≥3.
2. **DIM-2-01** — the mandated Phase-1b read (`references/solution-space.md:38`) prescribes prose open-source queries that now fail Rule 7b.
3. **DIM-4-02** — the corrected golden `valid.json` carries 2 of the mandated ≥3 topic combinations; the "golden encodes a below-doctrine correct" trap recurs.
4. **DIM-1-01** — the run's only positive miss (sonnet, `pos-06`) lands on a phrase present only in the body's non-routing Trigger list.
5. **DIM-7-01** — FR/EN synonym trigger pair in the always-loaded description.

Findings 1–3 share a single root and a coordinated fix: **the gate, the golden and the mandated reference all encode a weaker rule than `references/github-research.md:2` states.** The commit message's claim "Suite complète verte, schémas valides" is **true and independently confirmed** — and the suite being green is precisely why the divergence is invisible.

## Calibration note

**Run #4** against this target (`CHANGELOG.md` records run #1 = 6.6 FAIL / 0.2.0, run #2 = 8.94 PASS / 0.3.0 at `:56-58`, run #3 = 6.84 FAIL / AI-355 at `gotchas-log.md:30`). The skill-harness rubric itself remains **UNCALIBRATED** — `critic-rubric.md:156` and `harness-guide.md` frontmatter (`calibration_runs: 0`) require ≥3 human-reviewed calibration rounds before any score is trusted at face value, and Dimension 7 additionally ships uncalibrated in its own right. Scores here are evidence-anchored (87 live router calls, 10 CI suites executed, 3 adversarial gate probes) but **not yet face-value-trustworthy**. Manual review of this run is owed.

Prior-run trajectory for context, not for grading: 6.6 → 8.94 → 6.84 → **7.61**.

### Deliberate departures from the rubric's literal tier (declared, so the calibration comparison lands on a fixed target)

Both departures are **downward**; the no-rounding-up rule is unthreatened. They are named because run #4 against an uncalibrated rubric exists to be compared against human judgment, and an undocumented departure makes that comparison meaningless.

- **D3 graded 7.5; the literal tier is 8.** Tier 8 reads "Index tier 100-320 **OR** load tier 5,000-6,250", and the index at **171** satisfies the first disjunct outright. Tier 6's penalty condition ("without a documented justification in `CHANGELOG.md`") is not met either, since `CHANGELOG.md:24` supplies a specific one. Graded 7.5 rather than 8.0 because the **load** tier at 7,199 sits outside tier 8's own band and at 96% of the hard cap, one day after a +33.8% breach of that cap, with no CI guard. A grader applying tier 8 literally would score 8.0 and be defensible.
- **D4 graded 7.0; the literal tier is 10.** Every tier-10 condition is met on shape: all eval files populated, 15+15 balanced loading (floor ~10+10), progressive present at 13, 15 e2e fixtures with mechanical checks, `rubric.md` detailed. None of tiers 8/6/4/2 fires — no file missing, no placeholder text, no counts under. Graded 7.0 on the Strategist's explicit directive to grade *executability* over presence, and on two measured skill-owned defects (DIM-4-01, DIM-4-02) for which the rubric's presence-oriented tiers have no language. A grader applying the tiers literally would score 10.0.

Net effect of both departures on the Overall: **−0.55**. Literal tiers (D3 8.0, D4 10.0, all others unchanged) give `(16.00 + 10.50 + 12.00 + 15.00 + 9.00 + 9.00 + 6.00) / 9.5 = 77.50 / 9.5 = 8.16`; as graded, `72.25 / 9.5 = 7.61`. The verdict is **PASS under either reading**, so the departures change the reported score, never the outcome.
