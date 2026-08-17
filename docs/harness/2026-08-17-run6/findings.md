# Findings — deep-research (branch `chantier/AI-372-v1x-dettes`, HEAD `3e715fa`)

## Static-check summary

- **lint_skill.py**: exit **1** — 1 ERROR, 3 WARNINGs, 0 infos.
  - ERROR check#1 (folder name kebab-case, `AI-372-v1x-dettes`) — **evaluation artifact, NOT scored.** Verified independently: the shipped folder is `/home/ouroz/second-brain/20-engineering/skills/deep-research` (exists), frontmatter `name: deep-research` (SKILL.md:2).
  - WARNING check#13 — missing `## Examples` (SKILL.md:7). **Real; graded in D2.**
  - WARNING check#17 — `deep-research` matches `forbidden_names.txt`. **Verified pre-existing and a self-collision by construction**: the entry sits under `# Currently deployed skills (collision prevention)`, i.e. the list names *this very skill*. `git log -S 'name: deep-research' -- SKILL.md` returns only `d2a4b16` (initial commit). **Not scored.**
  - WARNING check#18 — `~/.claude/` path at SKILL.md:41, no `compatibility:` declaration. Real but rubric-orphaned; DIM-2-04 ADVISORY.
- **token_budget.py**: exit **0** — index **162** tok (target 100 / local hard 320), load **7,240** tok (target 5,000 / local hard 7,500), files 113,556 tok raw.
  - **FILES TIER inflation verified**: 5 `scripts/__pycache__/*.pyc` sum ~41,369 tok; `.gitignore:25` = `__pycache__/`; `git ls-files | grep -c __pycache__` = **0**. Real shipped files ~72,187 tok.
- **conflict_check.py**: exit **0** — max Jaccard **0.019** (`skill-generator`), **0** critical conflicts across 20 peers.
- **run_evals.py** (read from `loading_matrix.json`, not re-run): suite `loading`, backend `cli`, models = **`["opus"]`** only. `no_verdict_counts.loading.opus = 0`. 15 positives -> all `deep-research`; 16 negatives -> 13 `none` + 3 correct deferrals to other real skills (`scrape`, `research`, `diagnosing-bugs`); **zero leaks to `deep-research`**.

### Original measurement added by this Critic (load-bearing for D3)

Load tier reconstructed across the 5 commits (`git show <rev>:SKILL.md`, same cl100k_base encoder `token_budget.py` uses):

| rev | what | lines | load tok | desc chars |
|---|---|---|---|---|
| `origin/main` | branch point | 210 | **7,199** | 725 |
| `79a8730` | pre-commit hook | 210 | 7,199 | 725 |
| `9831ce9` | dead-sibling clause removed | 210 | 7,199 | **678** |
| `8623fa3` | 209 -> 150-line compression | 151 | **7,099** | 678 |
| `3e715fa` | HEAD (run-accounting step) | 151 | **7,240** | 678 |

Net over the branch: **-59 lines, +41 tokens.** The compression bought **100 tok (-1.4%)** for a **28% line reduction**; the accounting step then added **+141 tok**.

---

## Per-dimension scores

### Dimension 1 — Description routing precision (weight 2.0x)
**Score: 8.5 / 10**

Structural gates clear: description **678/1024 chars**, explicit when-to-use clause, third-person, **no** angle brackets, explicit negative boundaries (SKILL.md:3). The 5.0 coverage-gap ceiling does **not** apply: the matrix ran.

The measured column is flawless. The highest-risk edit in the package — `9831ce9` removing `or the plugin-namespaced deep-research sibling` from the routing surface — did not degrade opus routing on any of the 31 fixtures.

**Tier reasoning (an interpolation, stated as such):** tier 10 is unreachable by construction (it presupposes Opus/Sonnet/Haiku); tier 8 describes 1-2 misses or 1 leak, which is *worse* than measured. 8.5 interpolates "clean on 1 of 3 routers".

Findings:
- **[DIM-1-01] [WARNING]** `loading_matrix.json:4-6` — matrix covers **opus only**, on the branch whose sharpest change is the routing prompt. A weakened description degrades on weaker routers first, and the repo's own history puts the failure exactly there: run #4's `neg-08` leak landed on **sonnet** (CHANGELOG.md:81; gotchas-log.md:39 records the same cell leaking on sonnet *and* haiku under ablation). Fix: run `run_evals.py --suite loading --models opus,sonnet,haiku --backend cli` before any release tag; require >=14/15 positives and >=15/16 negatives per model (`evals/rubric.md:17`). Do not publish "routing verified" — publish "verified on opus".
- **[DIM-1-02] [ADVISORY]** CHANGELOG.md:81 — the repo measured **4 of 90 verdict cells changing in 9 days against a byte-identical description**; gotchas-log.md:41 closes an ablation with "re-open only with an n>=3-per-cell run". This grade is n=1. Fix: n=3 restricted to `neg-07`/`neg-08`/`neg-15`/`neg-16`, grading `neg-16` as the live link.
- **[DIM-1-03] [ADVISORY]** No `hero-queries.md` in the worktree (verified by `find`) — the 15 positives were authored *from* the description they grade. Mitigating: fixtures are live-measured, several are paraphrases not trigger echoes (`pos-07`, `pos-11`, `pos-13`), and `pos-06`'s `boundary` documents which semantics it rides on. Fix: capture 5-10 real invocations into `hero-queries.md`; mark each fixture `oracle_source: hero-query` vs `authored`.

Coverage gaps: no sonnet/haiku signal; n=1 per cell against a demonstrably drifting router; self-referential oracle; the body-side `Trigger` phrase `benchmark X against Y with citations` (SKILL.md:18) has no negative fixture proving it does not route standalone.

Dimension 1 complete. Setting aside findings for dimension 2.

### Dimension 2 — Tax-test compliance (weight 1.5x)
**Score: 7.5 / 10**

150 lines carrying a 7-phase pipeline, the flag contract, 12 scope constraints, a 13-case edge index and 16 reference pointers, with heavy content genuinely offloaded: `references/` is load-on-demand (SKILL.md:145), one file declared never-read-at-runtime (SKILL.md:151), and `solution-space.md` (4,634 tok) made conditional. That is the tier-10 behaviour the rubric names. Workflow is intent-level: each Phase-1 conditional source states its **gate condition** plus reference pointer rather than re-teaching the tool (SKILL.md:56-60). No sentence re-teaches a standard tool.

One clear slip, two documented ambiguities, one measured lint deviation.

Findings:
- **[DIM-2-01] [WARNING]** lint check#13, SKILL.md:7 — **no `## Examples` section.** Deliberate (CHANGELOG.md:43, gotchas-log.md:21: "`Examples` folded into `References` with its content intact") and the content is verifiably intact and reachable (`references/examples.md`, 1,481 tok, pointed to at SKILL.md:150 with its read-moment). Not content loss — a body-contract deviation from the generator's required-section list. Fix: add `## Examples` before `## References` carrying only the pointer sentence currently embedded at SKILL.md:150, and delete that clause from the References bullet. Net ~+2 lines; the 150-line gate has zero headroom, so pair with DIM-2-02.
- **[DIM-2-02] [ADVISORY]** The Artifact-render fact appears **three times**: SKILL.md:14 (Overview closing sentence), :118 (Phase 6 step 7, the instruction), :124 (Output Format, the carve-out defending the five-artifact contract against being read as six). :118 and :124 each do distinct work; **:14 does neither.** Fix: delete the final sentence of SKILL.md:14 — frees the line DIM-2-01 needs.
- **[DIM-2-03] [ADVISORY]** SKILL.md:18 — the `Trigger` section declares itself "a body-side convenience, not a second router", then restates the description's five trigger phrases; the body loads after the description is in context, so the echoes pass no tax test. **Not asserted as a violation**: its `Do NOT activate for` half names the four replacement tools (`tavily_search`/`tavily_extract`/`tavily_skill`/`tavily_map`), which the description carries only partially, and routing-to-the-cheaper-tool is load-bearing at runtime. A senior author defends this as the tool-substitution index. Fix (only if a line is needed): cut the five echoed phrases, keep the negative half and the not-a-router declaration.
- **[DIM-2-04] [ADVISORY]** lint check#18, SKILL.md:41 — `~/.claude/deep-research/newsletter-corpus/` is Claude-Code-specific with no `compatibility:` key. The skill is Claude-Code-native by design (Agent/Artifact/Skill tools, MCP namespaces), so the lint wants a declaration, not a rewrite. Fix: add `compatibility: Targets Claude Code (Agent/Artifact/Skill tools, MCP tool namespaces, user-scope ~/.claude paths).`

Coverage gaps: **rubric coverage gap recorded** — lint checks **#13** and **#18** are enumerated as penalties by **no** rubric dimension; homed here because D2's declared input is "SKILL.md body", and the dock is small because neither measures D2's own object (token waste). Two of three duplication candidates are defensible as deliberate and recorded as ambiguities. The Examples fold's token effect is already inside D3's 7,240 — cross-referenced, not compounded (`see D3`).

Dimension 2 complete. Setting aside findings for dimension 3.

### Dimension 3 — Token-budget hygiene (weight 1.5x)
**Score: 7.0 / 10**

Description **678/1024 chars** — the only public hard cap, 346 chars of margin; 94 words, under the 150-word soft note, no waiver owed. Index **162** tok: between target and local hard cap. Load **7,240** tok: between the 5,000 target and the **7,500 local hard cap**, so **no auto-CRITICAL** — and per `critic-rubric.md:51` (which won against `:53` in the run-#5 adjudication) **no finding below calls any token tier a specification breach**. The published figure is 5,000 *recommended*; the local hard cap is looser than that recommendation.

**Tier reasoning (an interpolation, stated as such):** tier 8's band is load 5,000-6,250 — 7,240 is 990 tok above it. Tier 6's condition is a tier over target *without* documented justification — but CHANGELOG.md:27 carries an explicit, substantive context-budget justification whose argument still covers the +41. The literal tiers bracket this at 6<->8; 7.0 is the midpoint, positioned by the two measured defects below.

Findings:
- **[DIM-3-01] [WARNING]** CHANGELOG.md:21 and :27 — the documented justification quotes **"load 7,199 tok … 301 tok of headroom"**. This branch invalidated both: HEAD measures **7,240 tok / 260 tok headroom**. The *substance* survives; the *figures* are stale — and the entire point of that entry was measurement discipline after the run-#3 D3 failure (gotchas-log.md:67-70, "no re-measurement of a body that grew +49%"). CHANGELOG.md:37's "absorbed the new Phase-6 step at **net-zero lines**, so the 150-line budget gate still passes" is **true exactly as written**; the defect is that no token figure was re-measured beside it. Fix: append one line to the `[Unreleased]` accounting entry — `Load tier re-measured after the Phase-6 step: 7,240 tok (was 7,199 pre-branch; 7,099 post-compression) — 260 tok under the 7,500 local hard cap.`
- **[DIM-3-02] [WARNING]** `tests/check-skill-length.sh:16` (`LIMIT="${SKILL_LINE_LIMIT:-150}"`, measured with `wc -l`), wired at `.github/workflows/validate.yml:30-31` — **the branch's new budget gate counts lines, and no gate anywhere counts tokens.** Verified: `grep -rln "token_budget\|LOAD_HARD\|7500" tests/ .github/` returns **nothing**. The script's header states the rationale in token terms ("SKILL.md is the prompt served on every activation, so its length is a budget"), but newlines are not what the model pays. **This branch is its own counter-example: -59 lines and +41 tokens simultaneously.** A future densification can pass the 150-line gate while pushing the load tier through 7,500 unobserved. Fix: add a CI step after the length check — `python3 <skill-generator>/scripts/token_budget.py . --json`, failing on exit 1 and printing tier warnings otherwise; or a stdlib character-count proxy calibrated against the current 7,240-tok/~28,000-char ratio to stay dependency-free. Keep the line gate: it guards attention, which a token gate does not.
- **[DIM-3-03] [ADVISORY]** `8623fa3` — "209 -> 150 lines by densifying, never deleting" moved the load tier only **7,199 -> 7,099 (-1.4%)**. Rule preservation was the stated goal and is verified (32-marker sweep, gotchas-log.md:21), so this is not a failed change — it is a **misnamed** one. The lever that actually moved context budget was progressive disclosure: the 2026-08-04 remediation took 10,036 -> 7,199 by relocating three sections (CHANGELOG.md:21-26). Fix: for the next reduction, relocate rather than densify. `## Scope Constraints` (SKILL.md:126-133, ~1,000 tok) is the candidate — but note CHANGELOG.md:27 argues that exact block must be resident at plan time, so the move needs its own justification.
- **[DIM-3-04] [ADVISORY]** Index tier **162** tok vs 100 target / 320 local hard (`budget.json:5-9`). Comfortable; the 678-char description does real disambiguation work (D7 finds no filler). **No action.**

Coverage gaps: `token_budget.py` measures the **body only** and is blind to conditional reference reads — the repo did the honest arithmetic itself (CHANGELOG.md:28); the real Phase-0 floor is ~7,240 tok on a not-applicable geometry and ~**11,674** tok on an applicable one (body + `solution-space.md` at 4,634 tok, re-derived from `budget.json:43-45`), and neither figure is gated by anything. The reported FILES TIER is inflated ~41k by untracked `.pyc`; unbounded by the rubric, unscored.

Dimension 3 complete. Setting aside findings for dimension 4.

### Dimension 4 — Eval coverage (weight 1.5x)
**Score: 9.5 / 10**

Every presence condition of the literal tier 10 is met. `evals/loading.jsonl`: **31 rows = 15 positive + 16 negative**, balanced, far past the ~10+10 floor. Territorial negatives name **named siblings**, not just tools: `/scrape` (neg-05), user-scope `/research` (neg-07, marked territorial), `linkedin-post` (neg-10), `deck-generator` (neg-12), `superpowers:dispatching-parallel-agents` (neg-16). `evals/e2e.jsonl`: **16 rows, every one carrying 4-8 mechanical checks** (deterministic commands or transcript predicates). `evals/progressive.jsonl`: **13 rows**. `evals/rubric.md`: 49 lines with per-suite pass bars, the five-failure-mode mapping, an `Adding fixtures` contract and a `Superseding` convention. **Zero placeholder text** (key unions verified: loading `{id,prompt,expect,boundary}`, e2e `{id,invocation,mechanical_checks,rationale}`, progressive `{id,when,expect_read,expect_not_read,note}`).

The branch honoured the skill's **own** fixture contract (`evals/rubric.md:41-45`) — the exact thing it violated at run #3: the description change (`9831ce9`) appended `neg-16`; the run-accounting feature added `e2e-16` with **7** mechanical checks whose load-bearing half is the *negative* assertion (no token or dollar figure anywhere), named at `evals/rubric.md:37`. Item 1 of that contract is correctly not owed by the accounting step — it changes no description surface.

Per the run-#4 precedent (a downward departure grading executability over presence, overturned by human review in favour of the literal tier), executability is recorded below as a **coverage gap, not a dock**.

Findings:
- **[DIM-4-01] [WARNING]** `evals/sycophancy-probes.jsonl` (5 rows) and `evals/benchmark-testset.jsonl` (5 rows) are executed by **nothing** — `run_evals.py --suite` accepts only `loading|progressive|e2e` (CHANGELOG.md:57). This is a *presence*-level defect inside D4's own input surface, not an executability caveat: two files sit in `evals/` that no suite value can name, and `benchmark-testset.jsonl` is on a **declared 4-weekly re-validation cadence** (gotchas-log.md:136) no runner reads, so its staleness can never surface mechanically. Fix: take the repo's own proposal — relocate both to `evals/manual/` (or `docs/eval-protocols/`) so non-executability is visible from the path, and add one line to `evals/rubric.md` naming who runs them and when. Deferring the `--suite` extension is fine; leaving them indistinguishable from executed fixtures is not.
- **[DIM-4-02] [ADVISORY]** CHANGELOG.md:56 — `run_evals.py` reads `entry["prompt"]`, absent from `progressive.jsonl` (keys on `when`) and `e2e.jsonl` (keys on `invocation`), so both suites skip every row and report `[]` with zero failures, "structurally indistinguishable from a perfect score". Consequence for this branch: `e2e-16`, its only behavioral assertion, is **unexercised**, and its load-bearing half is the negative one. Not a defect of this skill (shared harness script) and declared, not hidden. Fix belongs to `skill-generator`; until then read no e2e/progressive evidence on this branch.
- **[DIM-4-03] [ADVISORY]** `neg-08` = `neg-15` = `neg-16` carry **byte-identical prompts** (verified in `loading_matrix.json`), so the 16 negative rows are **14 distinct probes**. This is **declared supersession, not duplication** — `evals/rubric.md:49` codifies the three-link chain and instructs "grade the last link", and the append-only rule forbids editing predecessors. Recorded as **description, not a dock**. Optional future fix: a `superseded_by` key would let the matrix report 14 graded cells and remove the ambiguity for later Critics.

Coverage gaps: only `loading` executes (`e2e` 16 fixtures, `progressive` 13 statically checked); `evals/fixtures/sota-recall/` (3 cases, 6 ground-truth items) has no runner; the `pos-06` `boundary` was edited on this branch (line-pointer re-anchoring `SKILL.md:19` -> marker text) and is verified **not** eval laundering — `git diff` shows `prompt` and `expect` byte-identical, only the `boundary` tail changed, which is exactly what `evals/rubric.md:47` permits.

Dimension 4 complete. Setting aside findings for dimension 5.

### Dimension 5 — Append-mostly hygiene (weight 1.0x)
**Score: 9.5 / 10**

Mechanically verified append-only, not asserted: `git diff --stat origin/main..HEAD -- CHANGELOG.md gotchas-log.md` = **32 insertions, 0 deletions**; `git diff | grep -c '^-[^-]'` = **0** on both. Newest-first respected, semver headings intact, supersession handled by *declaration* rather than rewrite (CHANGELOG.md:19: "Per this file's append-only header the older line is **not rewritten**").

The rubric's tier-4 clause — description changed within 7 days without a CHANGELOG entry — was the run-#3 failure (gotchas-log.md:67-68) and is now **doubly** closed: the description changed 2026-08-17 in `9831ce9`, and the same day produced a CHANGELOG entry (:41) **and** a full gotchas entry (:26-32). Gotcha entries carry the complete template (Trigger/Gotcha/Resolution/Guard), including the honest **"Guard: none for the behavioral half — recorded as instrumentation debt"** (:22) and a fourth field warning the next session that `_KEBAB_RE` will mis-score `neg-16` (:32) — a log entry that materially protected this run. Corroborating against laundering: the negative pass bar was **raised** (14/15 -> 15/16, `evals/rubric.md:17`), not relaxed.

Findings:
- **[DIM-5-01] [ADVISORY]** Same-day paperwork carries two counts for one claim: gotchas-log.md:21 "**All 8 local gates PASS**" vs CHANGELOG.md:44 "**All 9 local gates PASS**". `.github/workflows/validate.yml` runs **11** `bash tests/*.sh` steps plus 3 direct python/gate steps, so neither matches the workflow. A chronological reading defends the pair (the compression commit predates `check-run-accounting.sh`), so **documented as ambiguity, not asserted as error**. Fix: replace both prose counts with the command that produces them — a count in prose rots on every added test.
- **[DIM-5-02] [ADVISORY]** `[Unreleased]` spans **2026-06-12 -> 2026-08-17** with four feature batches and **three separate `### Added` blocks** (CHANGELOG.md:7, :33, :61), while the newest released heading is `[0.3.0] — 2026-06-12` (:101); frontmatter carries no `metadata`/version block (SKILL.md:1-5), so nothing outside this file states which contract is live. Not a rubric penalty — no history rewritten, semver headings exist — but the file has stopped reading as a release history. Fix: cut `0.4.0` at the merge of this branch (a coherent unit: five artifacts, solution-space, Rules 7b/7c, run-accounting) and add `metadata: {version: 0.4.0}` to the frontmatter.

Coverage gaps: both logs graded on content plus git history; no CI step reads either, so the run-#3 root cause ("green CI says nothing about paperwork no CI step reads", gotchas-log.md:68) remains structurally true. The stale 7,199 figure is a currency defect in the CHANGELOG but is graded once, in **D3** (DIM-3-01) — cross-referenced, deliberately not compounded (`see D3`).

Dimension 5 complete. Setting aside findings for dimension 6.

### Dimension 6 — Cross-skill territorial conflicts (weight 1.0x)
**Score: 9.5 / 10**

Max Jaccard **0.019** against 20 peers, **zero** critical conflicts (`conflict.json:3-4`) — an order of magnitude under the tier-10 threshold of 0.1. Every overlap trigram is grammatical boilerplate ("when the user", "do not load"); the one topical hit, `research deep research` shared with `qualify-leads`, sits at **0.005**. No shared exact trigger phrase with any peer. The description carries explicit negative boundaries to its nearest tool peers and to the user-scope `/research` command (SKILL.md:3), and `9831ce9` **improved** this dimension by deleting a boundary pointing at a peer proven absent over 133 installed `SKILL.md` files.

Findings:
- **[DIM-6-01] [WARNING]** SKILL.md:3 — post-edit, the negative-boundary list names **no skill peer at all**: two tools and one slash command. Meanwhile the peer the router *empirically chooses* on the skill's own release-blocker boundary — `superpowers:dispatching-parallel-agents`, per CHANGELOG.md:41 and the runs-#4/#5 record — appears only in a fixture `boundary` and at `evals/rubric.md:7`: in the test contract, **not on the routing surface**. Tier 10 asks for explicit negative boundaries to nearest peers; the nearest *measured* peer is unnamed. The run-#5 adjudication deliberately deferred this edit pending measurement and I am not overriding it. Fix: do **not** edit on the current n=1 evidence — run the n>=3 measurement DIM-1-02 already owes, and if `neg-16` leaks on any model at >=1-in-3, add the peer by name to the `Do NOT load` clause (346 chars of headroom under the cap).
- **[DIM-6-02] [ADVISORY]** `conflict_check.py` scans `~/.claude/skills/*/SKILL.md` only — all 20 peers come from that root. **Plugin-scope skills are invisible to it**, which is exactly why the dead-sibling debt needed a hand-rolled `grep -rl "^name: deep-research" ~/.claude/plugins/` over 133 files to close (CHANGELOG.md:41), and why the one peer that actually competes is absent from the peer set. An instrument gap, not a skill defect — recorded so the 0.019 is not over-read. Fix belongs to `skill-generator` (sweep `~/.claude/plugins/**/skills/*/SKILL.md` and report the roots scanned).

Coverage gaps: peer set is user-scope only (20 skills); plugin- and project-scope peers unmeasured. Jaccard is a trigram proxy and cannot detect semantic territory shared without shared wording — `/research`, the sharpest real neighbour, is a slash command with no `SKILL.md` and is absent from the scan entirely.

Dimension 6 complete. Setting aside findings for dimension 7.

### Dimension 7 — Description economy (weight 1.0x)
**Score: 9.5 / 10**

Model-invoked, so the invocation-mode gate does not apply. Routing is clean (D1 matrix, opus), the precondition for economy to bite. **This dimension grades no token counts** — 678 chars is D3's object.

1. **One-trigger (duplication): 0 slips.** The FR/EN pair `"deep research on X"` / `"recherche approfondie sur X"` is **not** counted — closed by **measured ablation**, not argument: removing the FR form held positives 9/9 but flipped **3 negative cells to leaks**, including the release-blocker boundary on sonnet and haiku (gotchas-log.md:36-41). It empirically survives the no-op test; re-opening requires n>=3 per that entry's own condition. `"analyse multi-sources"` vs `"comparative analysis with sources"` are distinct branches (multi-source synthesis vs comparison), each with its own live-measured fixture (`pos-04`, `pos-05`, `pos-12`).
2. **Filler opener: 0 slips.** Position 1 is `Agentic multi-source deep research via Tavily MCP` — a domain concept, no filler frame.
3. **No-op:** one unresolved candidate.

Findings:
- **[DIM-7-01] [UNKNOWN]** SKILL.md:3, opening clause `calibrated to Perplexity Deep Research (100+ sources on exhaustive runs)` (~74 chars) — a positioning claim, not a trigger. No fixture rides on "Perplexity" or "100+ sources", so deletion plausibly changes no verdict, which would make it a no-op slip. **Severity UNKNOWN because I have no evidence either way**, and the rubric's own mechanization for this (a `run_evals.py` stub-ablation mode) is a queued feature, not an input. Counter-argument that keeps it: it is the only place the description signals *scale*, the discriminator against `/research`, and `pos-07`/`pos-11` route on nearby sourced-report semantics. Adjacent observation, not part of the finding: CHANGELOG.md:71 records the README being "de-benchmarked from Perplexity" while the description still leads with the Perplexity calibration. Fix: settle it the way this repo settled the FR trigger — one ablation variant without the clause, full loading suite, n>=3, keep or cut on the measured negative bar. Do not delete on judgment alone; last time this description was trimmed on an economy argument, the ablation showed the trim leaked negatives.
- **[DIM-7-02] [ADVISORY]** SKILL.md:3 — `9831ce9` excised `or the plugin-namespaced deep-research sibling` from *inside* a parenthetical, leaving one parenthesis that opens at `(use /research` and never closes until the end, so it now carries two unrelated jobs: the redirect target **and** the skill's positive self-description (7-phase, five artifacts, autonomous, one conditional pause). The self-description is genuine invocation work for an orchestrator deciding whether to drive this unattended — the defect is placement, not content, and it costs no economy slip. Fix: close after `(use /research)` and start a new sentence: `This skill is the 7-phase pipeline emitting five NATO-graded, script-verified artifacts; it runs autonomously and only pauses to ask a clarifying question when the query is genuinely ambiguous.` Character-neutral, and it puts the positive contract outside the negative-boundary clause where a router reads it as a reason to fire rather than to defer. **Re-measure the loading suite after this edit** — it touches the routing surface.

Coverage gaps: the no-op test is model-relative and unmechanized, so DIM-7-01 is a genuine unknown, not a hedge — a second Critic could score this dimension one tier either way on that single call. Without a stub-ablation instrument, tiers 4 and 2 remain text-judged; neither is in play here.

Dimension 7 complete.

---

## Overall score

```
Overall = (8.5x2.0 + 7.5x1.5 + 7.0x1.5 + 9.5x1.5 + 9.5x1.0 + 9.5x1.0 + 9.5x1.0) / 9.5
        = (17.00 + 11.25 + 10.50 + 14.25 + 9.50 + 9.50 + 9.50) / 9.5
        = 81.50 / 9.5
        = 8.58
```

| Dim | Object | Weight | Score |
|---|---|---|---|
| D1 | Description routing precision | 2.0x | **8.5** |
| D2 | Tax-test compliance | 1.5x | **7.5** |
| D3 | Token-budget hygiene | 1.5x | **7.0** |
| D4 | Eval coverage | 1.5x | **9.5** |
| D5 | Append-mostly hygiene | 1.0x | **9.5** |
| D6 | Cross-skill territorial conflicts | 1.0x | **9.5** |
| D7 | Description economy | 1.0x | **9.5** |

**Verdict: PASS — 8.58/10.** Overall >=7.0, no dimension below 5.0, and the D1 loading matrix **was** run, so `critic-rubric.md:152`'s "Incomplete" clause does not apply. Zero CRITICAL; no spec-violation flag in D1, D3 or D6 (description 678/1024 chars, no XML brackets, no reserved-name breach introduced by these commits, max Jaccard 0.019, no token tier over its local hard cap).

**The PASS carries one qualification that must travel with it:** routing is verified **on opus only**. The package's highest-risk change is the routing prompt itself, and the router where this skill's historical leak lived — sonnet — was not measured. Per DIM-1-01 and the repo's own instrumentation debt (gotchas-log.md:22, CHANGELOG.md:44), the 3-model loading suite is **owed before any release tag**. Do not report this run as "routing verified".

Findings by severity: **0 CRITICAL / 6 WARNING / 13 ADVISORY / 1 UNKNOWN** (20 total).

Cheapest high-value fixes in order: DIM-3-01 (one CHANGELOG line, restores the measurement property) -> DIM-2-01 + DIM-2-02 (paired, line-neutral) -> DIM-3-02 (one CI step, closes the line-vs-token gap this branch demonstrated) -> DIM-1-01 (the owed 3-model run, which also settles DIM-1-02, DIM-6-01 and DIM-7-01).

## Calibration note

Run **#6** against this target. The repo's CHANGELOG logs runs #2 (8.94), #4 (7.61) and #5 (7.97); run #1 was 6.6 (FAIL), run #3 6.84 (FAIL). Trajectory: 6.6 -> 8.94 -> 6.84 -> 7.61 -> 7.97 -> **8.58**.

`critic-rubric.md:156` ships **UNCALIBRATED** and D7 additionally so; per Anthropic's harness-design guidance scores are trusted at face value only from iteration >=3, and the guide still records `calibration_runs: 0`. **This entry increments no calibration counter and the manual human review of this run is owed.**

Two consecutive human reviews found this evaluator **too severe** on judgment-heavy dimensions — run #4 on D3/D4, run #5 on D2/D7 (CHANGELOG.md:85, :95) — diagnosed as "reads risk *location* well, over-weights risk *magnitude*". Applied here operationally, not merely cited: **D4 is graded at its literal presence tier** rather than departed downward for executability (the exact departure the run-#4 human overturned); **D7 counts zero slips** rather than re-litigating the ablation-closed FR trigger; **D2 and D6 hold their literal tiers** with residual worry placed in finding text, not the number. Every downward move is anchored to a *measured* defect: D3's 7.0 rests on the reconstructed 7,199->7,099->7,240 series and on `grep` proving no token gate exists; D2's 7.5 on a deterministic lint check; D4's and D6's half-points on file-anchored organizational facts.

Three previously-live findings were **not** re-raised, being already adjudicated: the FR/EN trigger pair (measured non-edit, gotchas-log.md:36-41), the `neg-08`/`neg-15`/`neg-16` identical prompts (declared supersession, `evals/rubric.md:49` — recorded as description only), and the absent Phase-0 human approval gate (deliberate removal; gotchas-log.md:97-102 explicitly warns auditors against "restoring" it).

Scores are indices for comparison against runs #2-#5 on the same uncalibrated rubric, not marks.
