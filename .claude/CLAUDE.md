# CLAUDE.md — deep-research skill

> Primary spec anchor for maintainers. Consumers of the skill (Claude Code users invoking `/deep-research`) should read `SKILL.md`. This file is the authoritative project memory for anyone **modifying** the repo.

## Project identity

`deep-research` is a markdown-only Claude Code skill packaged as a GitHub repository. It orchestrates a 7-phase agentic deep-research pipeline over the Tavily MCP tool suite, calibrated to Perplexity Deep Research output (≥100 cited sources on `--length exhaustive`). The skill produces four artifacts in the invocation CWD: `research-plan.md`, `research-report.md`, `research-sources.json`, `research-evidence.json`. Sources are graded on the NATO Admiralty A–F × 1–6 matrix against a 4-tier domain registry. A non-negotiable **human approval gate** sits between Phase 0 (planning) and Phase 1 (retrieval) — no Tavily call fires before the user approves `research-plan.md`.

The repo ships no executable code. Every deliverable is either documentation, a reference file, a JSON Schema, a bash test script, or a GitHub Actions workflow.

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
| `tests/check-cross-references.sh` | Walks markdown links + `[R§n]` back-refs, exits non-zero on miss | Link integrity |
| `tests/check-provenance.sh` | Re-computes SHA-256 of `deep-research-report.md` vs SKILL.md line 8 | Provenance invariant |
| `tests/check-schema.sh` | Validates JSON artifacts against `tests/schema/*.schema.json` via `npx ajv-cli` | Artifact conformance |
| `tests/schema/research-sources.schema.json` | JSON Schema for source records (draft-07) | Sources artifact shape |
| `tests/schema/research-evidence.schema.json` | JSON Schema for claim records (draft-07) | Evidence artifact shape |
| `tests/fixtures/` | Symlinks to `examples/eu-ai-act-2026/*.json` consumed by check-schema | CI inputs |
| `examples/eu-ai-act-2026/` | End-to-end mock run of the README example query | Illustrative reference |
| `.github/workflows/validate.yml` | GitHub Actions — runs all three check scripts on push + PR | CI |
| `README.md` | External-facing entry point | Install / Quick Start / Roadmap |

## Maintainer gotchas (invariants — do not violate)

### I1. SHA-256 provenance

The hash prefix declared on `SKILL.md` line 8 (`cb2fe20dced3c4bb…`) **must match** the actual SHA-256 of `deep-research-report.md`. After any edit to the report, re-compute and update the line 8 prefix **in the same commit**:

```bash
sha256sum deep-research-report.md
# then update SKILL.md line 8 with the new full/prefix hash
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

### I4. No executable code in the skill payload

This skill produces markdown artifacts via LLM reasoning over Tavily MCP results. Do not add Python, Node, or other executable code to the skill surface (`SKILL.md`, `references/`). Test scripts under `tests/` are the only bash/JS allowed, and only for CI validation — never invoked by the skill itself at runtime.

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
   ```

5. Commit message: `<type>(<scope>): <short summary>`. Reference the harness finding ID (e.g., `fix(D3): …`) if the edit closes a harness review item.

## Style conventions

- **Markdown only** in skill-surface files. No embedded HTML beyond what's already in README badges/mermaid.
- **Surgical quotes** (≤3 sentences) when citing report or external material in any skill-surface file. Never paste raw tool output.
- **No emoji** in `SKILL.md`, `references/*`, or produced artifacts. README status badges are the exception.
- **Deterministic rules over hedging.** Thresholds are numbers, not adjectives.
- **Absolute paths in tool routing / scripts; relative paths in markdown cross-references.**
- **Line-level stability.** SKILL.md line 8 (SHA-256 prefix) and `references/methodology.md §9` heading numbers are referenced by tests and cited in issue tracking — do not reorder sections casually.
