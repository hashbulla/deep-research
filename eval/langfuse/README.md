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
  └─ traces render as generations (model, tokens, cost) — enabled by CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1
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
#    ...then invoke /deep-research. Each turn renders in Langfuse as a trace whose
#    llm_request children are generations with model + tokens + cost. The beta flag in
#    enable-claude-telemetry.sh is what makes spans emit (no flag => no spans).

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
| **M1 — egress gate** | OTEL Collector + 3-layer redaction gate, proven server-side (a real `user.email` was masked in a live span). **Built.** |
| **M2 — native spans + cost** | `CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1` makes Claude Code emit native spans; the Collector remaps token counts to `gen_ai.usage.*` so Langfuse renders them as generations **with cost**. **Built + verified 2026-06-25.** |
| **M3 — content enrichment** | Correlate the log-event prompt/completion **content** onto generation input/output via post-run `enrich.py` script. **Built + verified.** |

**Empirical finding (2026-06-25, Claude Code 2.1.191):** Claude Code emits **native OTLP trace spans** — `claude_code.interaction` (root) → `claude_code.llm_request` / `claude_code.tool` (scope `com.anthropic.claude_code.tracing`) — but **only when `CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1` is set** alongside `CLAUDE_CODE_ENABLE_TELEMETRY=1`. The earlier "zero spans" result was that **missing flag**, not an interactive-vs-headless difference (there is none — both modes emit). The `llm_request` span carries OTel GenAI semconv (`gen_ai.request.model`, token counts, `ttft_ms`/`duration_ms`), so Langfuse promotes it to a **generation** automatically. Claude Code emits **bare** `input_tokens`/`output_tokens`/`cache_read_tokens`/`cache_creation_tokens`; the Collector's `transform/usage_semconv` remaps all four to `gen_ai.usage.*` so Langfuse computes **cost**. Verified end-to-end via the Langfuse API: `totalCost=$0.0355`, with `cache_creation_input_tokens` ≈ **95% of the bill** — mapping only input/output would have undercount cost ~100×. The 86 `com.anthropic.claude_code.events` **log** records still flow alongside (prompt/tool content); Langfuse OTLP ignores logs, so that content is not yet on the generation — M3 content enrichment is built — `enrich.py` correlates log-event prompt/completion content onto generation observations post-run. Design doc: [`docs/superpowers/specs/2026-06-23-langfuse-deep-research-eval-design.md`](../../docs/superpowers/specs/2026-06-23-langfuse-deep-research-eval-design.md).

## Security posture

- **Secret never touches git.** Creds live in the gitignored `~/second-brain/.secrets/langfuse.env`; `run-collector.sh` sources them at runtime. This directory's `.gitignore` also blocks `*.env`.
- **Redaction is the egress gate.** Three layers: `redaction` masks secret/PII values in span attributes; `transform` (OTTL) scrubs the same patterns in span-event and log bodies (where attribute redaction does not reach); `filter` drops any record where a high-severity secret *survived* — fail-closed.
- **Hardening path.** The attribute posture is currently mask-not-drop (`allow_all_keys: true`). Flipping to an enumerated allowlist (`allow_all_keys: false`) makes unknown attributes fail-closed by default. The enricher's in-Python `sanitize` gate (strip_identity → fail_closed) applies independently of the Collector layer.

## Content enrichment (M3)

The native OTLP spans carry model + token counts + cost, but prompt and completion **content** flows only via Claude Code log events. The post-run `enrich.py` script correlates that content onto Langfuse generation observations:

```bash
python3 enrich.py --run .logs/claude-logs.jsonl
```

The enricher reads the Collector's file-exported logs, applies redaction (mask-tier secrets + drop-tier PII + recursive identity strip), and PATCHes Langfuse observations: `api_request` log → generation `input`, `assistant_response` → generation `output`, tool-name → tool span, cost → generation cost fields. Redaction is enforced in Python before any egress; the reduce-surface posture keeps raw API bodies off the wire (they are deliberately commented out in `enable-claude-telemetry.sh`), so content comes only from the clean `assistant_response` event. All failures to ingest an observation are fail-closed: unmapped observations are skipped with a stderr warning and do not block the run.

## Known caveats (from the seeding research)

- Use **protobuf** OTLP (`OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf`); OTLP/JSON silently drops `gen_ai.usage.*` int64 token counts → zero cost.
- Claude Code OTEL trace support is **beta, CLI-only**, gated by `CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1` — without it, **no spans emit** (this was the original "zero spans" red herring). Re-verify the export empirically per Claude Code version.
- `session.id` / `user.id` must propagate to every span (resource attrs / Baggage) or they fail to aggregate into a Langfuse Session.
