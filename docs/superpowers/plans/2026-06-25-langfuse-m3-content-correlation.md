# Langfuse M3 — Content Correlation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Attach full-fidelity content (prompts, completions, tool I/O) and authoritative per-request cost onto the Langfuse observations a `/deep-research` run already produces, via a post-run out-of-band batch enricher.

**Architecture:** The OTEL Collector gains a `file` exporter on its existing `logs` pipeline, writing raw Claude Code log records to a local gitignored JSONL file. A stdlib-only Python enricher (`eval/langfuse/enrich.py` + focused helper modules) parses that file, redacts secrets/PII, routes each content event to the correct Langfuse observation (`id == span_id`; cost/completion to the generation by `request_id`), and PATCHes them via Langfuse's `/api/public/ingestion` endpoint. Redaction in Python is the single egress gate.

**Tech Stack:** Python 3 stdlib only (`json`, `re`, `urllib.request`, `argparse`, `dataclasses`, `base64`, `unittest`). No third-party deps. Langfuse Cloud OTLP + ingestion REST API. OTEL Collector contrib 0.155.0.

## Global Constraints

- **Lab zone only.** All code lives under `eval/langfuse/` (network-allowed). It must NEVER live under `scripts/` (CLAUDE.md I4a: `scripts/` is stdlib-only AND zero-network). Tests live under `eval/langfuse/tests/`.
- **Stdlib only.** No `requests`, no `pydantic`, no `pytest` — use `urllib.request` and `unittest`.
- **Egress posture = reduce surface + fail-closed (decided 2026-06-26, supersedes "full fidelity").** Raw Messages API bodies and full tool input/output bytes do **NOT** egress (`OTEL_LOG_RAW_API_BODIES` stays OFF). Egress surface = prompt (`user_prompt.prompt`) + completion (`assistant_response.response` — a clean structured field, **no raw bodies needed**, verified 2026-06-26) + tool **name** (`tool_result.tool_name`) + cost (`api_request.cost_usd`).
- **Redaction precedes every egress.** No content reaches a Langfuse API call before passing the redactor. `(?i)` on **every** secret/PII pattern (uppercase-only classes leak lowercase tails). Secret families are broadened (Google `AIza`, Slack `xox*`, Stripe live, PEM private-key blocks, `key=value` secrets) beyond the Collector's base set.
- **Fail-closed backstop.** After scrubbing, any field still matching a high-severity-secret heuristic is **dropped** (replaced with a placeholder), not posted.
- **Identity PII is dropped recursively**, not mapped: `user.email`, `user.account_id`, `user.account_uuid`, `organization.id`, `user.id` never egress, at any nesting depth.
- **Secret never printed/committed.** Langfuse creds come from `~/second-brain/.secrets/langfuse.env` (gitignored); never echo them.
- **Langfuse observation id == raw OTEL span_id** (verified identity, 2026-06-25).
- **The local log file never enters git:** `eval/langfuse/.logs/` and `*.jsonl` are gitignored.

---

## File Structure

| File | Responsibility |
|---|---|
| `eval/langfuse/otel-collector-config.yaml` | (modify) add `file` exporter to the `logs` pipeline |
| `eval/langfuse/.gitignore` | (modify) ignore `.logs/` and `*.jsonl` |
| `eval/langfuse/enrich.py` | CLI entrypoint: orchestrates parse → route → redact → POST |
| `eval/langfuse/enrich_parse.py` | JSONL OTLP-logs → `LogRecord` dataclass list |
| `eval/langfuse/enrich_redact.py` | redact secrets + drop identity PII from any string/dict |
| `eval/langfuse/enrich_route.py` | `LogRecord`s + request_id index → `ObservationUpdate` events |
| `eval/langfuse/enrich_langfuse.py` | Langfuse client: GET observations (build request_id index), POST ingestion batch |
| `eval/langfuse/tests/__init__.py` | test package marker |
| `eval/langfuse/tests/fixtures/logs-sample.jsonl` | captured real log records (redacted of real PII) for unit tests |
| `eval/langfuse/tests/test_parse.py` | parser unit tests |
| `eval/langfuse/tests/test_redact.py` | redaction + canary unit tests |
| `eval/langfuse/tests/test_route.py` | routing unit tests |
| `eval/langfuse/tests/run-roundtrip.sh` | integration: real run → enrich → assert via Langfuse API |

---

## Task 1: Spike — confirm the two live contracts

Resolve the spec's open items empirically before writing code. No production code in this task; the deliverable is a short notes file capturing confirmed shapes + working curls. The Collector from M2 should be running (`docker ps | grep langfuse-otelcol`); if not, `eval/langfuse/run-collector.sh`.

**Files:**
- Create: `eval/langfuse/M3-CONTRACT.md` (notes; committed)

- [ ] **Step 1: Confirm the Langfuse ingestion `observation-update` event shape.**

POST a no-op update to an existing observation and read it back. Use an observation id from a known trace (e.g. an `llm_request` generation id).

```bash
cd eval/langfuse
set -a; source ~/second-brain/.secrets/langfuse.env; set +a
base="${LANGFUSE_BASE_URL}"; [[ "$base" =~ ^https?:// ]] || base="https://$base"; base="${base%/}"
OBS=55dc5051e1951eef   # a known generation observation id (== span_id)
curl -s -u "${LANGFUSE_PUBLIC_KEY}:${LANGFUSE_SECRET_KEY}" \
  -H 'Content-Type: application/json' \
  -X POST "$base/api/public/ingestion" \
  -d '{"batch":[{"id":"m3-spike-1","type":"observation-update","timestamp":"2026-06-25T12:00:00Z","body":{"id":"'"$OBS"'","output":"M3 SPIKE OK"}}]}'
echo
# read back:
curl -s -u "${LANGFUSE_PUBLIC_KEY}:${LANGFUSE_SECRET_KEY}" "$base/api/public/observations/$OBS" | jq '{id, output}'
```

Expected: ingestion returns `{"successes":[...],"errors":[]}`; the read-back shows `output: "M3 SPIKE OK"`. Record the exact accepted event `type` (`observation-update` vs `generation-update`) and the body keys for `input`/`output`/`costDetails` in `M3-CONTRACT.md`. If `observation-update` is rejected for a generation, retry with `generation-update`.

- [ ] **Step 2: Confirm the request_id → generation observation mapping.**

Verify the `llm_request` generation observation carries `request_id` in queryable metadata, so the enricher can map an `api_request` log to the right generation.

```bash
curl -s -u "${LANGFUSE_PUBLIC_KEY}:${LANGFUSE_SECRET_KEY}" \
  "$base/api/public/observations?traceId=202126283572113feda57489172cf417" \
  | jq '[.data[]|select(.type=="GENERATION")|{id, requestId:(.metadata.request_id // .metadata.attributes.request_id // null), gen_ai_response_id:(.metadata."gen_ai.response.id" // null)}]'
```

Expected: each generation shows a non-null `request_id` (or `gen_ai.response.id`) in metadata. Record in `M3-CONTRACT.md` the exact metadata path. If neither is present, the fallback is documented there: map `api_request` cost/completion to the generation by **start-time ordering** within the trace (Nth api_request → Nth generation).

- [ ] **Step 3: Confirm the `file` exporter id encoding.**

Add a temporary `file` exporter, capture one line, inspect whether `traceId`/`spanId` are hex or base64.

```bash
docker exec langfuse-otelcol sh -c 'ls /tmp' 2>/dev/null || true   # sanity
# (Task 2 wires the exporter; here just note from a manual one-off capture)
```

Record in `M3-CONTRACT.md`: OTLP/JSON encodes `traceId`/`spanId` as **hex** strings in the file exporter's output (the parser in Task 3 will assume hex and the fixture in Task 2 confirms it).

- [ ] **Step 4: Commit the contract notes.**

```bash
git add eval/langfuse/M3-CONTRACT.md
git commit -m "docs(langfuse): M3 spike — confirm Langfuse ingestion + request_id mapping (AI-182)"
```

---

## Task 2: Collector `file` exporter + captured fixture

**Files:**
- Modify: `eval/langfuse/otel-collector-config.yaml` (add `file` exporter; add to `logs` pipeline)
- Modify: `eval/langfuse/.gitignore`
- Create: `eval/langfuse/tests/fixtures/logs-sample.jsonl`

**Interfaces:**
- Produces: a JSONL file where each line is an OTLP `ExportLogsServiceRequest` JSON object with `resourceLogs[].scopeLogs[].logRecords[]`, each record having `traceId` (hex), `spanId` (hex), `body.stringValue`, and `attributes[]` (`{key, value:{stringValue|intValue|doubleValue}}`).

- [ ] **Step 1: Add the `file` exporter.** In `otel-collector-config.yaml`, under `exporters:`, add:

```yaml
  # M3: raw logs to a LOCAL gitignored file for the post-run enricher. Never egresses.
  file/m3logs:
    path: /etc/otelcol-contrib/.logs/claude-logs.jsonl
```

- [ ] **Step 2: Mount the log dir and wire the exporter.** In `run-collector.sh`, add a volume mount for `.logs/` (`-v "$HERE/.logs:/etc/otelcol-contrib/.logs"`) after creating `mkdir -p "$HERE/.logs"`. In `otel-collector-config.yaml`, change the `logs` pipeline exporters from `[debug]` to `[debug, file/m3logs]`.

- [ ] **Step 3: Restart + run one traced session to capture logs.**

```bash
cd eval/langfuse
mkdir -p .logs
./run-collector.sh >/dev/null
export CLAUDE_CODE_ENABLE_TELEMETRY=1 CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1 \
  OTEL_LOGS_EXPORTER=otlp OTEL_TRACES_EXPORTER=otlp \
  OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318 \
  OTEL_LOG_USER_PROMPTS=1 OTEL_LOG_TOOL_DETAILS=1 OTEL_LOG_TOOL_CONTENT=1 OTEL_LOG_RAW_API_BODIES=1
claude -p "Reply with exactly: ok" --model haiku >/dev/null
ls -la .logs/claude-logs.jsonl
```

Expected: `.logs/claude-logs.jsonl` exists and is non-empty.

- [ ] **Step 4: Build the test fixture from the capture.** Copy a handful of representative lines (one each of `user_prompt`, `api_request`, `tool_decision`, `tool_result`) into `tests/fixtures/logs-sample.jsonl`. **Hand-edit any real PII** (replace the real email/account ids/prompt with synthetic values; insert one synthetic `sk-ant-FAKE...` secret and one `canary@example.com` for the redaction test). Confirm `traceId`/`spanId` are hex.

- [ ] **Step 5: Commit.**

```bash
git add eval/langfuse/otel-collector-config.yaml eval/langfuse/run-collector.sh eval/langfuse/.gitignore eval/langfuse/tests/fixtures/logs-sample.jsonl
git commit -m "feat(langfuse): M3 file exporter on logs pipeline + log fixture (AI-182)"
```

---

## Task 3: Log parser

**Files:**
- Create: `eval/langfuse/enrich_parse.py`
- Create: `eval/langfuse/tests/__init__.py` (empty)
- Test: `eval/langfuse/tests/test_parse.py`

**Interfaces:**
- Produces: `@dataclass LogRecord(trace_id: str, span_id: str, event_name: str, attrs: dict[str, str|int|float])` and `def parse_jsonl(path: str) -> list[LogRecord]`.

- [ ] **Step 1: Write the failing test.**

```python
# eval/langfuse/tests/test_parse.py
import os, unittest
from enrich_parse import parse_jsonl, LogRecord

FIX = os.path.join(os.path.dirname(__file__), "fixtures", "logs-sample.jsonl")

class TestParse(unittest.TestCase):
    def test_extracts_records_with_ids_and_attrs(self):
        recs = parse_jsonl(FIX)
        self.assertTrue(any(r.event_name == "user_prompt" for r in recs))
        up = next(r for r in recs if r.event_name == "user_prompt")
        self.assertRegex(up.trace_id, r"^[0-9a-f]{32}$")
        self.assertRegex(up.span_id, r"^[0-9a-f]{16}$")
        self.assertIn("prompt", up.attrs)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it, verify it fails.**

Run: `cd eval/langfuse && python3 -m unittest tests.test_parse -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'enrich_parse'`.

- [ ] **Step 3: Implement the parser.**

```python
# eval/langfuse/enrich_parse.py
"""Parse the Collector's file-exported OTLP logs (JSONL) into flat LogRecords."""
import json
from dataclasses import dataclass

@dataclass
class LogRecord:
    trace_id: str
    span_id: str
    event_name: str
    attrs: dict

def _attr_value(v: dict):
    for k in ("stringValue", "intValue", "doubleValue", "boolValue"):
        if k in v:
            return int(v[k]) if k == "intValue" else v[k]
    return None

def _flatten_attrs(attr_list):
    out = {}
    for a in attr_list or []:
        out[a["key"]] = _attr_value(a.get("value", {}))
    return out

def parse_jsonl(path: str) -> list:
    records = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            req = json.loads(line)
            for rl in req.get("resourceLogs", []):
                for sl in rl.get("scopeLogs", []):
                    for lr in sl.get("logRecords", []):
                        attrs = _flatten_attrs(lr.get("attributes", []))
                        records.append(LogRecord(
                            trace_id=lr.get("traceId", ""),
                            span_id=lr.get("spanId", ""),
                            event_name=attrs.get("event.name", ""),
                            attrs=attrs,
                        ))
    return records
```

- [ ] **Step 4: Run it, verify it passes.**

Run: `cd eval/langfuse && python3 -m unittest tests.test_parse -v`
Expected: PASS.

- [ ] **Step 5: Commit.**

```bash
git add eval/langfuse/enrich_parse.py eval/langfuse/tests/__init__.py eval/langfuse/tests/test_parse.py
git commit -m "feat(langfuse): M3 OTLP-logs JSONL parser (AI-182)"
```

---

## Task 4: Redaction (the egress gate) + canary test

**Files:**
- Create: `eval/langfuse/enrich_redact.py`
- Test: `eval/langfuse/tests/test_redact.py`

**Interfaces:**
- Produces: `def redact(value)` (recursively masks secrets in any str/dict/list) and `IDENTITY_PII_KEYS: frozenset[str]` and `def strip_identity(attrs: dict) -> dict`.

- [ ] **Step 1: Write the failing test (canary + identity-drop).**

```python
# eval/langfuse/tests/test_redact.py
import unittest
from enrich_redact import redact, strip_identity

class TestRedact(unittest.TestCase):
    def test_masks_secret_and_email(self):
        s = "key sk-ant-FAKE0123456789abcdef0123 mail canary@example.com end"
        out = redact(s)
        self.assertNotIn("sk-ant-FAKE0123456789abcdef0123", out)
        self.assertNotIn("canary@example.com", out)
        self.assertIn("REDACTED", out)

    def test_masks_lowercase_tail(self):
        self.assertNotIn("deadbeef", redact("sk-ant-ABCDEF0123456789deadbeef"))

    def test_strip_identity_drops_pii_keys(self):
        attrs = {"user.email": "x@y.com", "organization.id": "org", "prompt": "keep"}
        out = strip_identity(attrs)
        self.assertNotIn("user.email", out)
        self.assertNotIn("organization.id", out)
        self.assertEqual(out["prompt"], "keep")

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it, verify it fails.**

Run: `cd eval/langfuse && python3 -m unittest tests.test_redact -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'enrich_redact'`.

- [ ] **Step 3: Implement redaction.**

```python
# eval/langfuse/enrich_redact.py
"""Single egress gate: mask secrets/PII and drop identity keys before any Langfuse POST."""
import re

_PATTERNS = [
    re.compile(r"(?i)sk-ant-[a-z0-9-]{20,}"),
    re.compile(r"(?i)sk-lf-[a-z0-9-]{8,}"),
    re.compile(r"(?i)pk-lf-[a-z0-9-]{8,}"),
    re.compile(r"(?i)sk-[a-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)gh[pousr]_[a-z0-9]{20,}"),
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    re.compile(r"\+33[.\s-]?[0-9](?:[.\s-]?[0-9]){8}"),
    re.compile(r"(?i)CANARY-[A-Z0-9-]+"),
]
_MASK = "****REDACTED-SECRET****"

IDENTITY_PII_KEYS = frozenset({
    "user.email", "user.id", "user.account_id", "user.account_uuid", "organization.id",
})

def redact(value):
    if isinstance(value, str):
        out = value
        for pat in _PATTERNS:
            out = pat.sub(_MASK, out)
        return out
    if isinstance(value, dict):
        return {k: redact(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    return value

def strip_identity(attrs: dict) -> dict:
    return {k: v for k, v in attrs.items() if k not in IDENTITY_PII_KEYS}
```

- [ ] **Step 4: Run it, verify it passes.**

Run: `cd eval/langfuse && python3 -m unittest tests.test_redact -v`
Expected: PASS (3 tests). Note `REDACTED` substring is present because `_MASK` contains it.

- [ ] **Step 5: Commit.**

```bash
git add eval/langfuse/enrich_redact.py eval/langfuse/tests/test_redact.py
git commit -m "feat(langfuse): M3 redaction egress gate + identity-PII drop (AI-182)"
```

---

## Task 5: Routing — records → observation updates

> **POSTURE AMENDMENT (2026-06-26): reduce surface + fail-closed; completion via `assistant_response`.** The code block below predates the posture decision and must be adjusted: (1) DROP raw request `messages` and `tool_input`/`tool_output` — they do **not** egress. Route: `user_prompt`→interaction-obs `input` ← prompt; `api_request`→generation `cost_usd` (by `request_id`); **`assistant_response`→same generation `output` ← `response`** (clean field, by `request_id`); `tool_result`→tool `name` ← `tool_name` only. (2) Run every routed content value through the Task-4 gate `fail_closed(...)` (which internally `redact()`s; use `strip_identity` when passing a dict) before it enters an `ObservationUpdate`. (3) Tag each `ObservationUpdate` with `kind` (`generation` vs `span`) so Task 6 emits `generation-update` vs `span-update`. (4) The Task-2 fixture lacks an `assistant_response` record — add one (synthetic `response`) so routing is tested. Add tests for: raw fields NOT egressed; a fail-closed PEM in a prompt is dropped; `assistant_response`→generation `output` by request_id.

**Files:**
- Create: `eval/langfuse/enrich_route.py`
- Test: `eval/langfuse/tests/test_route.py`

**Interfaces:**
- Consumes: `LogRecord` (Task 3), `redact`/`strip_identity` (Task 4).
- Produces: `@dataclass ObservationUpdate(obs_id: str, fields: dict)` and `def build_updates(records: list, request_id_to_obs: dict[str,str]) -> list[ObservationUpdate]`. `request_id_to_obs` maps `api_request.request_id` → generation observation id (built in Task 6). `user_prompt` produces an update whose `obs_id` is the interaction span_id with `{"input": <prompt>}`; `api_request` produces an update on the generation obs with `{"output": ..., "costDetails": {"total": cost_usd}}`; `tool_result` produces an update on the tool span_id with `{"name": tool_name, "output": ..., "input": tool_args}`.

- [ ] **Step 1: Write the failing test.**

```python
# eval/langfuse/tests/test_route.py
import unittest
from enrich_parse import LogRecord
from enrich_route import build_updates

class TestRoute(unittest.TestCase):
    def test_user_prompt_to_interaction_input(self):
        recs = [LogRecord("t"*32, "iface000000000aa", "user_prompt", {"prompt": "hello"})]
        ups = build_updates(recs, {})
        self.assertEqual(ups[0].obs_id, "iface000000000aa")
        self.assertEqual(ups[0].fields["input"], "hello")

    def test_api_request_routes_to_generation_by_request_id(self):
        recs = [LogRecord("t"*32, "rootspan00000000", "api_request",
                          {"request_id": "req_X", "cost_usd": 0.05})]
        ups = build_updates(recs, {"req_X": "gen_obs_id_0001"})
        u = next(u for u in ups if u.obs_id == "gen_obs_id_0001")
        self.assertAlmostEqual(u.fields["costDetails"]["total"], 0.05)

    def test_secret_in_prompt_is_redacted(self):
        recs = [LogRecord("t"*32, "iface000000000aa", "user_prompt",
                          {"prompt": "leak sk-ant-FAKE0123456789abcdef0123"})]
        ups = build_updates(recs, {})
        self.assertNotIn("sk-ant-FAKE0123456789abcdef0123", ups[0].fields["input"])

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it, verify it fails.**

Run: `cd eval/langfuse && python3 -m unittest tests.test_route -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'enrich_route'`.

- [ ] **Step 3: Implement routing.**

```python
# eval/langfuse/enrich_route.py
"""Route content log records to Langfuse observation updates. Redaction applied here."""
from dataclasses import dataclass
from enrich_redact import redact

@dataclass
class ObservationUpdate:
    obs_id: str
    fields: dict

def build_updates(records: list, request_id_to_obs: dict) -> list:
    updates = []
    for r in records:
        if r.event_name == "user_prompt":
            updates.append(ObservationUpdate(r.span_id, {"input": redact(r.attrs.get("prompt"))}))
        elif r.event_name == "api_request":
            obs = request_id_to_obs.get(r.attrs.get("request_id"))
            if not obs:
                continue  # unmapped request: skip, don't guess
            fields = {}
            if r.attrs.get("cost_usd") is not None:
                fields["costDetails"] = {"total": r.attrs["cost_usd"]}
            if r.attrs.get("completion") is not None:        # present under RAW_API_BODIES
                fields["output"] = redact(r.attrs["completion"])
            if r.attrs.get("messages") is not None:
                fields["input"] = redact(r.attrs["messages"])
            if fields:
                updates.append(ObservationUpdate(obs, fields))
        elif r.event_name == "tool_result":
            fields = {"name": r.attrs.get("tool_name")}
            if r.attrs.get("tool_input") is not None:
                fields["input"] = redact(r.attrs["tool_input"])
            if r.attrs.get("tool_output") is not None:
                fields["output"] = redact(r.attrs["tool_output"])
            updates.append(ObservationUpdate(r.span_id, fields))
    return updates
```

- [ ] **Step 4: Run it, verify it passes.**

Run: `cd eval/langfuse && python3 -m unittest tests.test_route -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit.**

```bash
git add eval/langfuse/enrich_route.py eval/langfuse/tests/test_route.py
git commit -m "feat(langfuse): M3 routing of log content to observation updates (AI-182)"
```

---

## Task 6: Langfuse client (request_id index + ingestion POST)

**Files:**
- Create: `eval/langfuse/enrich_langfuse.py`
- Test: `eval/langfuse/tests/test_langfuse.py`

**Interfaces:**
- Consumes: `ObservationUpdate` (Task 5).
- Produces: `def build_request_id_index(base, auth, trace_id) -> dict[str,str]` (GET observations, map `metadata.request_id` → generation id — exact metadata path from Task 1 Step 2) and `def post_updates(base, auth, updates: list) -> dict` (POST `observation-update` batch — exact event type from Task 1 Step 1) and `def ingestion_body(updates) -> dict`.

- [ ] **Step 1: Write the failing test for the pure body builder (no network).**

```python
# eval/langfuse/tests/test_langfuse.py
import unittest
from enrich_route import ObservationUpdate
from enrich_langfuse import ingestion_body

class TestLangfuse(unittest.TestCase):
    def test_ingestion_body_shape(self):
        ups = [ObservationUpdate("obs1", {"output": "hi"})]
        body = ingestion_body(ups)
        ev = body["batch"][0]
        self.assertEqual(ev["type"], "observation-update")
        self.assertEqual(ev["body"]["id"], "obs1")
        self.assertEqual(ev["body"]["output"], "hi")
        self.assertIn("id", ev)         # event id present
        self.assertIn("timestamp", ev)  # timestamp present

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it, verify it fails.**

Run: `cd eval/langfuse && python3 -m unittest tests.test_langfuse -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'enrich_langfuse'`.

- [ ] **Step 3: Implement the client.** (Use the event type + metadata path confirmed in Task 1; below assumes `observation-update` and `metadata.attributes.request_id` — adjust to the contract notes.)

```python
# eval/langfuse/enrich_langfuse.py
"""Langfuse REST: build the request_id->generation index and POST observation updates."""
import json, urllib.request

def _get(base, auth, path):
    req = urllib.request.Request(base + path, headers={"Authorization": auth})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)

def build_request_id_index(base, auth, trace_id) -> dict:
    data = _get(base, auth, f"/api/public/observations?traceId={trace_id}")
    index = {}
    for o in data.get("data", []):
        if o.get("type") != "GENERATION":
            continue
        meta = o.get("metadata") or {}
        rid = meta.get("request_id") or (meta.get("attributes") or {}).get("request_id") \
            or meta.get("gen_ai.response.id")
        if rid:
            index[rid] = o["id"]
    return index

def ingestion_body(updates: list) -> dict:
    batch = []
    for i, u in enumerate(updates):
        batch.append({
            "id": f"m3-{i}-{u.obs_id}",
            "type": "observation-update",
            "timestamp": "2026-06-25T00:00:00Z",   # any valid ISO ts; ingestion needs it present
            "body": {"id": u.obs_id, **u.fields},
        })
    return {"batch": batch}

def post_updates(base, auth, updates: list) -> dict:
    body = json.dumps(ingestion_body(updates)).encode("utf-8")
    req = urllib.request.Request(
        base + "/api/public/ingestion", data=body, method="POST",
        headers={"Authorization": auth, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)
```

- [ ] **Step 4: Run it, verify it passes.**

Run: `cd eval/langfuse && python3 -m unittest tests.test_langfuse -v`
Expected: PASS.

- [ ] **Step 5: Commit.**

```bash
git add eval/langfuse/enrich_langfuse.py eval/langfuse/tests/test_langfuse.py
git commit -m "feat(langfuse): M3 Langfuse client (request_id index + ingestion POST) (AI-182)"
```

---

## Task 7: CLI orchestration + round-trip integration

**Files:**
- Create: `eval/langfuse/enrich.py`
- Create: `eval/langfuse/tests/run-roundtrip.sh`

**Interfaces:**
- Consumes: all prior modules.
- Produces: `enrich.py --run <jsonl> [--trace <id>]` CLI; composes Basic auth from `~/second-brain/.secrets/langfuse.env` like `run-collector.sh`.

- [ ] **Step 1: Implement the CLI.**

```python
# eval/langfuse/enrich.py
"""Post-run enricher: read Collector log JSONL, redact, PATCH Langfuse observations."""
import argparse, base64, os, sys
from enrich_parse import parse_jsonl
from enrich_route import build_updates
from enrich_langfuse import build_request_id_index, post_updates

def _load_auth():
    env = os.path.expanduser("~/second-brain/.secrets/langfuse.env")
    vals = {}
    with open(env) as fh:
        for line in fh:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                vals[k] = v.strip().strip('"').strip("'")
    base = vals["LANGFUSE_BASE_URL"]
    if not base.startswith("http"):
        base = "https://" + base
    base = base.rstrip("/")
    raw = f"{vals['LANGFUSE_PUBLIC_KEY']}:{vals['LANGFUSE_SECRET_KEY']}".encode()
    return base, "Basic " + base64.b64encode(raw).decode()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True, help="path to Collector log JSONL")
    args = ap.parse_args()
    base, auth = _load_auth()
    records = parse_jsonl(args.run)
    trace_ids = {r.trace_id for r in records if r.trace_id}
    total = 0
    for tid in trace_ids:
        idx = build_request_id_index(base, auth, tid)
        trace_recs = [r for r in records if r.trace_id == tid]
        updates = build_updates(trace_recs, idx)
        if not updates:
            continue
        resp = post_updates(base, auth, updates)
        errs = resp.get("errors") or []
        if errs:
            print(f"trace {tid}: {len(errs)} ingestion errors", file=sys.stderr)
        total += len(updates)
        print(f"trace {tid}: {len(updates)} observation updates posted")
    print(f"done: {total} updates across {len(trace_ids)} trace(s)")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Write the round-trip integration script.**

```bash
# eval/langfuse/tests/run-roundtrip.sh
#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$HERE"
[ -s .logs/claude-logs.jsonl ] || { echo "no captured logs; run a traced session first" >&2; exit 1; }
python3 enrich.py --run .logs/claude-logs.jsonl
set -a; source ~/second-brain/.secrets/langfuse.env; set +a
base="${LANGFUSE_BASE_URL}"; [[ "$base" =~ ^https?:// ]] || base="https://$base"; base="${base%/}"
TID="$(python3 -c 'import sys,json;from enrich_parse import parse_jsonl;rs=parse_jsonl(".logs/claude-logs.jsonl");print(next(r.trace_id for r in rs if r.trace_id))')"
echo "verifying trace $TID has content + cost..."
curl -s -u "${LANGFUSE_PUBLIC_KEY}:${LANGFUSE_SECRET_KEY}" "$base/api/public/traces/$TID" \
  | jq -e '[.observations[]|select(.type=="GENERATION")]|any(.output != null)' >/dev/null \
  && echo "PASS: generation output present" || { echo "FAIL: no generation output"; exit 1; }
```

- [ ] **Step 3: Run unit suite + round-trip.**

Run: `cd eval/langfuse && python3 -m unittest discover -s tests -v && bash tests/run-roundtrip.sh`
Expected: all unit tests PASS; round-trip prints `PASS: generation output present`. Confirm in the Langfuse UI that a generation shows input/output and Opus cost ≠ 0.

- [ ] **Step 4: Commit.**

```bash
git add eval/langfuse/enrich.py eval/langfuse/tests/run-roundtrip.sh
git commit -m "feat(langfuse): M3 enricher CLI + round-trip integration (AI-182)"
```

---

## Task 8: Docs + reduced-surface posture

> **POSTURE AMENDMENT (2026-06-26):** do NOT enable `OTEL_LOG_RAW_API_BODIES` — the reduce-surface posture keeps raw bodies off egress.

**Files:**
- Modify: `eval/langfuse/enable-claude-telemetry.sh` (keep `OTEL_LOG_RAW_API_BODIES` **commented**; rewrite its comment to state raw bodies are deliberately OFF under the reduce-surface posture)
- Modify: `eval/langfuse/README.md` (M3 row → Built; document `enrich.py` + the reduce-surface + fail-closed egress posture)

- [ ] **Step 1: Confirm raw bodies stay OFF.** Ensure `OTEL_LOG_RAW_API_BODIES=1` remains commented in `enable-claude-telemetry.sh`; rewrite its comment to explain raw bodies are excluded from egress (reduce-surface posture) and the enricher sends only prompt/completion/tool-name/cost.

- [ ] **Step 2: Update README.** Flip the M3 milestone row to **Built**; add a "Content enrichment" subsection describing the post-run `enrich.py` flow, the reduce-surface + fail-closed posture, and that redaction is enforced in Python before egress.

- [ ] **Step 3: Run the full check + commit.**

```bash
cd eval/langfuse && python3 -m unittest discover -s tests
git add eval/langfuse/enable-claude-telemetry.sh eval/langfuse/README.md
git commit -m "docs(langfuse): M3 enricher docs + reduce-surface posture (AI-182)"
```

---

## Self-Review

**Spec coverage:**
- §2 criterion 1 (generation input/output) → Task 5 (`api_request` routing) + Task 7. ✓
- §2 criterion 2 (Opus cost via `cost_usd`) → Task 5 `costDetails` + Task 1 contract. ✓
- §2 criterion 3 (tool name/input/output) → Task 5 `tool_result` routing. ✓
- §2 criterion 4 (no secret/PII leak) → Task 4 canary + identity-drop, applied in Task 5. ✓
- §4 architecture (file exporter, local file, post-run) → Task 2, Task 7. ✓
- §5 routing table → Task 5. ✓
- §6 redaction single gate → Task 4 + applied in Task 5/7. ✓
- §7 error handling (missing obs skip, idempotent, retry) → Task 5 skip-on-unmapped; **retry/backoff not yet a task** — acceptable for a lab tool; first version surfaces ingestion errors to stderr (Task 7). Note for hardening.
- §8 testing (fixture, canary, round-trip) → Tasks 3/4/5 unit + Task 7 round-trip. ✓
- §10 open items → Task 1 spike resolves all four. ✓

**Placeholder scan:** Task 1 resolves the two API-shape unknowns with concrete curls; later tasks reference the confirmed contract. The `completion`/`messages`/`tool_input`/`tool_output` attr names in Task 5 depend on the actual `OTEL_LOG_RAW_API_BODIES` payload — Task 2 Step 4 captures it, and the implementer adjusts the attr keys to the observed names (flagged inline).

**Type consistency:** `LogRecord` (parse) → consumed by `build_updates` (route); `ObservationUpdate(obs_id, fields)` produced by route, consumed by `ingestion_body`/`post_updates`; `request_id_to_obs` produced by `build_request_id_index`, consumed by `build_updates`. Names align across tasks. ✓

**Known follow-ups (not blocking):** retry/backoff on ingestion; the exact raw-body attribute key names (resolved at Task 2 capture); fail-closed allowlist (separate hardening milestone).
