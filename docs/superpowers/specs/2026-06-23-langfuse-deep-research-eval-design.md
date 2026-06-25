---
title: Langfuse observability + live eval of /deep-research
ticket: AI-182
related: [AI-38, AI-124, AI-115]
status: draft
date: 2026-06-23
---

# Langfuse observability + live eval of /deep-research

> Wire Langfuse Cloud Hobby onto the `/deep-research` skill to observe real runs live and evaluate output quality over time, without violating the skill's markdown-only contract.

## Problem

The skill already has a strong **offline** evaluation harness (AI-124: deterministic gates, decorrelated entailment judge, sycophancy probes, frozen benchmark). It has **no live observability** — no per-run view of cost, latency, tool-call sequence, or prompt/completion content — and no hosted store to track quality scores across runs. This work adds that layer for upskilling on harness engineering and agent evaluation, and as reusable AI-SRE tooling.

## Constraint that shapes the architecture

`CLAUDE.md` invariant I4a: the skill surface is markdown-only, and `scripts/` is stdlib-only and **zero-network**. No Langfuse SDK call can live inside the skill. All instrumentation lives outside it — at the Claude Code harness layer (OpenTelemetry) or in a separate offline uploader.

`★ Insight ─────────────────────────────────────`
Langfuse is two separable capabilities: **tracing** (live spans, needs runtime instrumentation) and **evaluation** (Datasets → Runs → Scores, can run fully offline on saved artifacts). The markdown-only constraint forces tracing to the OTEL layer and evaluation to an external uploader — they are independent integrations, built in separate slices.
`─────────────────────────────────────────────────`

## Integration paths

| Path | Mechanism | Decision |
|------|-----------|----------|
| A — live tracing | Claude Code OTEL → OTEL Collector (redaction) → Langfuse OTLP | Slice 1, build now |
| B — offline eval | Maintainer uploader replays artifacts + AI-124 judges → Langfuse Datasets/Scores | Slice 2, README roadmap |
| C — SDK port | Reimplement pipeline on Claude Agent SDK with `@observe` | Out of scope (different artifact) |

## Slice 1 architecture (Path A)

Data flow:

```text
Claude Code session (runs /deep-research)
  │  CLAUDE_CODE_ENABLE_TELEMETRY=1  (OTLP metrics + log events)
  ▼
OpenTelemetry Collector  ← single control point
  │  redaction/masking processor  (PII + secret scrub)  ← egress gate
  ▼
Langfuse Cloud Hobby  (OTLP endpoint /api/public/otel)
  └─ traces · cost · latency · tool-calls · SANITIZED prompt/completion
```

Decisions locked:

- **Content tracing ON, sanitized.** Prompts and completions are traced, but PII/secrets are scrubbed by the Collector processor *before* egress. The Collector is the single redaction control point.
- **Direct-OTLP vs Collector** is resolved in favor of the Collector specifically because sanitization is required — direct export gives no interception point. (Confirm the exact redaction processor in the seeding research.)
- **Cloud Hobby for all runs.** Acceptable because the Collector enforces redaction and the first runs are public-topic.

Deferred to post-research:

- Exact fidelity of Claude Code's OTEL export mapped onto Langfuse's trace/observation/generation model (coarse session/turn events vs clean per-LLM-generation spans).
- Whether prompt-content log events need an explicit Claude Code flag (e.g. `OTEL_LOG_USER_PROMPTS`) and how that interacts with Collector-side masking.

## Slice 2 architecture (Path B) — roadmap only

A maintainer/CI tool under a new top-level `eval/langfuse/` (NOT `scripts/`, which must stay zero-network) takes a run's four artifacts, runs the AI-124 judges, and pushes Datasets + Runs + Scores to Langfuse. Langfuse becomes the cross-run quality leaderboard and regression dashboard. Extends AI-124; does not replace it.

## Error handling and failure posture

- Collector unreachable → Claude Code OTEL export fails open (telemetry is best-effort, never blocks a run).
- Redaction processor misconfigured → fail **closed** on egress (drop the span rather than leak unsanitized content). Verify this is the Collector default, else configure it.
- Langfuse quota/auth failure → run completes normally; only observability is lost.

## Testing

- Slice 1 acceptance: one real `/deep-research` run appears in Langfuse with cost/latency/tool-call spans and sanitized prompt/completion content; a deliberately-seeded fake secret in a prompt does NOT appear in Langfuse (redaction proof).
- No skill-surface test changes — Path A touches zero skill files.

## Seeding research

Broad `/deep-research` run at `~/Desktop/AIEngineering/research-runs/langfuse-agent-eval/`, covering documentation + newsletter corpus + GitHub (stars and broader trending). Resolves the deferred items above and serves as the first candidate artifact for Slice 2.
