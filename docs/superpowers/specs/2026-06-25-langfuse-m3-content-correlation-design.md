---
title: "Langfuse M3 — log→span content correlation (out-of-band batch enricher)"
issue: AI-182
date: 2026-06-25
status: approved
supersedes_note: "Extends 2026-06-23-langfuse-deep-research-eval-design.md (Slice 1 content acceptance, line ~71)."
---

# Langfuse M3 — log→span content correlation

> Attach full-fidelity content (prompts, completions, tool I/O) and authoritative cost onto the Langfuse observations a `/deep-research` run already produces, via an out-of-band batch enricher that PATCHes Langfuse by `trace_id`/`span_id` — because Claude Code emits content as OTLP **log records** that Langfuse's traces-only OTLP endpoint drops.

## 1. Context

M2 (commit `9c8d184`) made Claude Code's **native spans** render in Langfuse as a trace whose `claude_code.llm_request` children are generations with model, token usage, and (for priced models) cost. Proven end-to-end: a real `/deep-research` run rendered a 30-observation trace; a haiku probe rendered `totalCost=$0.0355`.

Two gaps remain, both rooted in the same fact — **content lives in log records, not spans**:

- **Content gap.** Generations/tools render structure + usage but **no content**: `langfuse.observation.input`/`output` are empty; tool observations show `input: null`. The prompt/completion text and tool args/results are emitted as OTLP **log records** (scope `com.anthropic.claude_code.events`), which Langfuse's OTLP endpoint (traces only) silently drops.
- **Cost gap (finding A).** Real runs use `claude-opus-4-8[1m]`, which is absent from Langfuse's price table → `totalCost = 0` even though usage is fully populated. The `api_request` log carries an authoritative `cost_usd` per request, model-independent.

M3 closes both. It is the work that completes the existing design doc's Slice-1 acceptance: *"one real `/deep-research` run appears in Langfuse with cost/latency/tool-call spans and sanitized prompt/completion content."*

### Established facts (empirically verified 2026-06-25, Claude Code 2.1.191)

- Content log records carry **`trace_id` + `span_id`** → deterministic join, no timing heuristics.
- **Langfuse observation `id` == raw OTEL `span_id`** (identity), verified: span `55dc5051e1951eef` → obs `55dc5051e1951eef`; parent links match.
- The join is **not** uniformly span_id-direct: `user_prompt` and `api_request` logs attach to the **interaction (root)** span; the generation is the `llm_request` child. Cost/completion therefore route to the generation by a **secondary key, `request_id`**, not the log's span_id.
- `api_request` log carries `cost_usd` (e.g. `0.0557253`) — and disagrees with Langfuse's price-table computation (`$0.0355`); Claude Code's figure is authoritative (it knows real billing).
- Log records carry **cleartext identity PII** (`user.email`, `user.account_id`, `organization.id`). Today they reach only the `debug` exporter; any egress path must redact them.

## 2. Goal & success criteria

A real `/deep-research` run, after enrichment, shows in Langfuse:

1. Each **generation** with `input` (the API request messages) and `output` (the completion text); the **trace** with `input` = the user prompt.
2. Each **generation** with accurate **cost**, including `claude-opus-4-8[1m]` (cost ≠ 0), sourced from `api_request.cost_usd`.
3. Each **tool** observation with its real `tool_name`, `input` (args), and `output` (result).
4. **No secret or identity-PII leakage**: a seeded fake secret and a fake email in a prompt do not appear in the outgoing Langfuse payload.

## 3. Decision: out-of-band batch enricher

**Chosen.** The Collector keeps streaming native spans to Langfuse unchanged. A separate Python lab script reads the log signal off-Collector, redacts, and PATCHes the matching Langfuse observations by id via the ingestion API, **after** each run completes.

**Rejected alternatives:**

- **Custom Collector log→span connector (Go).** No off-the-shelf connector converts log records to spans; this needs a bespoke Go build and a custom image (abandoning the pinned `otel/opentelemetry-collector-contrib:0.155.0`), and relies on the *unverified* assumption that Langfuse merges two spans sharing a `span_id`. Heavy + risky; loses the clean supply chain for no gain over the API.
- **Streaming daemon enricher.** Same as batch but long-running and tailing logs live — introduces ordering races (content can arrive before the span is ingested) and ops overhead, for no benefit on discrete `/deep-research` runs.

Batch over daemon because a `/deep-research` run is a discrete event: enriching post-run means spans are already ingested, so the PATCH always finds its target.

## 4. Architecture

```text
Claude Code run  ──OTLP──▶  OTEL Collector
                              ├─ traces  ─▶ Langfuse (spans: structure + usage + remapped cost)   [unchanged, M2]
                              └─ logs    ─▶ file exporter ─▶ eval/langfuse/.logs/<run>.jsonl       [NEW, local, gitignored]

(post-run)  eval/langfuse/enrich.py
   read JSONL → group by trace_id → route by event → REDACT → POST /api/public/ingestion
   (observation-update events, id = span_id)                          ─▶ Langfuse (content + cost)
```

- **Collector change:** add a `file` exporter to the existing `logs` pipeline. Raw records to a **local, gitignored** file (`eval/langfuse/.logs/`); nothing extra egresses from the Collector.
- **`eval/langfuse/enrich.py`:** stdlib + one HTTP POST to `/api/public/ingestion`. Lives in the network-allowed lab zone, **not** `scripts/` (which is zero-network per CLAUDE.md I4a). Invoked `enrich.py --run <file>` (or `--since <ts>`).

The enricher is a single-purpose unit: input = a JSONL log file + Langfuse creds; output = `observation-update` POSTs. It does not touch the span path and can be tested in isolation against fixtures.

## 5. Data flow & routing table

The enricher groups log records by `trace_id` and routes each content event to its observation:

| Log event | Join key → target observation | Langfuse fields set |
|---|---|---|
| `user_prompt` | `span_id` = interaction root (identity) | trace-level `input` |
| `api_request` | **`request_id`** → `llm_request` generation | `input` (request messages) + `output` (completion) when `OTEL_LOG_RAW_API_BODIES=1`; `cost_details` ← `cost_usd` |
| `tool_decision` / `tool_result` | `span_id` = tool span (identity) | tool obs `input` (args), `output` (result), `name`/metadata ← `tool_name` |

Emitted as `observation-update` events — **upsert semantics, idempotent**: re-running the enricher is a safe no-op-or-refresh.

## 6. Redaction & security

Full fidelity = the largest possible egress surface (full prompts, completions, tool outputs, raw API bodies of real research runs). Redaction is therefore a first-class component, not a regex afterthought.

- **Single egress gate, in Python.** The `file` exporter writes **raw** logs to a **local** gitignored file (no network). The enricher redacts immediately **before** the POST — the only point where content leaves the machine. Python redaction is structured and unit-testable, stronger than regex-in-YAML.
- **Patterns:** reuse the Collector's secret/PII set (`sk-ant-*`, Langfuse keys, AWS, GitHub, email, FR phone, canary) and **extend** for the larger content surface. `(?i)` on every pattern (the tail-leak lesson).
- **Identity PII:** strip `user.email` and account/org ids before egress (decision deferred to spec review: drop entirely vs. map `user.email` → Langfuse `user.id`). Default: **drop**.
- **`.gitignore`:** `eval/langfuse/.logs/` and `*.jsonl` never enter git.

## 7. Error handling

- **Observation not found** → log and skip that event; never fail the whole batch.
- **Ordering** → batch runs post-run, so spans are already ingested (the reason batch beats daemon).
- **Idempotence** → `observation-update` is upsert; the enricher may be re-run safely.
- **Auth / transient HTTP** → bounded retry with backoff; on persistent failure, exit non-zero with a clear message (nothing partially leaks because redaction precedes every POST).

## 8. Testing

- **Unit (fixture):** a captured JSONL sample → enricher → assert the exact `observation-update` payloads (right ids, right fields, right routing — including `request_id` → generation).
- **Canary (the `redaction-proof` analog):** seed a fake `sk-ant-…` secret and a fake email inside a prompt; run the enricher; assert both are masked in the outgoing payload. This is the enricher's egress-gate acceptance test.
- **Round-trip (integration):** real run → enrich → query the Langfuse API → assert `input`/`output` present on generations and tools, and **Opus cost ≠ 0**.

## 9. Scope & non-goals

**In:** batch enricher; the full-fidelity content chosen; `cost_usd` cost fix; Python-side redaction; the `file` exporter on the logs pipeline; `.gitignore` for the local log file; `OTEL_LOG_RAW_API_BODIES=1` in the enable script.

**Out (YAGNI):** custom Go / custom Collector image; a streaming daemon; a Collector image change beyond the `file` exporter; the fail-closed attribute allowlist (separate hardening item); routing logs *through* Langfuse OTLP (it rejects logs).

## 10. Open items to settle in the plan / implementation

- Exact Langfuse `/api/public/ingestion` `observation-update` event shape for `input`/`output`/`cost_details` (confirm against current Langfuse API).
- Identity-PII handling: drop vs. map to `user.id` (default drop; confirm at spec review).
- Whether completion text is fully present under `OTEL_LOG_RAW_API_BODIES=1` or truncated (verify on first capture).
- Tool-span join: confirm `tool_result.span_id` equals the `claude_code.tool` observation id (not a child `tool.execution`).

## References

- M2 build: commit `9c8d184`; `eval/langfuse/otel-collector-config.yaml`, `enable-claude-telemetry.sh`, `README.md`.
- Langfuse OTEL attribute mapping: `langfuse.com/integrations/native/opentelemetry` (retrieved 2026-06-25).
- Prior design: `docs/superpowers/specs/2026-06-23-langfuse-deep-research-eval-design.md`.
- Linear AI-182 (Path A); CLAUDE.md invariant I4a (skill surface markdown-only; `scripts/` zero-network; `eval/langfuse/` is the network-allowed lab zone).
