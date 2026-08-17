# CLAUDE.md — deep-research skill

> Primary spec anchor for maintainers. Consumers of the skill (Claude Code users invoking `/deep-research`) should read `SKILL.md`. This file is the authoritative project memory for anyone **modifying** the repo.

## Project identity

`deep-research` is a markdown-only Claude Code skill packaged as a GitHub repository. It orchestrates a 7-phase agentic deep-research pipeline over the Tavily MCP tool suite, calibrated to Perplexity Deep Research output (≥100 cited sources on `--length exhaustive`). The skill produces five artifacts in the invocation CWD: `research-plan.md`, `research-report.md`, `research-sources.json`, `research-evidence.json`, `research-solution-space.json` (the solution-space manifest, artifact #5, AI-355). Sources are graded on the NATO Admiralty A–F × 1–6 matrix against a 4-tier domain registry. Phase 0 (planning) writes `research-plan.md` and proceeds **autonomously** to Phase 1 (retrieval) — there is no mandatory human approval halt. A **conditional pre-flight refinement** sits at Phase 0 step 3: a single `AskUserQuestion` round fires only when a named ambiguity signal or a safety trigger trips (`references/methodology.md` §9, the authoritative checklist). The one hard invariant remains: no Tavily call before `research-plan.md` is written and any triggered refinement has resolved (`references/anti-patterns.md` A1).

The skill-surface (`SKILL.md`, `references/`) is markdown-only. Deterministic helpers live under `scripts/` and are invocable at runtime via Bash (amendment I4a, 2026-06-12): `scripts/verify_gates.py` computes counts, ratios, medians, cascade conformance, punycode normalization, and the CWD-report SHA-256 check — quality gates are script-verified, never LLM-self-reported. Everything else is documentation, a reference file, a JSON Schema, a bash test script, or a GitHub Actions workflow.

## Architecture map

| Path | Purpose | Authoritative for |
|---|---|---|
| `SKILL.md` | Skill entry point — YAML frontmatter + 7-phase workflow + examples | Trigger, inputs, flags, edge cases |
| `deep-research-report.md` | Standalone intelligence brief on SOTA web-search techniques for AI agents | Methodology source of truth (SHA-256 guarded) |
| `references/methodology.md` | Near-verbatim distillation of the report with `[R§n]` back-refs | **Single source of phase vocabulary** (§9) |
| `references/tool-routing.md` | Tavily MCP tool selection per intent | Phase 1 / Phase 4 call templates |
| `references/report-structure.md` | Output structure + JSON schemas for `research-sources.json` and `research-evidence.json` | Artifact schemas |
| `references/quality-gate.md` | Deterministic thresholds + CRAG trigger rules | Phase 5 gates, confidence-tag assignment |
| `references/anti-patterns.md` | Forbidden behaviors (skill non-negotiables + report anti-patterns) | Guardrails |
| `references/research-plan-template.md` | Phase 0 plan scaffold | Plan artifact shape |
| `references/examples.md` | Worked examples moved out of SKILL.md (token budget) | Illustrative plan/report excerpts |
| `references/solution-space.md` | Solution-space doctrine: the closed set of 6 categories, status + capability-class vocabularies, sweep order, completeness-critic contract, `check-solution-space` rules | Artifact #5 (AI-355). Read at Phase 0 **only when the geometry is applicable**; SKILL.md step 5 carries the minimal NA contract |
| `references/flags.md` | Full semantics of every flag (moved out of SKILL.md 2026-08-04, D3 load-tier remediation) | Flag effects |
| `references/edge-cases.md` | Full handling of the 13 edge cases (moved out of SKILL.md 2026-08-04, D3) — SKILL.md keeps the trigger→verdict index | Edge-case reasoning |
| `references/provenance.md` | Scaffold deviations + interim defaults (moved out of SKILL.md 2026-08-04, D3). The hash-check and report-wins rules stay in SKILL.md — they are runtime defenses | Maintainer audit trail |
| `scripts/stack_inventory.py` | Own-stack grep over the paths in `~/.claude/deep-research/stack-paths.json` (stdlib, zero network); absent config → `degraded`, never silent `empty` | Phase-1b own-stack category |
| `tests/check-solution-space.sh` | Drives `verify_gates.py check-solution-space` over `tests/fixtures/solution-space/` (valid + 14 single-mutation violations + 1 positive control for Rule 7c) and replays `stack_inventory.py` against a synthetic corpus | Solution-space gate conformance (CI) |
| `evals/` | Loading (≥12+12 incl. territorial negatives), progressive (bar = the fixture count, currently 13/13), e2e (≥3) fixtures + `rubric.md` | Activation + disclosure + mechanical e2e checks |
| `CHANGELOG.md` | Semver release history, append-only | Release notes, waivers |
| `gotchas-log.md` | Maintainer traps (trigger/gotcha/resolution/guard) + perishable-asset maintenance cadences | Operational memory |
| `scripts/verify_gates.py` | Deterministic gate verification (stdlib-only, zero network): artifact counts/ratios/medians, §4.1 cascade conformance, punycode, CWD-report hash, `--rigor critical` anchors; OSINT gates: social-domain tier-map validation, `--max-stealth` cap enforcement, `retrieval_status` field check, B13 anti-amplification masquerade detection | Runtime quality gates (Phase 0 hash check, Phase 6 artifact check, OSINT checks) |
| `scripts/github_rank.py` | Composite GitHub-repo ranking (scoring only, zero network — retrieval via `gh` CLI upstream) | GitHub deep-research ranking + fake-star gate |
| `references/github-research.md` | GitHub SOTA-repo discovery pipeline (sharding, expert prior, ecosyste.ms, measurement protocol) | Conditional GitHub source |
| `references/academic-research.md` | Scholarly pipeline (OpenAlex ‖ arXiv → S2 → expansion → legal-OA), dual-track ranking, Exa/Valyu decision | Conditional academic source |
| `scripts/academic_graph.py` | Dual-track paper ranking + BibTeX/RIS export (scoring only, zero network) | Academic reading-list ranking |
| `references/newsletter-signal.md` | Curated-feed routing source: corpus location/shape, FTS5 search invocation, routing-signal (never-cited) grading, confidential posture, degradation | Conditional newsletter source |
| `scripts/newsletter_search.py` | Newsletter-corpus search — in-memory FTS5 (bm25 + recency) with pure-Python fallback, derives reference date from data; stdlib, zero network | Newsletter-signal retrieval |
| `references/osint-retrieval.md` | OSINT/SOCMINT stealth escalation contract: 3-rung ladder, isolation-subagent output schema, account-reliability mapping, GDPR persistence posture | Conditional OSINT/SOCMINT source |
| `tests/check-osint-gates.sh` | Drives `verify_gates.py` over OSINT fixtures; asserts tier-map, stealth-cap, retrieval-status, and B13 anti-amplification gates fire and clear as designed | OSINT gate conformance (CI-only) |
| `scripts/eval_harness/` | Five-layer verification harness: layer-1 = verify_gates.py; versioned judge prompts (entailment/adversarial/completeness); `run_ci_judges.sh` (maintainer-secret-gated, skips gracefully) | AI-124 permanent verification; per-run vs CI mapping per rigor profile |
| `evals/sycophancy-probes.jsonl` + `evals/benchmark-testset.jsonl` | Versioned false-premise probes + frozen Perplexity-benchmark questions (4-weekly cadence) | Harness layers 5 + benchmark |
| `references/model-tiers.md` | Model-tier policy + subagent override mechanics (D-4) | Tier selection |
| `tests/check-cross-references.sh` | Walks markdown links + `[R§n]`/`[R§n.m]` back-refs (methodology, anti-patterns, SKILL.md prose), exits non-zero on miss | Link integrity |
| `tests/check-example-invariants.sh` | jq cross-file validation of the example sources/evidence pair (IDs, cascade, routing, counts) | Example conformance to the skill's own gates |
| `tests/check-provenance.sh` | Re-computes SHA-256 of `deep-research-report.md` vs the `Hash at generation time:` line in SKILL.md | Provenance invariant |
| `tests/check-schema.sh` | Validates JSON artifacts against `tests/schema/*.schema.json` via `npx ajv-cli` | Artifact conformance |
| `tests/schema/research-sources.schema.json` | JSON Schema for source records (draft-07) | Sources artifact shape |
| `tests/schema/research-evidence.schema.json` | JSON Schema for claim records (draft-07) | Evidence artifact shape |
| `tests/schema/newsletter-corpus-record.schema.json` + `tests/check-newsletter-search.sh` + `tests/fixtures/newsletter-corpus/` | Corpus-record contract (`additionalProperties:false` enforces redaction) + helper check (ranking, `--since`, `--bucket`, degradation, fallback, per-line schema validation via direct `ajv -s`) + fixture corpus | Newsletter-signal conformance |
| `tests/fixtures/` | Symlinks to `examples/eu-ai-act-2026/*.json` consumed by check-schema | CI inputs |
| `examples/eu-ai-act-2026/` | End-to-end mock run of the README example query | Illustrative reference |
| `.github/workflows/validate.yml` | GitHub Actions — runs every check script on push + PR | CI |
| `.githooks/pre-commit` | Refreshes the SHA-256 provenance prefix in `SKILL.md` from the **staged** report; blocks rather than stage unreviewed edits. Inert until `git config core.hooksPath .githooks` | Invariant I1, author-side |
| `tests/check-precommit-hook.sh` | Drives the hook over a throwaway repo (4 cases: no-op, repair+restage, blocked-on-dirty, missing marker) | Hook conformance (CI) |
| `README.md` | External-facing entry point | Install / Quick Start / Roadmap |

## Maintainer gotchas (invariants — do not violate)

### I1. SHA-256 provenance

The hash prefix declared on the `Hash at generation time:` line of `SKILL.md` §Provenance (`cb2fe20dced3c4bb…`) **must match** the actual SHA-256 of `deep-research-report.md`. After any edit to the report, re-compute and update the prefix **in the same commit**:

```bash
sha256sum deep-research-report.md
# then update the 'Hash at generation time:' line in SKILL.md with the new prefix
```

Guarded by `tests/check-provenance.sh`. A failing provenance check blocks the CI workflow.

**Install the hook once per clone — it does the update for you:**

```bash
git config core.hooksPath .githooks
```

`.githooks/pre-commit` hashes the **staged** report, and when the declared prefix is stale it rewrites the marker line and re-stages `SKILL.md`. If `SKILL.md` carries unstaged edits it repairs the working tree but **blocks the commit** rather than sweeping unreviewed work into it. A hook stays inert until `core.hooksPath` is set, so an uninstalled clone silently loses this defense — `tests/check-provenance.sh` remains the backstop, and `tests/check-precommit-hook.sh` proves the hook itself still works (4 cases, CI).

### I2. `[R§n]` back-reference integrity

Every `[R§n]` / `[R§n.m]` citation in `references/methodology.md` must resolve to a numbered section in `deep-research-report.md`. After any edit to either file, revalidate:

```bash
bash tests/check-cross-references.sh
```

### I3. Methodology wins — single source of phase vocabulary

`references/methodology.md §9` is the single source of truth for phase names. `SKILL.md` overview, `README.md` (badge + prose + mermaid), and `references/quality-gate.md` must conform. When in doubt, rewrite to match §9 — never the other way around. The 7-phase enumeration is:

1. Phase 0 — Query Architect
2. Phase 1 — Broad Retrieval
3. Phase 2 — Source Grading
4. Phase 3 — Precision Rerank
5. Phase 4 — Deep Extract & Synthesis
6. Phase 5 — Grounding Validation
7. Phase 6 — Confidence Annotation

(Phase 0 is the planning phase — pre-flight refinement plus plan authoring; it proceeds autonomously to Phases 1–6 unless the ambiguity-signal checklist fires a clarifying question.)

### I4a. Markdown skill-surface; deterministic helpers under `scripts/` only

Amended 2026-06-12 with explicit user approval (decisions D-3/D-4 of the AI-119 refonte plan). The skill surface (`SKILL.md`, `references/`) stays markdown-only — no embedded executable code. Deterministic helpers live under `scripts/` and ARE invocable by the skill at runtime via Bash, under a strict supply-chain contract:

- **Stdlib-only** (or pinned dependencies with hashes if ever unavoidable — prefer stdlib).
- **Zero network calls.** `scripts/verify_gates.py` must never open a socket; CI lints for this by review and `py_compile`.
- **Zero LLM/SDK calls** (I4b was considered and abandoned by decision D-4: consumers are Claude Code users without API keys; model selection uses Claude Code subagent `model:` overrides, not SDK clients).
- Test scripts under `tests/` remain CI-only — never invoked by the skill at runtime.

### I5. Tier registry changes in one place only

New domains always land in `references/methodology.md §6` first. The README tier table and SKILL.md examples must be updated to match in the same commit, not in a follow-up.

## Extension protocol

User-facing extension points are documented in `README.md` under "Extending". For maintainer-side changes:

1. Identify the single authoritative file (usually `references/methodology.md`).
2. Edit there first.
3. Propagate consequential changes to `SKILL.md` and `README.md` in the **same commit** — do not leave cross-file documentation drift.
4. Run local verification before commit:

   ```bash
   bash tests/check-cross-references.sh
   bash tests/check-provenance.sh
   bash tests/check-schema.sh tests/fixtures/research-sources.json tests/fixtures/research-evidence.json
   bash tests/check-example-invariants.sh
   python3 -m py_compile scripts/verify_gates.py
   python3 scripts/verify_gates.py check-artifacts --sources examples/eu-ai-act-2026/research-sources.json --evidence examples/eu-ai-act-2026/research-evidence.json --length short
   ```

5. Commit message: `<type>(<scope>): <short summary>`. Reference the harness finding ID (e.g., `fix(D3): …`) if the edit closes a harness review item.

## Style conventions

- **Markdown only** in skill-surface files. No embedded HTML beyond what's already in README badges/mermaid.
- **Surgical quotes** (≤3 sentences) when citing report or external material in any skill-surface file. Never paste raw tool output.
- **No emoji** in `SKILL.md`, `references/*`, or produced artifacts. README status badges are the exception.
- **Deterministic rules over hedging.** Thresholds are numbers, not adjectives.
- **Absolute paths in tool routing / scripts; relative paths in markdown cross-references.**
- **Anchor stability.** The `Hash at generation time:` marker line in SKILL.md §Provenance (SHA-256 prefix — marker-anchored since 0.2.0, robust to frontmatter growth) and `references/methodology.md §9` heading numbers are referenced by tests and cited in issue tracking — do not rename or reorder them casually.
