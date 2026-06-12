# CLAUDE.md — deep-research skill

> Primary spec anchor for maintainers. Consumers of the skill (Claude Code users invoking `/deep-research`) should read `SKILL.md`. This file is the authoritative project memory for anyone **modifying** the repo.

## Project identity

`deep-research` is a markdown-only Claude Code skill packaged as a GitHub repository. It orchestrates a 7-phase agentic deep-research pipeline over the Tavily MCP tool suite, calibrated to Perplexity Deep Research output (≥100 cited sources on `--length exhaustive`). The skill produces four artifacts in the invocation CWD: `research-plan.md`, `research-report.md`, `research-sources.json`, `research-evidence.json`. Sources are graded on the NATO Admiralty A–F × 1–6 matrix against a 4-tier domain registry. A non-negotiable **human approval gate** sits between Phase 0 (planning) and Phase 1 (retrieval) — no Tavily call fires before the user approves `research-plan.md`.

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
| `references/research-plan-template.md` | Phase 0 plan scaffold | Approval artifact shape |
| `references/examples.md` | Worked examples moved out of SKILL.md (token budget) | Illustrative plan/report excerpts |
| `evals/` | Loading (≥12+12 incl. territorial negatives), progressive (≥8), e2e (≥3) fixtures + `rubric.md` | Activation + disclosure + mechanical e2e checks |
| `CHANGELOG.md` | Semver release history, append-only | Release notes, waivers |
| `gotchas-log.md` | Maintainer traps (trigger/gotcha/resolution/guard) + perishable-asset maintenance cadences | Operational memory |
| `scripts/verify_gates.py` | Deterministic gate verification (stdlib-only, zero network): artifact counts/ratios/medians, §4.1 cascade conformance, punycode, CWD-report hash, `--rigor critical` anchors | Runtime quality gates (Phase 0 hash check, Phase 6 artifact check) |
| `scripts/github_rank.py` | Composite GitHub-repo ranking (scoring only, zero network — retrieval via `gh` CLI upstream) | GitHub deep-research ranking + fake-star gate |
| `references/github-research.md` | GitHub SOTA-repo discovery pipeline (sharding, expert prior, ecosyste.ms, measurement protocol) | Conditional GitHub source |
| `references/academic-research.md` | Scholarly pipeline (OpenAlex ‖ arXiv → S2 → expansion → legal-OA), dual-track ranking, Exa/Valyu decision | Conditional academic source |
| `scripts/academic_graph.py` | Dual-track paper ranking + BibTeX/RIS export (scoring only, zero network) | Academic reading-list ranking |
| `scripts/eval_harness/` | Five-layer verification harness: layer-1 = verify_gates.py; versioned judge prompts (entailment/adversarial/completeness); `run_ci_judges.sh` (maintainer-secret-gated, skips gracefully) | AI-124 permanent verification; per-run vs CI mapping per rigor profile |
| `evals/sycophancy-probes.jsonl` + `evals/benchmark-testset.jsonl` | Versioned false-premise probes + frozen Perplexity-benchmark questions (4-weekly cadence) | Harness layers 5 + benchmark |
| `references/model-tiers.md` | Model-tier policy + subagent override mechanics (D-4) | Tier selection |
| `tests/check-cross-references.sh` | Walks markdown links + `[R§n]`/`[R§n.m]` back-refs (methodology, anti-patterns, SKILL.md prose), exits non-zero on miss | Link integrity |
| `tests/check-example-invariants.sh` | jq cross-file validation of the example sources/evidence pair (IDs, cascade, routing, counts) | Example conformance to the skill's own gates |
| `tests/check-provenance.sh` | Re-computes SHA-256 of `deep-research-report.md` vs the `Hash at generation time:` line in SKILL.md | Provenance invariant |
| `tests/check-schema.sh` | Validates JSON artifacts against `tests/schema/*.schema.json` via `npx ajv-cli` | Artifact conformance |
| `tests/schema/research-sources.schema.json` | JSON Schema for source records (draft-07) | Sources artifact shape |
| `tests/schema/research-evidence.schema.json` | JSON Schema for claim records (draft-07) | Evidence artifact shape |
| `tests/fixtures/` | Symlinks to `examples/eu-ai-act-2026/*.json` consumed by check-schema | CI inputs |
| `examples/eu-ai-act-2026/` | End-to-end mock run of the README example query | Illustrative reference |
| `.github/workflows/validate.yml` | GitHub Actions — runs all three check scripts on push + PR | CI |
| `README.md` | External-facing entry point | Install / Quick Start / Roadmap |

## Maintainer gotchas (invariants — do not violate)

### I1. SHA-256 provenance

The hash prefix declared on the `Hash at generation time:` line of `SKILL.md` §Provenance (`cb2fe20dced3c4bb…`) **must match** the actual SHA-256 of `deep-research-report.md`. After any edit to the report, re-compute and update the prefix **in the same commit**:

```bash
sha256sum deep-research-report.md
# then update the 'Hash at generation time:' line in SKILL.md with the new prefix
```

Guarded by `tests/check-provenance.sh`. A failing provenance check blocks the CI workflow.

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

(Phase 0 is the human-gated planning phase; Phases 1–6 run post-approval.)

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
