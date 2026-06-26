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

**Egress posture (decided 2026-06-26): reduce surface + fail-closed.** Raw Messages API bodies and full tool input/output bytes do **not** egress (do not enable `OTEL_LOG_RAW_API_BODIES`). Only prompt, completion text, tool **name**, and cost reach Langfuse. The gate is defense-in-depth: broadened secret families + **recursive** `strip_identity` + a **fail-closed** backstop that drops any field still matching a high-severity-secret heuristic after scrubbing.

A real `/deep-research` run, after enrichment, shows in Langfuse:

1. The interaction observation `input` = the user prompt (from `user_prompt`). Each **generation** `output` = the completion text from the **`assistant_response.response`** clean structured field — confirmed available with `OTEL_LOG_USER_PROMPTS=1` and **without** raw API bodies (empirically verified 2026-06-26). Raw bodies are never enabled.
2. Each **generation** with accurate **cost**, including `claude-opus-4-8[1m]` (cost ≠ 0), sourced from `api_request.cost_usd`.
3. Each **tool** observation labelled with its real `tool_name` (from `tool_decision`/`tool_result`). Full tool args/output are **not** egressed.
4. **No secret or identity-PII leakage**, fail-closed: a seeded fake secret and a fake email in a prompt do not appear in the outgoing payload, and a residual high-severity match causes the field to be **dropped**, not posted.

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
| `user_prompt` | `span_id` = interaction root (identity) | interaction obs `input` ← prompt |
| `api_request` | **`request_id`** → `llm_request` generation (resolve via the LIST endpoint `?traceId=`, path `metadata.attributes.request_id`) | `cost_details` ← `cost_usd` |
| `assistant_response` | **`request_id`** → same `llm_request` generation | generation `output` ← `response` (clean structured field; **no raw bodies needed** — gated by `OTEL_LOG_USER_PROMPTS`) |
| `tool_result` | `span_id` = tool span (identity) | tool obs `name` ← `tool_name` **only** (no args/output egressed) |

Emitted via the Langfuse ingestion API as **`generation-update`** for GENERATION targets and **`span-update`** for SPAN/tool targets (event type confirmed in Task 1; `observation-update` is rejected). Upsert semantics, idempotent.

## 6. Redaction & security

Posture: **reduce surface + fail-closed** (decided 2026-06-26). Raw API bodies and full tool I/O do **not** egress, so the content surface is prompt + completion + tool-name + cost. Redaction is a first-class, defense-in-depth component.

- **Single egress gate, in Python.** The `file` exporter writes raw logs to a local gitignored file (no network); the enricher redacts immediately **before** the POST — the only egress point.
- **Broadened secret families.** Reuse the Collector's set (`sk-ant-*`, Langfuse keys, generic `sk-`, AWS, GitHub, email, FR phone, canary) and add high-severity families plausible in research content: Google API key (`AIza…`), Slack (`xox[baprs]-…`), Stripe live keys (`sk_live_`/`rk_live_`), PEM private-key blocks (`-----BEGIN … PRIVATE KEY-----`), and `key=value` secret assignments. `(?i)` on **every** pattern (the tail-leak lesson — including the previously-missed AWS `AKIA`).
- **Recursive `strip_identity`.** Drop identity keys (`user.email`, `user.id`, `user.account_id`, `user.account_uuid`, `organization.id`) at **any** nesting depth, not just top-level.
- **Fail-closed backstop.** After scrubbing, if a field still matches a high-severity-secret heuristic (PEM block, known credential prefix, or `secret|token|api[_-]?key|password|bearer` `= <8+ chars>`), **DROP** that field (replace with a redaction placeholder) rather than POST it. Security wins over completeness; accept occasional false-positive drops.
- **`.gitignore`:** `eval/langfuse/.logs/` and `*.jsonl` never enter git.

## 7. Error handling

- **Observation not found** → log and skip that event; never fail the whole batch.
- **Ordering** → batch runs post-run, so spans are already ingested (the reason batch beats daemon).
- **Idempotence** → `observation-update` is upsert; the enricher may be re-run safely.
- **Auth / transient HTTP** → bounded retry with backoff; on persistent failure, exit non-zero with a clear message (nothing partially leaks because redaction precedes every POST).

## 8. Testing

- **Unit (fixture):** a captured JSONL sample → enricher → assert the exact `observation-update` payloads (right ids, right fields, right routing — including `request_id` → generation).
- **Canary (the `redaction-proof` analog):** seed a fake `sk-ant-…` secret and a fake email inside a prompt; run the enricher; assert both are masked in the outgoing payload. This is the enricher's egress-gate acceptance test.
- **Fail-closed test:** a field carrying an unknown-format but high-severity secret (e.g. a PEM `BEGIN PRIVATE KEY` block) is **dropped**, not posted.
- **Round-trip (integration):** real run → enrich → query the Langfuse API → assert prompt/completion/cost present on the trace/generation and **Opus cost ≠ 0**, and that no raw API body egressed.

## 9. Scope & non-goals

**In:** batch enricher; reduced-surface content (prompt + completion + tool-name + cost); `cost_usd` cost fix; Python-side redaction (broadened families + recursive `strip_identity` + **fail-closed drop**); the `file` exporter on the logs pipeline; `.gitignore` for the local log file.

**Out (YAGNI / posture):** **raw API bodies and full tool I/O do NOT egress** (`OTEL_LOG_RAW_API_BODIES` stays off); custom Go / custom Collector image; a streaming daemon; a Collector image change beyond the `file` exporter; the fail-closed *attribute allowlist* on the Collector traces path (separate M4 hardening — distinct from the enricher's fail-closed field drop, which IS in M3); routing logs *through* Langfuse OTLP (it rejects logs).

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
