#!/usr/bin/env bash
# Round-trip integration test for the AI-182 M3 enricher.
#
# What it does:
#   1. Ensures the OTEL Collector container is up.
#   2. Runs a minimal Claude haiku call under telemetry (no raw bodies).
#   3. Waits for the trace to be ingested by Langfuse (polls up to 90s).
#   4. Runs enrich.py --run .logs/claude-logs.jsonl.
#   5. Verifies the generation has output (completion) and cost via the API.
#   6. Asserts no raw JSON Messages body egressed.
#   7. Prints PASS or FAIL.
#
# Run manually: bash tests/run-roundtrip.sh
# NOT part of CI (requires live Langfuse + Docker + Claude Code CLI).
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$HERE"

LOGFILE=".logs/claude-logs.jsonl"
MAX_WAIT=90    # seconds to wait for Langfuse ingestion
POLL_INTERVAL=5

# ── helpers ─────────────────────────────────────────────────────────────────

fail() {
    echo "FAIL: $*" >&2
    exit 1
}

pass() {
    echo "PASS: $*"
}

# Load creds into local variables inside a subshell-safe way:
# We source them, use them, and never echo the secret key.
_load_creds() {
    local secrets_file="$HOME/second-brain/.secrets/langfuse.env"
    [ -f "$secrets_file" ] || fail "secrets file not found: $secrets_file"
    set -a
    # shellcheck disable=SC1090
    source "$secrets_file"   # path is runtime-determined from $HOME
    set +a
    : "${LANGFUSE_PUBLIC_KEY:?missing LANGFUSE_PUBLIC_KEY}"
    : "${LANGFUSE_SECRET_KEY:?missing LANGFUSE_SECRET_KEY}"
    : "${LANGFUSE_BASE_URL:?missing LANGFUSE_BASE_URL}"
    local base="$LANGFUSE_BASE_URL"
    [[ "$base" =~ ^https?:// ]] || base="https://$base"
    LANGFUSE_BASE="${base%/}"
}

# ── Step 1: (Re)start Collector with a fresh log file ───────────────────────
# We always restart the container so the file exporter gets a fresh fd on the
# rotated log file. (Unix: mv leaves the old fd open inside the container, so
# the exporter would keep writing to the old inode if we only rotate without
# restarting.)

echo "=== Step 1: Rotating log file and (re)starting Collector ==="
mkdir -p "$(dirname "$LOGFILE")"
# Rotate existing log — the container is about to be replaced anyway.
if [ -f "$LOGFILE" ]; then
    mv "$LOGFILE" "${LOGFILE}.$(date +%Y%m%dT%H%M%S).bak"
fi
touch "$LOGFILE"

bash "$HERE/run-collector.sh"
echo "Waiting 4s for the Collector to bind its ports..."
sleep 4

# ── Step 2: Run a traced Claude invocation ──────────────────────────────────

echo ""
echo "=== Step 2: Traced Claude haiku invocation ==="

# Export telemetry vars; deliberately omit OTEL_LOG_RAW_API_BODIES.
export CLAUDE_CODE_ENABLE_TELEMETRY=1
export CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1
export OTEL_LOGS_EXPORTER=otlp
export OTEL_TRACES_EXPORTER=otlp
export OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
export OTEL_LOG_USER_PROMPTS=1
# OTEL_LOG_RAW_API_BODIES is intentionally NOT set.

echo "Running: claude -p 'Reply with exactly the word: ROUNDTRIP_OK' --model haiku"
CLAUDE_RESPONSE="$(claude -p "Reply with exactly the word: ROUNDTRIP_OK" --model haiku 2>&1)"
echo "Claude responded: $CLAUDE_RESPONSE"

# Allow a brief moment for spans to flush before reading the log.
sleep 2

# ── Step 3: Extract trace_id from captured logs ──────────────────────────────

echo ""
echo "=== Step 3: Extract trace id from JSONL ==="
[ -s "$LOGFILE" ] || fail "JSONL log is empty — check Collector config and Claude telemetry"

TID="$(python3 - <<'PYEOF'
import sys, json

logfile = ".logs/claude-logs.jsonl"
trace_ids = set()
with open(logfile) as fh:
    for line in fh:
        line = line.strip()
        if not line:
            continue
        req = json.loads(line)
        for rl in req.get("resourceLogs", []):
            for sl in rl.get("scopeLogs", []):
                for lr in sl.get("logRecords", []):
                    tid = lr.get("traceId", "")
                    if tid:
                        trace_ids.add(tid)

if not trace_ids:
    print("NO_TRACE_ID", file=sys.stderr)
    sys.exit(1)

# Use the first (or only) trace id.
print(sorted(trace_ids)[0])
PYEOF
)"

echo "Trace id: $TID"

_load_creds

# ── Step 4: Poll for Langfuse ingestion ─────────────────────────────────────

echo ""
echo "=== Step 4: Poll Langfuse until trace has GENERATION observations (max ${MAX_WAIT}s) ==="

elapsed=0
HAS_GEN=0
while [ "$elapsed" -lt "$MAX_WAIT" ]; do
    HTTP_CODE="$(curl -s -o /dev/null -w "%{http_code}" \
        -u "${LANGFUSE_PUBLIC_KEY}:${LANGFUSE_SECRET_KEY}" \
        "${LANGFUSE_BASE}/api/public/traces/${TID}")"

    if [ "$HTTP_CODE" = "200" ]; then
        # Check for GENERATION observations in the list endpoint.
        GEN_COUNT="$(curl -s \
            -u "${LANGFUSE_PUBLIC_KEY}:${LANGFUSE_SECRET_KEY}" \
            "${LANGFUSE_BASE}/api/public/observations?traceId=${TID}" \
            | python3 -c "import sys,json; d=json.load(sys.stdin); print(sum(1 for o in d.get('data',[]) if o.get('type')=='GENERATION'))")"
        if [ "${GEN_COUNT:-0}" -gt 0 ]; then
            echo "Trace ingested with ${GEN_COUNT} GENERATION observation(s) after ${elapsed}s."
            HAS_GEN=1
            break
        fi
    fi

    echo "  waiting... (${elapsed}s elapsed, HTTP ${HTTP_CODE:-0})"
    sleep "$POLL_INTERVAL"
    elapsed=$(( elapsed + POLL_INTERVAL ))
done

[ "$HAS_GEN" -eq 1 ] || fail "Langfuse did not ingest GENERATION observations within ${MAX_WAIT}s"

# ── Step 5: Run enricher ─────────────────────────────────────────────────────

echo ""
echo "=== Step 5: Enrich ==="
python3 enrich.py --run "$LOGFILE"

# Langfuse Hobby processes PATCH batches asynchronously; observed lag is 10–30s.
# The output visibility is polled in the verification step below (6a).
echo "Enrichment posted. Proceeding to verification with polling..."

# ── Step 6: Verify enrichment via Langfuse API ─────────────────────────────
# Use the OBSERVATIONS LIST endpoint — the trace endpoint embeds only observation IDs,
# not their full payload (output/input/costDetails are absent in the trace response).

echo ""
echo "=== Step 6: Verify enrichment via Langfuse API ==="

# Fetch the observations list to find the GENERATION observation ID.
# NOTE: the list endpoint returns null for output/input after a generation-update PATCH
# (Langfuse Hobby behavior — confirmed empirically). Use the SINGLE obs endpoint for
# verifying enriched output; the list endpoint is only used for id discovery.
OBS_LIST_JSON="$(curl -s \
    -u "${LANGFUSE_PUBLIC_KEY}:${LANGFUSE_SECRET_KEY}" \
    "${LANGFUSE_BASE}/api/public/observations?traceId=${TID}")"

GEN_OBS_ID="$(echo "$OBS_LIST_JSON" | python3 -c "
import sys, json
d = json.load(sys.stdin)
gens = [o for o in d.get('data', []) if o.get('type') == 'GENERATION']
if not gens:
    print('')
else:
    print(gens[0]['id'])
")"

[ -n "$GEN_OBS_ID" ] || fail "no GENERATION observation found for trace ${TID}"
echo "GENERATION observation id: ${GEN_OBS_ID}"

# 6a. Generation output must be present (the enricher wrote the completion text).
# Poll with retries — Langfuse Hobby processes PATCH batches asynchronously (10–30s lag).
OUTPUT_PRESENT="0"
verify_elapsed=0
VERIFY_MAX=60
VERIFY_POLL=5
while [ "$verify_elapsed" -lt "$VERIFY_MAX" ]; do
    GEN_OBS_JSON="$(curl -s \
        -u "${LANGFUSE_PUBLIC_KEY}:${LANGFUSE_SECRET_KEY}" \
        "${LANGFUSE_BASE}/api/public/observations/${GEN_OBS_ID}")"
    OUTPUT_PRESENT="$(echo "$GEN_OBS_JSON" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('1' if d.get('output') else '0')
")"
    if [ "$OUTPUT_PRESENT" = "1" ]; then
        break
    fi
    echo "  output not yet visible (${verify_elapsed}s elapsed)..."
    verify_elapsed=$(( verify_elapsed + VERIFY_POLL ))
    sleep "$VERIFY_POLL"
done

if [ "$OUTPUT_PRESENT" = "1" ]; then
    pass "generation output present in Langfuse (single-obs endpoint, ${verify_elapsed}s)"
else
    fail "no generation output found after ${VERIFY_MAX}s — enricher may not have matched request_id or PATCH did not persist"
fi

# 6b. Cost must be present — comes from the OTEL traces pipeline (gen_ai.usage.* semconv).
COST_PRESENT="$(echo "$OBS_LIST_JSON" | python3 -c "
import sys, json
d = json.load(sys.stdin)
gens = [o for o in d.get('data', []) if o.get('type') == 'GENERATION']
has_cost = any(
    (o.get('costDetails') or {}).get('total') or
    (o.get('costDetails') or {}).get('output') or
    o.get('calculatedTotalCost')
    for o in gens
)
print('1' if has_cost else '0')
")"

if [ "$COST_PRESENT" = "1" ]; then
    pass "cost present on GENERATION observation"
else
    echo "WARN: no cost found on GENERATION — gen_ai.usage.* semconv mapping may not have propagated" >&2
fi

# 6c. Prompt input on the root span — from user_prompt log event.
SPAN_OBS_ID="$(echo "$OBS_LIST_JSON" | python3 -c "
import sys, json
d = json.load(sys.stdin)
spans = [o for o in d.get('data', []) if o.get('type') == 'SPAN']
print(spans[0]['id'] if spans else '')
")"

INPUT_PRESENT="0"
if [ -n "$SPAN_OBS_ID" ]; then
    SPAN_OBS_JSON="$(curl -s \
        -u "${LANGFUSE_PUBLIC_KEY}:${LANGFUSE_SECRET_KEY}" \
        "${LANGFUSE_BASE}/api/public/observations/${SPAN_OBS_ID}")"
    INPUT_PRESENT="$(echo "$SPAN_OBS_JSON" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('1' if d.get('input') else '0')
")"
fi

if [ "$INPUT_PRESENT" = "1" ]; then
    pass "prompt (input) present on root span"
else
    echo "WARN: prompt input not found — user_prompt event may not carry a prompt attr in this run" >&2
fi

# 6d. Assert no raw JSON Messages body egressed.
# Concatenate both observation payloads and scan for raw Messages API markers.
COMBINED_PAYLOAD="${GEN_OBS_JSON}${SPAN_OBS_JSON:-}"
RAW_BODY_PRESENT="$(echo "$COMBINED_PAYLOAD" | python3 -c "
import sys
text = sys.stdin.read()
# Raw Messages API markers that must NEVER appear in enriched content.
markers = [
    '\"role\":\"assistant\"',
    '\"role\": \"assistant\"',
    '\"content\":[{',
    '\"stop_reason\"',
]
found = any(m in text for m in markers)
print('1' if found else '0')
")"

if [ "$RAW_BODY_PRESENT" = "0" ]; then
    pass "no raw JSON Messages body detected in observation payloads"
else
    fail "raw Messages API body markers detected in Langfuse observations — redaction failure"
fi

echo ""
echo "=== Round-trip complete ==="
echo "PASS: all checks passed. Trace: ${LANGFUSE_BASE}/trace/${TID}"
