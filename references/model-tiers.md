# Model tiers — session-model guidance and subagent overrides

> Read at Phase 0 when `--model` or `--confidential` is set, or when planning an exhaustive run. Policy decided 2026-06-12 (decisions D-1 and D-4 of the AI-119 refonte): the skill is **Claude-Code-native** — it never calls the Anthropic SDK and requires no API key. Model selection happens through (a) the session model the user picked, and (b) per-subagent `model` overrides on Claude Code's Agent tool. Model facts below verified against the `claude-api` skill, 2026-06-12.

## Tier policy

| Tier | Model | When | Cost (per MTok in/out) |
|---|---|---|---|
| **Default** | `claude-opus-4-8` (session model "opus") | All runs. 1M context, 128K output, ZDR-compatible. | $5 / $25 |
| **Opt-in** | `claude-fable-5` (session model "fable") | The hardest long-horizon synthesis on `--length exhaustive`, when the user explicitly opts in via `--model fable`. Eligible on BOTH paths including `--confidential` (decision D-1: 30-day retention accepted). | $10 / $50 (~2× Opus 4.8) |
| **Subagent worker** | `haiku` / `sonnet` overrides | Cheap parallel work inside the pipeline: per-sub-question Phase-2 grading subagents, mechanical extraction passes. | $1/$5 · $3/$15 |

**Cost note (corrects the original AI-120 estimate):** Fable 5 uses the same tokenizer as Opus 4.8 — token counts are roughly unchanged; the cost multiple vs Opus 4.8 is ~2× (price ratio), not ~2.6×. The "+30% tokens" penalty applies only when comparing against Opus 4.6 or older tokenizers.

## How selection actually works (no SDK, D-4)

1. **Session model** — the lead orchestrator (the model reading this file) runs on whatever the user selected with `/model`. The skill cannot switch it. If `--model fable` is requested but the session runs on another model, say so in `research-plan.md` at the human gate and recommend the user switch (`/model fable`) before approving — never silently proceed as if the tier applied.
2. **Subagent overrides** — Claude Code's Agent tool accepts a per-subagent `model` parameter (`haiku`, `sonnet`, `opus`, `fable`). The pipeline uses it for:
   - Phase 2 grading subagents per sub-question: `sonnet` (cheap, mechanical tier/CRAAP application);
   - the Phase 5 decorrelated entailment judge: a **different** Claude model than the synthesis model (e.g. synthesis on opus → judge on sonnet), breaking same-model circularity;
   - optional Fable 5 synthesis subagents on exhaustive runs when the user opted in but keeps the session on opus.
3. **Declare the tier in the plan.** `research-plan.md` states the session model observed, the subagent models the run will use, and the cost implication — visible at the human gate.

## Flags

| Flag | Values | Default | Effect |
|---|---|---|---|
| `--model` | `opus` \| `fable` | `opus` | Synthesis tier. `fable` = opt-in (cost ~2×; see latency and refusal notes). |
| `--confidential` | boolean | off | Marks the run as confidential-path: subagents receive neutral references only (never confidential text), rigor profile escalates to `critical` (see `quality-gate.md`), and the plan records the retention posture. Fable 5 remains eligible (D-1). |

## Fable 5 operational notes (verified 2026-06-12)

- **Retention:** requires 30-day data retention; orgs configured for ZDR get `400` on every request. D-1 accepts 30-day retention for the target corpus — recorded in Linear AI-120.
- **Latency:** single turns on hard tasks can run many minutes. On exhaustive runs, expect the synthesis phase to be substantially slower; the runtime table in `quality-gate.md` still applies — if the 15-minute exhaustive budget cannot hold on fable, say so at the human gate.
- **Refusals:** Fable 5 runs safety classifiers targeting research biology and most cybersecurity content; benign security research can trigger false positives (`stop_reason: refusal` surfaced as a subagent failure). For research questions in security/bio domains, prefer the opus tier — note this in the plan when the topic matches.
- **Thinking:** always on for fable (no configuration needed or possible from a skill); opus runs adaptive thinking. No action required at the skill level.
- **Prompt cache is per model.** Never alternate the lead's work between models mid-run (cold cache each switch). Use dedicated subagents per model instead — each keeps its own warm cache.

## Cost re-baselining

When the user asks for a cost estimate at the human gate: estimate from the plan's Tavily call count and candidate volume, then apply the price table above for the chosen tier. For precise re-baselining of a recurring research workload, the user can run `/cost` after a run — the skill itself performs no token accounting (no API access, D-4).
