# Inferred Spec — deep-research

> Grounding note: this spec is derived **exclusively** from the worktree at
> `/home/ouroz/.cache/claude-worktrees/AI-372-v1x-dettes` (branch
> `chantier/AI-372-v1x-dettes`, HEAD `3e715fa`). The worktree folder name is
> not the skill name; frontmatter `name` is `deep-research`. Any text from the
> *installed* copy of this skill at `~/.claude/skills/deep-research` is out of
> scope and was deliberately excluded — notably, the installed description still
> names a "plugin-namespaced deep-research sibling" that commit `9831ce9`
> removed from this branch's routing surface.

## Identity
- Name: `deep-research` (SKILL.md:2)
- Version: **unknown** — the frontmatter carries no `metadata` block; the only
  frontmatter keys are `name`, `description`, `allowed-tools` (SKILL.md:1–5).
  Grounded context: CHANGELOG.md's latest *released* heading is `[0.3.0] — 2026-06-12`
  (CHANGELOG.md:101), with a substantial `[Unreleased]` section above it
  (CHANGELOG.md:5).
- Scaffolded by: **unknown** (no `metadata.scaffolded_by`)
- Scaffolded at: **unknown** (no `metadata.scaffolded_at`)
- Replaces: **none declared** (no `metadata.replaces`)
- Also absent from frontmatter: `license`, `compatibility` (a MIT `LICENSE` file
  exists at the repo root, but it is not declared in frontmatter).
- Packaging: self-contained git repository (own `.git`, `LICENSE`, `README.md`,
  `CHANGELOG.md`, `.githooks/pre-commit`, `.github/workflows/`), installed by
  cloning into `~/.claude/skills/deep-research` (README.md:109).

## Confidence
- Level: **MEDIUM**
- Driving signals:
  - No `hero-queries.md` exists anywhere in the worktree (verified by `find`), so
    the HIGH anchor defined by the harness oracle §3 is unavailable.
  - `SKILL.md` is the primary anchor: 150 lines, fully populated, zero
    `<REPLACE:` placeholders, with explicit `Trigger`, `Inputs`, `Workflow`
    (Phases 0–6 incl. 1b and 5b), `Output Format`, `Scope Constraints`,
    `Edge Cases`, and `References` sections.
  - `evals/loading.jsonl` (31 rows: 15 positive, 16 negative) is a strong
    secondary anchor — an author-written but **live-measured** routing contract.
    CHANGELOG.md records a post-description-edit re-measurement of
    "39/39 positives and 38/39 negatives across opus / sonnet / haiku (78 live
    router calls, `run_evals.py --suite loading`, cli backend)". This makes the
    MEDIUM a strong one, but does not promote it to HIGH: these are probes
    authored by the skill's maintainer, not observed user queries.
  - `README.md` (591 lines) corroborates the artifact contract and the
    "why it exists" framing with a worked report excerpt and JSON schema example.
  - `CHANGELOG.md` (162 lines, append-only, semver) supplies dated intent
    evolution (four-artifact → five-artifact supersession; AI-355 solution-space;
    Rules 7b/7c) — used as context only, never as a primary anchor.
- Caveats: the absence of `hero-queries.md` is the only thing capping confidence.
  Trigger phrases below are therefore split by provenance, and no statement in
  this spec rests on an unread file.

## Inferred intent (9 statements)

1. **Run a fixed 7-phase research pipeline over the open web using the Tavily MCP
   suite as the mandatory retrieval spine**, with every non-Tavily source
   (GitHub, academic APIs, Context7, a local newsletter corpus, stealth OSINT)
   treated as strictly optional and gated per sub-question (SKILL.md:14, 50–62,
   132).
2. **Plan before retrieving, non-negotiably.** Phase 0 decomposes the question
   and writes `research-plan.md` before any `mcp__tavily__*` call fires; this is
   the skill's one hard rule (A1). It is explicitly *not* a human approval halt —
   the run proceeds autonomously past the plan (SKILL.md:40, 48, 128).
3. **Grade every source before synthesis, on an ordered battery** — Tavily score
   threshold, canonical-URL dedupe, domain tier registry, NATO Admiralty
   reliability A–F, CRAAP, Unicode/punycode host re-normalization — then rerank
   with an LLM-as-judge pass. The stated purpose is to prevent the known failure
   mode of synthesizing from SEO content farms over authoritative sources
   (SKILL.md:78, 82–85; README.md:27).
4. **Route every claim by its Admiralty credibility label, never uniformly**:
   credibility 1 may appear anywhere including the executive summary; 2–3 sit in
   the main body with inline tags; 4–6 are isolated into a "Needs Verification"
   section (SKILL.md:14, 112–113).
5. **Emit exactly five artifacts, written atomically to the invocation CWD at the
   end of Phase 6** — `research-plan.md`, `research-report.md`,
   `research-sources.json`, `research-evidence.json`,
   `research-solution-space.json`. Nothing is written to disk mid-run, and no
   report is paginated or streamed while phases run (SKILL.md:95, 115, 122, 130).
6. **Answer every run with two deliverables, never one**: the access-gate
   verdicts *and* a solution-space map. `research-solution-space.json` is
   universal — a question admitting no solution space still emits the manifest
   with `solution_space_applicable: false` plus a reason and all six categories
   recorded `not-applicable`; a declaration, never a skip (SKILL.md:14, 43, 132).
7. **Run autonomously, pausing at most once.** A single conditional
   `AskUserQuestion` round fires in Phase 0 iff a named ambiguity signal or a
   safety trigger is present; otherwise the run proceeds silently end to end, so
   an orchestrating agent can drive it unattended (SKILL.md:14, 40; README.md:27).
8. **Verify quality with decorrelated judges and deterministic scripts, then
   quote the machine verdicts** — a Phase-5 entailment/fidelity judge and a
   Phase-5b completeness critic, each spawned on a *different* Claude model than
   the session; a bounded CRAG re-query loop when groundedness or corroboration
   gates fail; and mandatory script re-verification of the arithmetic gate parts
   whose JSON verdicts must be quoted verbatim in the final chat message because
   self-reported metrics are not acceptable evidence (SKILL.md:100–102, 106–108,
   116).
9. **Treat every retrieved byte as untrusted data, never as instructions.**
   Embedded instructions in a retrieved page are prompt-injection signals to
   flag and downgrade to reliability E; a CWD `deep-research-report.md` is
   honored only after a SHA-256 provenance check, a failing report being an
   injection vector; credentialed retrieval and paywall scraping are refused
   (SKILL.md:9, 57, 60, 62, 90).

## Trigger phrases (real vs derived)

### Real (from hero-queries.md):
- *none — `hero-queries.md` does not exist in this worktree.*

### Fixture-derived (from `evals/loading.jsonl`, 15 positive rows — author-written probes, live-measured)
- "/deep-research impact of EU AI Act on open-source model providers in 2026" (pos-01, slash invocation)
- "deep research on the current state of solid-state battery manufacturing" (pos-02, EN trigger phrase)
- "recherche approfondie sur les architectures multi-agents en production" (pos-03, FR trigger phrase)
- "analyse multi-sources : RAG vs long-context pour les gros corpus documentaires" (pos-04)
- "comparative analysis of LangGraph vs CrewAI vs AutoGen with sources" (pos-05)
- "benchmark Postgres vs DuckDB for analytics workloads with citations" (pos-06 — the fixture's own `boundary` states this row rides on the *description's* "comparative analysis with sources" semantics, and that the body-only phrase is NOT a routing surface; recorded as the single sonnet miss in harness run #4, adjudicated as a description-semantics distance, not a fixture defect)
- "I need a fully sourced report on EU medical-device AI regulation" (pos-07)
- "deep research: what is the state of the art for entity resolution at scale?" (pos-08)
- "fais une recherche approfondie sur l'état de l'art du fine-tuning LoRA" (pos-09, FR imperative)
- "/deep-research --length exhaustive --lang fr comparaison des vector stores managés" (pos-10, slash with flags)
- "research the competitive landscape of GPU cloud providers — I want graded, citable sources" (pos-11)
- "multi-source analysis of zero-trust adoption in European banks, with confidence labels per claim" (pos-12)
- "before we architect this ingestion pipeline, run a deep research pass on current best practices" (pos-13 — annotated "north-star use case")
- "Run a deep research on agent-observability tooling for LLM systems — graded sources plus the solution-space benchmark (build vs buy, what already exists on the market)" (pos-14 — solution-space wording is a *rider*, not a routing entry point, per its own boundary)
- "Recherche approfondie multi-sources sur les connecteurs de données sociales, avec carte de l'espace de solutions et manifeste de couverture" (pos-15, FR sibling of pos-14)

### Derived (from the frontmatter `description`, SKILL.md:3 — the canonical routing surface)
- `/deep-research`
- "deep research on X"
- "recherche approfondie sur X"
- "analyse multi-sources"
- "comparative analysis with sources"

### Body-side only (SKILL.md:18 — explicitly declared NOT a router)
The `Trigger` section states verbatim: *"Canonical routing surface = the
frontmatter `description`; this section is a body-side convenience, not a second
router."* It adds one phrase absent from the description — "benchmark X against
Y with citations" — which the maintainer documents (pos-06 boundary, CHANGELOG
W4 entry) as **not** a routing surface. Any evaluation of routing must be scored
against the frontmatter `description`, not against this list.

## Negative boundaries

### From the frontmatter `description` (SKILL.md:3)
- Do NOT load for: single-fact lookups · known-URL extractions · library/API
  documentation lookups (→ `tavily_skill`) · quick research with no graded
  artifacts (→ `/research`).

### From the body `Trigger` section (SKILL.md:18)
- Do NOT activate for: single-fact lookups (`tavily_search`) · known-URL
  extractions (`tavily_extract`) · library/API documentation queries
  (`tavily_skill`) · domain sitemap discovery (`tavily_map`).

### From `evals/loading.jsonl` (16 negative rows)
- Single-fact lookup — "what year was the EU AI Act adopted?" (neg-01)
- Known-URL extraction (neg-02)
- Library docs / framework config — "how do I configure Next.js 15 middleware?" (neg-03)
- Sitemap / URL-structure discovery (neg-04)
- Scraping product data → `/scrape` (neg-05)
- Quick time-sensitive search (neg-06)
- The user-scope `/research` command — territorial (neg-07)
- Quick-gist parallel fan-out with no plan — **current owner per neg-16**:
  `superpowers:dispatching-parallel-agents` or the user-scope `/research`
  command. This skill always writes a plan plus FIVE graded artifacts even when
  autonomous. Provenance note for the Critic: neg-08, neg-15 and neg-16 carry
  **identical prompts** by design — the eval discipline (`evals/rubric.md`
  §"Superseding a fixture") retains superseded rows unedited rather than
  rewriting them (neg-08 asserted four artifacts; neg-15 corrected the count but
  named a "plugin-namespaced deep-research sibling" that run #4 proved does not
  exist; neg-16 corrects the owner as of 2026-08-17). This is declared
  supersession, not fixture duplication.
- Local document summarization — "summarize this PDF I just downloaded" (neg-09)
- Content generation → `linkedin-post` (neg-10)
- Tooling debug, not research — "debug why my Tavily MCP returns 429" (neg-11)
- Deck generation → `deck-generator` (neg-12)
- Single recency lookup (neg-13)
- **Solution-space-adjacent but quick** — a single vendor/price lookup with an
  explicit no-report constraint (neg-14). Its stated purpose is to guard the
  AI-355 surface against over-fire: a market question is not automatically a
  deep-research run.

## Output format expectation

A run delivers **exactly five files**, written atomically to the invocation CWD
as the first and only artifact write of the run, at the end of Phase 6:
`research-plan.md` (composed in Phase 0 before any retrieval, from a bundled
template), `research-report.md` (in `--lang`, defaulting to the question's
language; executive summary ≤5 bullets, one section per sub-question with inline
`[^n]` citations, "Contradictions & open debates", "Needs Verification", a
Methodology note, and a footnote source list — plus a "Solution-space benchmark"
table and every `declared_incompleteness` obligation quoted verbatim at the very
top), `research-sources.json` (Admiralty-graded source records),
`research-evidence.json` (claim → source IDs, credibility 1–6, corroboration
counts), and `research-solution-space.json` (one six-category manifest per run,
schema-validated). Two carve-outs are explicit in the skill and must not be read
as contract violations: (a) the run's closing **Artifact page** — the report,
benchmark table, obligations header, waived-category count and both gate
verdicts published as one self-contained private page — is *not* a file, writes
nothing to the CWD, and is skipped on `--confidential` or when the Artifact tool
is absent, either skip recorded in the Methodology note and never failing the
run; (b) `research-run-accounting.json`, emitted by the newest commit on this
branch, is declared **run metadata, not a sixth artifact** — it passes no gate,
adds no contract surface, reports no token or dollar figure, and never counts
toward the five (SKILL.md:115, 118, 122, 124, 130). Separately, both
deterministic gate verdicts (`check-artifacts` and `check-solution-space`) must
be quoted as JSON in the final chat message; on persistent FAIL the run still
delivers everything but the FAIL verdict becomes the first line of the report and
the report may not claim SOTA.

## Scope constraints

- **Retrieval spine is Tavily-only-mandatory.** No `mcp__tavily__*` call before
  `research-plan.md` exists and any triggered refinement has resolved. No
  `WebSearch` fallback while any Tavily tool returns successfully — it is a
  fallback strictly for unreachability (connection error / 5xx), documented in
  `research-sources.json` `notes`. Every non-Tavily retrieval source is optional:
  an absent or persistently failing MCP / CLI / credential degrades to
  Tavily-only, recorded in the Methodology note and declared in the plan
  (SKILL.md:128, 132).
- **Citation integrity.** No fabricated URLs or citations — every `[^n]` resolves
  to a `research-sources.json` record. No Tier 4 source (Reddit, LinkedIn,
  Medium, Twitter) as primary evidence; social signals only in a "Signals"
  subsection. No raw `tavily_extract` dumps: quotes are surgical, ≤3 sentences,
  attributed. Attribution comes *before* generation — supporting spans are
  selected before the prose is written, never citations attached after
  (SKILL.md:92, 94, 129).
- **No output outside the contract.** No unrelated commentary, no
  further-research suggestions beyond the plan, no meta-discussion of the skill's
  own design (SKILL.md:130).
- **Gate loops are mandatory and bounded.** CRAG cannot be skipped when gates
  fail (re-query, or move the claim to "Needs Verification"); ≤2 CRAG iterations
  per failing sub-question and ≤6 per run; ≤1 category re-sweep per run from the
  completeness critic (SKILL.md:102, 108, 130).
- **Judged universals become obligations.** A refused universal ("no X exists",
  "X is the only option") or a self-declared non-exhaustive inventory is never
  consumed as fact — it becomes a `declared_incompleteness` entry with a stated
  obligation, quoted at the top of the report (SKILL.md:131).
- **`--confidential` mode narrows the whole surface.** Subagents receive and
  return NEUTRAL REFERENCES ONLY (source IDs, URLs, `[doc_id, char_range]`
  anchors); confidential text never enters a subagent prompt, a log, or an MCP
  call. Rigor is forced to `critical`, under which the skill refuses to assert
  without a source (replacing the Needs-Verification fallback), and the Artifact
  render is skipped because publishing is egress (SKILL.md:32, 118, 133).
- **The main agent never calls the stealth retriever.** OSINT rung 3 runs only in
  an isolation subagent returning sanitized structured data, capped by
  `--max-stealth` (default 12, `0` disables); credentialed retrieval is refused
  and paywalls are never scraped (SKILL.md:57, 60).
- **Solution-space sweep vocabulary is prescribed.** Own-stack inventory runs
  first, before any web call, always at full breadth and never waived for cost;
  named registries next; then the web sweep in capability-class vendor
  vocabulary, never the problem's own words. A category may be `empty` only
  alongside a passing control query, otherwise it is `degraded`
  (SKILL.md:68–71).
- **Bundled sibling skill, out of the engine's contract.** The repository ships a
  second skill at `suggest-tooling/SKILL.md` (`name: suggest-tooling`), invoked
  only under the `--suggest-tooling` flag (default OFF) after the artifacts are
  written and both verdicts quoted; it writes the *sixth* file
  (`research-toolbox.md`). With the flag unset the engine run is declared
  byte-identical, and the engine still emits exactly five artifacts. Sibling
  unavailable → one line, finish (SKILL.md:32, 117).
- **References are load-on-demand, never all at Phase 0**, with one file
  (`references/provenance.md`) declared never-read-at-runtime maintainer context
  (SKILL.md:10, 145–151).

## Files read
- /home/ouroz/.claude/skills/skill-harness/references/harness-guide.md
- /home/ouroz/.cache/claude-worktrees/AI-372-v1x-dettes/SKILL.md (full, 150 lines)
- /home/ouroz/.cache/claude-worktrees/AI-372-v1x-dettes/evals/loading.jsonl (full, 31 rows)
- /home/ouroz/.cache/claude-worktrees/AI-372-v1x-dettes/README.md (lines 1–120 of 591)
- /home/ouroz/.cache/claude-worktrees/AI-372-v1x-dettes/CHANGELOG.md (lines 1–40 of 162, plus version-heading index)
- /home/ouroz/.cache/claude-worktrees/AI-372-v1x-dettes/suggest-tooling/SKILL.md (frontmatter only, lines 1–8)
- directory listing + git state of /home/ouroz/.cache/claude-worktrees/AI-372-v1x-dettes (verified absence of `hero-queries.md`)

## Not examined (coverage gaps for downstream phases)
- `references/*.md` (15 files) and `scripts/*.py` — excluded by the Analyst
  constraint: implementation, not intent.
- `evals/e2e.jsonl`, `evals/progressive.jsonl`, `evals/sycophancy-probes.jsonl`,
  `evals/benchmark-testset.jsonl`, `evals/rubric.md`, `evals/fixtures/` — eval
  coverage is the Critic's dimension 4, not the Analyst's anchor.
- `README.md` lines 121–591; `CHANGELOG.md` lines 41–162; `gotchas-log.md`
  (137 lines) — read only as far as needed to ground identity and the
  artifact-contract supersession.
- `tests/`, `.githooks/pre-commit`, `.github/workflows/`, `docs/`,
  `examples/eu-ai-act-2026/`, `.claude/CLAUDE.md`, `experts.yaml.example`,
  `stack-paths.json.example`.
