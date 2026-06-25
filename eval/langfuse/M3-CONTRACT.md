# M3 Spike — Confirmed Langfuse API Contracts

> Empirical SPIKE executed 2026-06-25. All facts below are observed, not assumed.
> Test observation `55dc5051e1951eef` in trace `202126283572113feda57489172cf417` was used.
> A harmless `"M3 SPIKE OK"` output and dummy usage/cost were written to that observation — acceptable (disposable test trace).

---

## Contract 1 — Ingestion event type for GENERATION observations

### Finding

`observation-update` is **rejected** for GENERATION-type observations with HTTP 207 partial:

```json
{"code":"invalid_value","values":["GENERATION","SPAN","EVENT"],
 "path":["body","type"],"message":"Invalid option: expected one of \"GENERATION\"|\"SPAN\"|\"EVENT\""}
```

**Use `generation-update`** — accepted with `{"successes":[{"id":"...","status":201}],"errors":[]}`.

### Accepted body keys for `generation-update`

| Body key | Type | Effect |
|----------|------|--------|
| `id` | string | Required — observation id to patch (== span_id hex) |
| `output` | string | Sets generation output text |
| `input` | string | Sets generation input text |
| `usage.input` | int | Sets `promptTokens` |
| `usage.output` | int | Sets `completionTokens` |
| `costDetails.input` | float | Input cost in USD |
| `costDetails.output` | float | Output cost in USD |
| `costDetails.cache_read_input_tokens` | float | Cache-read cost in USD |
| `costDetails.cache_creation_input_tokens` | float | Cache-creation cost in USD |

Langfuse computes `costDetails.total` server-side from the provided fields.

### Propagation lag

The Hobby tier introduces a ~3–5s propagation delay between ingestion and read-back.
Poll with a retry or add `sleep 5` before verifying.

---

## Contract 2 — `request_id` metadata path in GENERATION observations

### Finding

`request_id` lives at **`metadata.attributes.request_id`** in both the list and single-observation endpoints.

```
GENERATION observation metadata structure:
  metadata
  └── attributes
        ├── request_id: "req_XXXXXX..."   ← PRIMARY mapping key
        ├── gen_ai.response.id: "req_XXXXXX..."   ← IDENTICAL value (alias)
        ├── gen_ai.system: "anthropic"
        ├── gen_ai.request.model: "..."
        ├── span.type: "llm_request"
        └── ... (token counts, timing, etc.)
  └── resourceAttributes: {...}
  └── scope: {...}
```

`metadata.request_id` (top-level) is **null** — do not use.
`metadata.gen_ai.response.id` (top-level, not nested under `attributes`) is **null** — do not use.

`metadata.attributes.request_id` == `metadata.attributes.gen_ai.response.id` — both point to the Anthropic request id (e.g., `req_011CcPwtUykNbLGH5ryW5ohn`).

### jq path

```bash
jq '[.data[] | select(.type=="GENERATION") | {id, request_id: .metadata.attributes.request_id}]'
```

### Critical implementation note — endpoint selection

The **single-observation GET** (`/api/public/observations/{id}`) returns **empty** `metadata.attributes`
after any `generation-update` PATCH has been applied to that observation.
The **list GET** (`/api/public/observations?traceId=...`) preserves the full attributes.

**The enricher MUST use the list endpoint to retrieve `request_id`**, not the single-observation endpoint.

### Fallback (if `request_id` absent)

Map `api_request` cost/completion to generation by **start-time ordering** within the trace:
Nth `api_request` span (sorted by `startTime`) → Nth GENERATION observation (sorted by `startTime`).

---

## Contract 3 — OTEL span/trace id encoding

### Finding

Both the OTEL Collector debug exporter and the Langfuse REST API represent trace/span IDs as **lowercase hex strings**.

| Field | Format | Length | Example |
|-------|--------|--------|---------|
| `traceId` | lowercase hex | 32 chars (128-bit) | `202126283572113feda57489172cf417` |
| `spanId` | lowercase hex | 16 chars (64-bit) | `55dc5051e1951eef` |

Evidence:
- Collector debug log: `Trace ID: 517be03934ab2078c2e508e1da9528b0` (all hex, 32 chars).
- Langfuse API `observation.id` == OTEL `spanId` (hex, 16 chars) — identity mapping confirmed in M2.
- Known test IDs verified hex: `[0-9a-f]+` pattern matches, no base64 padding or `+`/`/` chars present.

The OTLP/proto binary encoding uses raw bytes internally; both the file exporter and Langfuse REST decode to hex, not base64. The parser in Task 3 should assume **hex input**.

---

## Spike commands reference (credentials elided)

```bash
# Step 1 — confirm generation-update
curl -s -u "PUB_KEY:SECRET_KEY" -H 'Content-Type: application/json' -X POST \
  "https://cloud.langfuse.com/api/public/ingestion" \
  -d '{"batch":[{"id":"m3-spike-2","type":"generation-update","timestamp":"...","body":{"id":"SPAN_ID","output":"M3 SPIKE OK"}}]}'

# Step 2 — list observations in trace (use list endpoint, not single-obs)
curl -s -u "PUB_KEY:SECRET_KEY" \
  "https://cloud.langfuse.com/api/public/observations?traceId=TRACE_ID" \
  | jq '[.data[]|select(.type=="GENERATION")|{id, request_id:.metadata.attributes.request_id}]'

# Step 3 — hex encoding confirmed from collector debug logs (no file exporter needed)
docker logs langfuse-otelcol | grep "Trace ID"
```

---

## Open questions for Task 2 / Task 3

- `api_request` spans carrying cost/token data are emitted to the **logs** pipeline (not traces). Task 2 must wire a file exporter on the **logs** pipeline to capture them.
- The `generation-update` body supports `usage` and `costDetails` but the mapping from raw Claude Code attributes (`input_tokens`, `cache_read_tokens`) to these keys needs Task 3 to implement.
- Single-observation endpoint loses attributes after PATCH — store `request_id` values in enricher memory before writing.
