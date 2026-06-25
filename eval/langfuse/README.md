# Langfuse observability for `/deep-research` (AI-182, Path A)

> Live tracing of `/deep-research` runs into Langfuse Cloud via an OpenTelemetry Collector that acts as the PII/secret **redaction egress gate**. Lab-side tooling — network-allowed, lives outside the markdown-only skill surface.

This directory is the **lab** half of AI-182. It holds the *heavy* (runtime instrumentation, Collector config, the redaction gate); the **brain** half — what Langfuse is, the creds pointer, run summaries — lives in the second-brain vault at `~/second-brain/50-stack/langfuse.md` (separate repo). It is deliberately **not** under `scripts/`, which the skill keeps stdlib-only and zero-network (`CLAUDE.md` invariant I4a).

## Why a Collector and not direct OTLP

Claude Code's richest telemetry — prompt/completion **content** (log events) and **cost** (metrics) — does not match what Langfuse ingests. Langfuse's OTLP endpoint (`/api/public/otel`) accepts the **traces** signal only, over HTTP, with Basic auth. A direct export therefore under-delivers, and worse, gives **no interception point** to sanitize content before it leaves the machine. The Collector solves both: it reconciles signals and is the single place to enforce redaction.

```text
Claude Code session (runs /deep-research)
  │  CLAUDE_CODE_ENABLE_TELEMETRY=1   (OTLP: metrics + log events + beta traces)
  ▼
OpenTelemetry Collector  ── THIS directory ──  single control point
  │  redaction (attrs) + transform/OTTL (event & log bodies) + filter (fail-closed)
  ▼
Langfuse Cloud Hobby   (OTLP /api/public/otel — traces signal, HTTP, Basic auth)
  └─ renders only after M2 log->span enrichment: native Claude Code export is log-events, not spans
```

## Quickstart

```bash
# 1. Boot the Collector (sources creds from ~/second-brain/.secrets/langfuse.env).
./run-collector.sh
docker logs -f langfuse-otelcol         # watch it authenticate + idle

# 2. Prove the redaction gate before trusting it with real content.
./redaction-proof.sh                    # PASS => seeded fake secrets never egress

# 3. Launch a traced run in a fresh shell (telemetry is per-process env).
source enable-claude-telemetry.sh && claude
#    ...then invoke /deep-research. NOTE: native Claude Code export is log-based;
#    Langfuse renders traces only after M2 enrichment (see Milestone scope).

# Stop:  docker rm -f langfuse-otelcol
```

## Files

| File | Role |
|------|------|
| `otel-collector-config.yaml` | Receiver -> `memory_limiter` + `redaction` + `transform` + `filter` (fail-closed) -> `otlp_http/langfuse` + `debug`. Requires the *contrib* distribution. |
| `run-collector.sh` | Sources `~/second-brain/.secrets/langfuse.env`, composes the Basic-auth header (secret never printed), runs the contrib Collector in Docker. |
| `enable-claude-telemetry.sh` | **Source** (not execute) to export Claude Code OTEL env vars at the local Collector, with content opt-in. |
| `redaction-proof.sh` | Pushes a synthetic span with seeded fake secrets; asserts they are masked before egress. The Slice-1 acceptance test. |

## Milestone scope — what actually lands (empirically verified)

| Milestone | State |
|-----------|-------|
| **M1 — egress gate (this build)** | OTEL Collector + 3-layer redaction gate, proven server-side; Claude Code telemetry confirmed reaching the Collector. **Built.** |
| **M2 — log→span enrichment** | Synthesize Langfuse spans/generations from Claude Code's log events (+ cost from metrics). **Prerequisite for any Langfuse trace rendering.** Deferred. |

**Empirical finding (2026-06-25, Claude Code 2.1.191, headless `-p`):** Claude Code emits its run as **log events** (86 records — lifecycle, prompts, tool content; scope `com.anthropic.claude_code.events`) plus **metrics**, and **zero trace spans**. Langfuse OTLP ingests **only traces**. So a real Claude Code run currently lands **nothing** in Langfuse — not because the pipeline is broken (the Collector received all 86 records and redacted them, 0 dropped), but because the signal types don't match. There is no "free" span visibility from the native (beta) export. M2's log→span correlation is therefore the **prerequisite** for Langfuse rendering, not a content/cost nicety. The redaction egress gate (M1) is proven end-to-end with a synthetic span. Whether *interactive* sessions emit beta trace spans (vs headless) is still worth confirming. Design doc: [`docs/superpowers/specs/2026-06-23-langfuse-deep-research-eval-design.md`](../../docs/superpowers/specs/2026-06-23-langfuse-deep-research-eval-design.md).

## Security posture

- **Secret never touches git.** Creds live in the gitignored `~/second-brain/.secrets/langfuse.env`; `run-collector.sh` sources them at runtime. This directory's `.gitignore` also blocks `*.env`.
- **Redaction is the egress gate.** Three layers: `redaction` masks secret/PII values in span attributes; `transform` (OTTL) scrubs the same patterns in span-event and log bodies (where attribute redaction does not reach); `filter` drops any record where a high-severity secret *survived* — fail-closed.
- **Hardening path.** The attribute posture is currently mask-not-drop (`allow_all_keys: true`). Flipping to an enumerated allowlist (`allow_all_keys: false`) after an M2 capture makes unknown attributes fail-closed by default.

## Known caveats (from the seeding research)

- Use **protobuf** OTLP (`OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf`); OTLP/JSON silently drops `gen_ai.usage.*` int64 token counts → zero cost.
- Claude Code OTEL trace support is **beta, CLI-only**; verify the trace export empirically per Claude Code version.
- `session.id` / `user.id` must propagate to every span (resource attrs / Baggage) or they fail to aggregate into a Langfuse Session.
