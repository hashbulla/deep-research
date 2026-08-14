# Inferred Spec — `deep-research`

> Analyst artifact for the skill-harness pipeline (run #5). Anchored on `SKILL.md` frontmatter + body. `README.md` read as supplementary framing only; `CHANGELOG.md` / `gotchas-log.md` read as context, never as anchor (harness-guide §3). This document states intent — what the skill is for and when it should fire. It does not grade, does not inventory the folder, and does not prescribe implementation.

## Identity

- **Name:** `deep-research` (`SKILL.md:2`)
- **Version:** unknown — the frontmatter carries exactly three keys (`name`, `description`, `allowed-tools`; verified by parse). There is **no `metadata` block**, so no `version`, `scaffolded_by`, `scaffolded_at` or `replaces` field exists to read.
- **Scaffolded by:** unknown (no metadata block)
- **Scaffolded at:** unknown (no metadata block)
- **Replaces:** none declared in frontmatter
- **Observable frontmatter facts:** `description` = **725 chars**, written as a single unfolded scalar line (verified: not a `>` / `|` block, so the count is not truncated at a newline); `allowed-tools` is an explicit enumerated list (Read, Write, Glob, Grep, AskUserQuestion, WebSearch, five path-scoped `Bash(...)` patterns, Agent, Artifact, Skill, five `mcp__tavily__*`, two `mcp__context7__*`, three `mcp__scrapling__*`); body = 210 lines.
- **Invocation mode:** neither `disable-model-invocation` nor `user-invocable` is present. I record only that observable absence — how the platform resolves the default, and what it implies for rubric dimension 7, is the Critic's call, not mine.

### Scope of "the skill" — one boundary the Critic must not blur

`SKILL_PATH` contains a **second, separate skill**: `suggest-tooling/SKILL.md` declares its own `name: suggest-tooling` and its own description, references, evals and rubric. `SKILL.md:42` and `SKILL.md:138` describe it as a *sibling* invoked only under `--suggest-tooling` (default OFF) which writes a sixth file, while "this engine still emits exactly the five artifacts". It is **out of scope for this spec's intent**. Grading the two as one skill would misread both the token budget and the territorial-conflict surface.

## Confidence

- **Level: MEDIUM** — `SKILL.md`-anchored.
- **Driving signals:**
  - **`hero-queries.md` is absent.** Verified by full-tree `find` for `hero-quer*` — zero hits anywhere under `SKILL_PATH`. Per harness-guide §3 this caps the anchor at MEDIUM. I am not inflating it, and no adjacent artifact substitutes for it (see the circularity caveat below).
  - `SKILL.md` is unusually explicit about intent *and* boundary: a dedicated `## Trigger` section carrying its own anti-trigger list (`:26`), an `## Output Format` contract table (`:143-153`), twelve `## Scope Constraints` (`:157-165`), a 13-case Edge-Case index (`:171-183`), and a References load-tier table (`:193-210`). Intent is stated, not merely implied.
  - The `description` itself names its two nearest neighbours (`/research`, "the plugin-namespaced deep-research sibling") and its own differentiator ("the 7-phase pipeline emitting five NATO-graded, script-verified artifacts"). Territorial intent is explicit at the routing surface.
  - `README.md` tagline corroborates without moving the anchor: "Intelligence-grade multi-source research as a Claude Code skill — source-graded, autonomous-capable, evidence-anchored."
- **Caveats on the anchor itself:**
  - **The anchor is partly a pointer.** `SKILL.md:10` declares *"Where this SKILL.md and `references/methodology.md` disagree, follow the methodology reference — it is the spec."* My anchor therefore explicitly subordinates itself to a file my role forbids me to mine for intent. Any intent statement below that `methodology.md` contradicts is superseded by that file, and I cannot detect such a contradiction from where I stand. This is a real, structural limit on MEDIUM here.
  - **`CHANGELOG.md` carries a knowingly-stale count.** Its `[Unreleased]` section still contains the superseded sentence *"the engine still emits exactly four"*, preserved deliberately under the file's append-only header ("old entries are never rewritten"), with a later entry explicitly superseding it. **The live contract is FIVE** (`SKILL.md:136`, `:143-151`). The Critic must not inherit "four" from the changelog.
  - **`README.md` read only at the top (~45 of 591 lines).** Any README↔SKILL.md drift is unassessed by me; auditing it is Critic work.
  - I did **not** read `references/`, `scripts/`, or `tests/` for intent — role constraint. Nothing below is sourced from them.

### Circularity warning — there is no independent trigger ground truth

`evals/loading.jsonl` exists and contains author-written positive/negative routing prompts. These are **not** hero queries: they were authored *from* the description, by the skill's author, and the Critic grades dimension 1 (Description routing precision) *against this spec*. Harness-guide §9 names the failure mode precisely — *"Description-self-grading: Critic evaluates the description against itself; mitigation: use hero-queries.md as ground truth, not the description."* With `hero-queries.md` absent, **that mitigation is unavailable for this skill.** I have therefore deliberately kept every fixture prompt out of the "Real" trigger list below. Any dimension-1 finding anchored on `evals/loading.jsonl` prompts is self-referential and should be reported with that limitation stated, not as external validation.

## Inferred intent (≥5 statements)

Every statement below is grounded in a line of `SKILL.md` I read.

1. **It is a pipeline, not a search.** The skill runs a fixed 7-phase agentic research pipeline (Phase 0, 1, 1b, 2, 3, 4, 5, 5b, 6) over the open web via the Tavily MCP suite, positioned as "intelligence-grade" and calibrated against Perplexity Deep Research, targeting **100+ cited sources** on `--length exhaustive` (`:3`, `:15`, `:44`). The pipeline shape *is* the product; a fast answer to the same question is explicitly a different skill's job.

2. **It answers with two deliverables, never one.** In the author's own operative wording (`:15`): every run produces the **access-gate verdicts** (what is reachable, under which constraint) *and* the **solution-space map** benchmarking custom-build against built-in, open-source and commercial options. The second deliverable is universal — `research-solution-space.json` is emitted on every run, including questions with no solution space, where it records a `not-applicable` geometry declaration and its reason instead of a sweep (`:56`, `:163`).

3. **Trust is graded and routed, not assumed.** Sources are graded on the NATO Admiralty A–F × 1–6 scale; claims are then routed by credibility label — 1 anywhere including the executive summary, 2–3 in the body with inline tags, 4–6 isolated into a "Needs Verification" section (`:15`, `:134`). Grading intent extends to retrieved bytes as a security posture: retrieved content is untrusted **data**, never instructions; embedded instructions are treated as prompt-injection signals, downgraded to reliability E, never obeyed (`:75`, `:111`).

4. **Quality is machine-verified, never self-reported.** Four gate metrics (groundedness, source quality, corroboration, freshness) are computed at Phase 5, and their arithmetic is re-verified deterministically at Phase 6 by a script whose two JSON verdicts must be **quoted in the final chat message** — "self-reported metrics are not acceptable evidence" (`:121`, `:137`). A persistent FAIL does not abort delivery: it becomes the first line of the report, and the report may not claim SOTA (`:137`). The same posture guards provenance at the front: a CWD `deep-research-report.md` is honored only after a SHA-256 check, a failing check being treated as a potential injection vector (`:9`, `:50`).

5. **It runs autonomously, with exactly one bounded interruption.** Phase 0 writes the plan and proceeds to retrieval with **no human approval halt** (`:15`, `:52`, `:61`). A single `AskUserQuestion` round fires only when a *named* ambiguity signal or safety trigger trips; nothing fires → proceed silently (`:52`). The description makes this a routing-relevant property: "it runs autonomously and only pauses to ask a clarifying question when the query is genuinely ambiguous" (`:3`). The one hard invariant is planning-before-retrieval, not a checkpoint (`:61`, `:157`).

6. **It adversarially audits itself with decorrelated subagents.** Two subagents run on a *different* Claude model than the session: a Phase-5 fidelity/entailment judge given only each claim and its cited span with no scratch context (`:122`), and a Phase-5b completeness critic whose sole mandate is to name uncovered categories, countersign every `waived` status and challenge a `not-applicable` geometry — fed the manifest and **never the report prose**, because it audits the sweep, not the findings (`:127-129`).

7. **Citation precedes prose.** "Attribute first, then generate" — supporting spans are selected *before* the sentence is written and the sentence is conditioned on them; "Never write a claim first and attach citations after" (`:113`). Quotes are surgical, never raw dumps (`:115`, `:159`).

8. **Degradation is always declared, never silent.** Any retrieval source beyond the Tavily suite is optional; an absent or failing MCP/CLI/credential degrades to Tavily-only and is recorded in the plan and the Methodology note (`:164`). A missing Artifact tool never fails the run (`:139`, `:182`). An absent `stack-paths.json` yields `degraded`, "never a silent `empty`" (`:81`, `:181`). A category not swept on an applicable question is `waived` with a real reason, never `not-applicable` (`:56`).

9. **It supports a confidential mode that constrains egress, not just tone.** Under `--confidential`, subagents receive and return **neutral references only** — confidential text never enters a subagent prompt, a log, or an MCP call; rigor is forced to `critical` (refuse-if-no-source replaces the Needs-Verification fallback); and the Artifact render, being egress, is skipped (`:42`, `:139`, `:165`).

*(A tenth statement — that the skill is intended to be "operator-personalized" because it reads a local newsletter corpus and stack inventory keyed to named topics at `:53`, `:72`, `:81` — was drafted and then **removed** under the §8 self-challenge. `SKILL.md` states those mechanisms but never states personalization as a goal, so the statement described what I think the skill is for rather than what it demonstrably declares. The mechanisms themselves are already covered by statement #8 and by the conditional-source bullet under Scope constraints, where they are grounded.)*

## Trigger phrases (real vs derived)

### Real (from `hero-queries.md`)

- **None. `hero-queries.md` does not exist in this skill.** No phrase below is backed by an observed real user query.

### Derived (from `SKILL.md` description + `## Trigger` section, no hero-queries backing)

From the frontmatter `description` (`:3`) — the canonical routing surface:

- `/deep-research`
- "deep research on X"
- "recherche approfondie sur X" (FR)
- "analyse multi-sources" (FR)
- "comparative analysis with sources"
- Semantic frame stated in the description: *"when the user wants a planned, source-graded research report"*

From the body `## Trigger` section (`:23-24`) — the body **explicitly disclaims router authority**: *"Canonical routing surface = the frontmatter `description`; the list below is a body-side convenience, not a second router"* (`:19`). These add two phrasings not present in the description:

- `/deep-research <question>` (slash form with argument)
- "comparative analysis of X vs Y with sources"
- "benchmark X against Y with citations" — **body-only, not in the description**; therefore not routing-load-bearing by the skill's own declaration

### Third category — author-authored probes (NOT ground truth)

`evals/loading.jsonl` ships author-written routing prompts. Per the circularity warning above, they are description-derived artifacts, not independent evidence of what real users type. They are listed here as a category so the Critic knows they exist and knows what they are; I decline to promote any of them into the trigger list.

## Negative boundaries

Do NOT activate for:

From the `description` (`:3`) — routing-load-bearing:

- **Single-fact lookups** — the answer is one fact, no graded artifact set is wanted
- **Known-URL extractions** — the URL is already in hand
- **Library / API documentation lookups** — description names the correct owner: `tavily_skill`
- **Quick research with no graded artifacts** — description names two correct owners: the user-scope `/research` command, **and the plugin-namespaced `deep-research` sibling**. This second one is a same-name collision the author called out explicitly at the routing surface; it is the sharpest declared territorial boundary in the artifact.

From the body `## Trigger` section (`:26`) — body-side convenience, four owners named as tools:

- Single-fact lookups → `tavily_search`
- Known-URL extractions → `tavily_extract`
- Library / API documentation queries → `tavily_skill`
- Domain sitemap discovery → `tavily_map`

**Observation for the Critic, not a finding:** the description's differentiator is stated in terms of *what the run emits* ("the 7-phase pipeline emitting five NATO-graded, script-verified artifacts") and *how it behaves* (autonomous, one conditional clarifying question). The boundary is therefore drawn on **deliverable weight and autonomy**, not on topic. Whether that distinction routes reliably is a dimension-1 question, and it is not mine to answer.

## Output format expectation

A run writes **exactly five files to the invocation CWD**, all written **atomically at the end of Phase 6** — declared as "the first and only artifact write of the run", with Phase 4 explicitly forbidden from writing anything (`:116`, `:136`, `:143`). The five are: `research-plan.md` (composed in Phase 0 *before* any retrieval call), `research-report.md` (in `--lang`, defaulting to the question's language), `research-sources.json` (source records), `research-evidence.json` (claim records: claim → source IDs, credibility, corroboration), and `research-solution-space.json` (one manifest per run, mandatory even on a `not-applicable` geometry). The report itself is structured: executive summary ≤5 bullets, one section per sub-question with inline `[^n]` citations, "Contradictions & open debates", "Needs Verification", a Methodology note, and a footnote source list; a "Solution-space benchmark" table (solution × class × cost × risk × coverage × verdict, every row citing a dated source) is rendered into it, and every `declared_incompleteness` obligation is quoted **verbatim at the TOP** of the report (`:114`, `:135`, `:162`). Beyond the files, the run publishes **one self-contained private Artifact page** as its final step — explicitly *not* a file, nothing written to CWD, skipped on `--confidential` and when the tool is absent, with either skip recorded in the Methodology note and never failing the run (`:139`, `:153`). Terminal chat output is constrained: **both** JSON gate verdicts quoted verbatim, and nothing else — no unrelated commentary, no further-research suggestions beyond the plan, no meta-discussion of the skill's own design (`:137`, `:161`). Under `--suggest-tooling` (default OFF) a sibling skill writes a sixth file, `research-toolbox.md`; this engine still emits exactly five, and unset, "the run is byte-identical" (`:138`).

## Scope constraints

Stated by the skill about itself (`SKILL.md` §Scope Constraints `:157-165`, §Trigger `:26`, §Inputs `:30-44`, §Edge Cases `:171-183`):

- **Planning precedes retrieval, absolutely.** No `mcp__tavily__*` call before `research-plan.md` is written and any triggered step-3 refinement has resolved. Declared non-negotiable — and declared explicitly **not** to be a human approval halt (`:61`, `:157`).
- **Tavily is the retrieval substrate; `WebSearch` is an outage fallback only.** Never fall back while any Tavily tool returns successfully; a fallback is documented in `research-sources.json` `notes` (`:158`).
- **No fabricated URLs or citations** — every `[^n]` resolves to a `research-sources.json` record (`:159`).
- **Tier 4 sources (Reddit, LinkedIn, Medium, Twitter) are never primary evidence** — social signal goes in a "Signals" subsection only (`:159`).
- **No raw extract dumps** — quotes are surgical, ≤3 sentences, attributed (`:159`).
- **No streaming or pagination of a report while phases run** — artifacts are atomic at end of Phase 6 (`:160`).
- **The CRAG loop is not skippable** when gates fail: re-query, or move the failing claim to "Needs Verification" (`:160`).
- **The solution-space manifest is never skipped**, on any run, including `not-applicable` geometries (`:163`).
- **A judge-refused universal or a self-declared non-exhaustive inventory is never consumed as fact** — it becomes a `declared_incompleteness` entry with a stated obligation, quoted at the top of the report (`:162`).
- **Every non-Tavily retrieval source is optional and gated.** GitHub, Academic, Context7, Newsletter signal and OSINT each fire only for a sub-question that passed its named gate at Phase 0 *and* was declared in the plan; Context7 gets "zero calls" on a sub-question that did not pass (`:68-73`).
- **The main agent never calls scrapling.** OSINT rung 3 runs only inside an isolation `Agent` subagent returning sanitized structured data, capped by `--max-stealth` (default 12); credentialed retrieval is refused (`:73`). Paywalls are never scraped — prefer the OA equivalent (`:70`, `:178`).
- **Confidential mode constrains the subagent surface**, not just the prose: neutral references only into and out of subagents; confidential text never reaches a prompt, log or MCP call (`:165`).
- **Input contract:** one required input — a research question in any natural language. Eleven optional flags, all with declared value sets and defaults (`--length`, `--lang`, `--since`, `--profile`, `--rigor`, `--domains`/`--exclude`, `--min-corroboration`, `--model`, `--confidential`, `--suggest-tooling`, `--max-stealth`) (`:30-42`).
- **Progressive disclosure is a declared design constraint**, not incidental: sixteen `references/` files with an explicit "Read at" phase column, and "Load on demand; never all at Phase 0" (`:191-210`). `solution-space.md` is read at Phase 0 **only when the geometry is applicable** (`:196`) — SKILL.md carries an inline minimal contract for the other case (`:54-56`).

## Change under review — context, not anchor

Recorded as fact so the Critic knows what moved; I adjudicate nothing here. Branch `chantier/software-capability-tiering`, **3 commits ahead of `origin/main`** (baseline `11a0439`, run #4's target):

- `4d96350` — software-capability tier grading path: `references/methodology.md` (+20), `scripts/verify_gates.py` (+6)
- `05b2937` — gate Rule 7c (agent-skill class sweep): `references/github-research.md` (+13), `references/solution-space.md` (+1/−1), `scripts/verify_gates.py` (+76)
- `53c4444` — fixture pair + regression test locking Rule 7c: `tests/check-solution-space.sh` (+63/−13), two new fixtures (+378), `CHANGELOG.md` (+2), `.claude/CLAUDE.md` (+1/−1)

**The one intent-relevant fact:** `SKILL.md` is byte-identical to the run #4 baseline. The **routing surface did not change** while the **behavioral contract grew** (a grading path, a gate rule, a fixture pair). Two observations follow, both offered as observations rather than verdicts: (a) the loading measurement recorded for the 2026-08-04 description edit plausibly still applies, since nothing it measured has moved; (b) the new obligations live entirely in `references/` and `scripts/`, i.e. below the surface this spec is anchored on — so my spec cannot describe them, and the Critic reading those files directly will see contract surface I structurally cannot.

## Where I disagree with run #4's spec

I read `docs/harness/2026-08-05-run4/skill_spec.md` and depart from it on three points.

1. **Structure and depth — run #4 exceeded the Analyst's mandate.** It contains a 30-row "Shipped surface" inventory and a 27-item "Contracts the skill imposes on itself" list sourced from `scripts/verify_gates.py` line numbers, `tests/check-solution-space.sh`, `evals/rubric.md` and multiple `references/` files. My role definition forbids exactly that: *"Do NOT reach into `<SKILL_PATH>/scripts/` or `<SKILL_PATH>/references/` for intent — those are implementation, not intent."* Harness-guide §9 names the resulting failure mode: *Cascade errors — an overly specific spec propagates wrong assumptions; mitigation: the Analyst stays at intent level.* It is also redundant work: per §2 the Critic's input is "spec + skill folder + tool outputs" — it reads the folder itself, so a folder inventory in the spec can only add drift. I have written to the role template's section order instead.

2. **Run #4 promoted eval fixtures into its trigger ground truth.** Its "Should fire on" list cites `pos-07`, `pos-11`, `pos-12`, `pos-14`, `pos-15` as evidence of what should fire. Those fixtures were authored from the description; feeding them back as the anchor the Critic grades the description against is the §9 *Description-self-grading* failure mode, whose stated mitigation (use hero-queries.md) is **unavailable here because that file does not exist**. Run #4 did label them "corroborating, not anchor-upgrading" in its Confidence section, which is honest — but they still appear in its "Should fire on" list, where the Critic will read them as spec. I have excluded them from the trigger list and stated the circularity explicitly instead.

3. **Run #4 adjudicated the diff.** Its "Recent change under review" section runs seven numbered points and surfaces a tension between a golden fixture being edited and `evals/rubric.md:45`'s no-editing rule, framed as "two adjacent facts, stated without adjudication". Raising the tension *is* the adjudication — it seeds a dimension-4/5 finding from the Analyst's chair. I have reduced this section to commit stats plus the single intent-relevant fact (routing surface static, behavioral contract grew).

**Where run #4 was right and I concur:** MEDIUM confidence with `hero-queries.md` absent as the driving signal (I reached the same level independently, on the same evidence); scoping `suggest-tooling/` out of intent as a separate skill; and treating `README.md` as supplementary framing that cannot move the anchor.

## Files read

- `/home/ouroz/.claude/skills/skill-harness/agents/skill-harness-analyst.md` (role definition)
- `/home/ouroz/.claude/skills/skill-harness/references/harness-guide.md` (oracle)
- `/home/ouroz/second-brain/20-engineering/skills/deep-research/SKILL.md` (**primary anchor**, full, 210 lines)
- `/home/ouroz/second-brain/20-engineering/skills/deep-research/README.md` (first ~45 of 591 lines — tagline/badges only)
- `/home/ouroz/second-brain/20-engineering/skills/deep-research/CHANGELOG.md` (first 60 of 131 lines — context)
- `/home/ouroz/second-brain/20-engineering/skills/deep-research/gotchas-log.md` (first 30 of 118 lines — context)
- `/home/ouroz/second-brain/20-engineering/skills/deep-research/.claude/CLAUDE.md` — **read** (present in session context in full). It is maintainer-facing project memory, and I declined to source intent statements from it; it did corroborate the 7-phase enumeration, the five-artifact contract and the autonomy posture I took from `SKILL.md`.
- `/home/ouroz/second-brain/20-engineering/skills/deep-research/suggest-tooling/SKILL.md` (first 8 lines — to confirm it is a separate skill)
- `/home/ouroz/second-brain/20-engineering/skills/deep-research/docs/harness/2026-08-05-run4/skill_spec.md` (prior Analyst output — compared, not copied)

**Deliberately not read for intent** (role constraint): `references/*`, `scripts/*`, `tests/*`. **Not read at all:** `deep-research-report.md`, `evals/*.jsonl` contents, `examples/`, `REVIEW.md` (stale run-#2 artifact, gitignored — flagged by the orchestrator as not current state, and I confirm I did not use it).
