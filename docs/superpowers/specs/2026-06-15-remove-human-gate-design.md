# Design — Replace the mandatory human gate with structured pre-flight refinement

**Date:** 2026-06-15
**Status:** Approved (design); pending implementation plan
**Scope:** `deep-research` skill — Phase 0 behavioral contract

## Problem

The skill halts after Phase 0 for mandatory human approval of `research-plan.md` before
any Tavily call fires. This blocks use by fully autonomous agents and adds friction on
unambiguous queries where there is nothing to steer. The gate is a documented
non-negotiable wired through ~24 locations across 7 files plus evals.

## Decision

Remove the mandatory approval halt. Replace it with a **structured pre-flight refinement**
step that fires `AskUserQuestion` **only** when the query is ambiguous (per a named-signal
checklist) or when a folded safety trigger fires. Clear queries proceed autonomously with
no human checkpoint. `research-plan.md` is still produced (artifact #1 of the four-artifact
contract); only the *halt* is deleted.

This re-anchors the skill's identity from "the human-gated pipeline" to "the only research
entry point that emits four NATO-graded, `verify_gates.py`-verified artifacts — now
autonomous-capable." It converges this skill's interaction model toward the plugin-namespaced
`deep-research` sibling (which already clarifies-if-underspecified) while keeping the graded
four-artifact contract neither sibling has.

### Sibling landscape (positioning context)

| Entry point | Artifacts | Grading | Pre-flight clarify? |
|---|---|---|---|
| `/research` (user cmd) | none | none | no |
| plugin `deep-research` ("harness") | none/ad-hoc | none | yes (already) |
| **this** skill (user `deep-research`) | **4 NATO-graded, script-verified** | Admiralty A–F×1–6 | **new: yes, conditional** |

## Behavioral contract

Phase 0 splits; the halt is deleted:

- **Phase 0a — Pre-flight refinement.** Parse query + flags. Run the ambiguity-signal
  checklist. If ≥1 signal fires OR a folded safety trigger fires, call `AskUserQuestion`
  once and weave answers into the query. If nothing fires, proceed silently.
- **Phase 0b — Query Architect.** Decompose, classify, write `research-plan.md`
  (unchanged artifact #1; `verify_gates.py check-artifacts` unaffected).
- **→ Phase 1 directly. No approval halt.**

### Autonomous-mode contract (load-bearing property)

The only thing that can block an unattended run is genuine ambiguity. A well-formed query
from an orchestrator triggers zero signals → zero blocks → fully autonomous. An ambiguous
query surfaces `AskUserQuestion`, which correctly stalls a headless run — researching an
ambiguous question unattended is the worse failure. **No escape hatch** (user-approved):
"provide a well-formed query for fully unattended runs" is the documented contract. The
structured checklist (not LLM vibes) is what makes "clear → silent" reliable.

## Ambiguity-signal checklist (authoritative in `methodology.md`)

Fire `AskUserQuestion` iff ≥1 named signal is present:

1. **No scope boundary** — subject extent unbounded.
2. **Undefined comparison axis** — a compare/vs intent with no stated dimensions.
3. **Ambiguous timeframe** — time-sensitive topic, no date range.
4. **Unspecified depth** — query breadth mismatches the `--length` default.
5. **Undefined audience/jurisdiction** — legal/regulatory/regional topic, no locale.

## Folded safety triggers

The `AskUserQuestion` dialog also opens (even on a clear query) when:

- a `--domains` entry is **below Tier 2** → confirm inclusion (was `README.md:450`);
- `--rigor critical` presupposition probe finds an **unsupported premise** → proceed /
  reframe / cancel (was `SKILL.md:74`, `quality-gate.md:15`);
- **budget** (exhaustive ~120 calls) → **log-and-proceed**, no prompt.

**Open implementation detail (resolve in writing-plans):** the critical-rigor premise probe
may need a lightweight pre-Phase-1 verification retrieval to have something to surface.
Decide exact sequencing in the plan, not here.

## Cross-file propagation (~24 edits)

- **SKILL.md**: `:3` description re-anchor + sibling routing · `:24` overview · new Phase 0a +
  rewrite `:86` step 7 · `:74`/`:193`/`:201` "at the human gate" → refinement · "approved
  plan" → "the plan" at `:90,94–97,168,179`.
- **references/anti-patterns.md**: rewrite **A1** → "No Tavily call before `research-plan.md`
  is written and any triggered refinement is resolved" · `:62,73`.
- **references/methodology.md**: rewrite `:337` gate paragraph + **add the signal checklist**
  (single source of phase vocab, invariant I3) · `:282,292,365` "at the human gate".
- **references/quality-gate.md** `:15` · **references/research-plan-template.md** `:3,106`
  (drop "approve to proceed").
- **.claude/CLAUDE.md** (project memory) `:7,82` — rewrite the "non-negotiable human approval
  gate" line.
- **README.md**: tagline `:6` · "why exist" `:27` · **mermaid `:181`** (HUMAN GATE node →
  conditional refinement diamond) · **"The Human Gate" section + badge `:250–256`** →
  "Pre-flight Refinement" · `:36,359,450,481`.
- **gotchas-log.md**: add a maintainer note that the gate was removed **intentionally**
  (prevent a future audit from "restoring" it as a regression).
- **CHANGELOG.md**: new entry — **minor bump + prominent BEHAVIOR-CHANGE callout**
  (user-approved).

## Evals

- `loading.jsonl` / `rubric.md` / `e2e.jsonl` — drop any assertion scoring "halts at the
  gate"; **add** two fixtures: (a) clear query → no `AskUserQuestion`; (b) ambiguous query →
  `AskUserQuestion` fires citing the right signal.
- `sycophancy-probes.jsonl` — false-premise probes expect surfacing via the refinement
  question, not the gate.

## Explicitly untouched (invariants held)

- `deep-research-report.md` — no edit → **I1** SHA-256 hash holds (gate is not in the report).
- `references/methodology.md §9` `[R§9]` anchor — points to the phase list (unchanged) → **I2**.
- `scripts/verify_gates.py` — plan still artifact #1 → `check-artifacts` valid.
- `tests/check-provenance.sh`, `scripts/*` ranking, the four-artifact contract.

## Semver

Minor bump + loud BEHAVIOR-CHANGE note (skill is pre-1.0; user-approved). Confirm exact
version in the plan.
