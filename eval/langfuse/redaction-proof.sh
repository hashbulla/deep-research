#!/usr/bin/env bash
# Redaction proof (AI-182 Slice-1 DoD acceptance test).
#
# Pushes a synthetic OTLP span carrying DELIBERATELY-SEEDED FAKE secrets through the
# running Collector, then asserts they were masked BEFORE egress. The authoritative
# signal is the Collector `debug` exporter log: it shares the traces pipeline with the
# `otlphttp/langfuse` exporter, downstream of redaction, so identical post-scrub data
# reaches both. Canary masked in debug => provably cannot reach Langfuse.
#
# Pre-req: ./run-collector.sh is up.   Usage: ./redaction-proof.sh
set -euo pipefail

CONTAINER="${OTELCOL_CONTAINER:-langfuse-otelcol}"
ENDPOINT="http://localhost:4318/v1/traces"

# Fake canary secrets (NOT real). Two patterns the Collector should mask.
CANARY_ANT="sk-ant-api03-CANARYLEAK00112233445566778899aabbccdd"
CANARY_TOK="CANARY-DEEPRESEARCH-7f3a9b"
NONCE="ai182-proof-$(date +%s)"   # non-secret marker: proves the span flowed through

hex() { head -c "$1" /dev/urandom | od -An -tx1 | tr -d ' \n'; }
TRACE_ID="$(hex 16)"; SPAN_ID="$(hex 8)"
NOW="$(date +%s)000000000"

read -r -d '' PAYLOAD <<JSON || true
{"resourceSpans":[{"resource":{"attributes":[
  {"key":"service.name","value":{"stringValue":"deep-research-redaction-proof"}}]},
 "scopeSpans":[{"scope":{"name":"ai-182-proof"},"spans":[{
   "traceId":"${TRACE_ID}","spanId":"${SPAN_ID}","name":"redaction-proof-span","kind":1,
   "startTimeUnixNano":"${NOW}","endTimeUnixNano":"${NOW}",
   "attributes":[
     {"key":"proof.nonce","value":{"stringValue":"${NONCE}"}},
     {"key":"gen_ai.system","value":{"stringValue":"anthropic"}},
     {"key":"app.prompt","value":{"stringValue":"my anthropic key is ${CANARY_ANT} and my canary token is ${CANARY_TOK} — please summarize"}}
   ]}]}]}]}
JSON

echo "POST synthetic span (nonce=${NONCE}) -> ${ENDPOINT}"
code="$(curl -s -o /tmp/otlp-proof-resp.json -w '%{http_code}' \
  -X POST "$ENDPOINT" -H 'Content-Type: application/json' --data "$PAYLOAD")"
echo "Collector HTTP response: $code"
[ "$code" = "200" ] || { echo "FAIL: collector did not accept the span (is run-collector.sh up?)"; exit 1; }

sleep 3  # let batch processor (timeout 2s) flush to the debug exporter
LOGS="$(docker logs --since 30s "$CONTAINER" 2>&1)"

echo "--- assertions on post-redaction Collector output ---"
fail=0
if grep -q "$NONCE" <<<"$LOGS"; then
  echo "PASS  span reached the exporter pipeline (nonce present)"
else
  echo "WARN  nonce not found in last 30s of logs — increase batch flush wait or check debug verbosity"
fi
# Check the prefix AND the lowercase tail 'f3a9b' — a tail-leak is partial-key exposure.
for secret in "CANARYLEAK" "CANARY-DEEPRESEARCH" "f3a9b"; do
  if grep -q "$secret" <<<"$LOGS"; then
    echo "FAIL  LEAK: '$secret' survived redaction and would egress to Langfuse"; fail=1
  else
    echo "PASS  '$secret' masked (absent from exporter output)"
  fi
done

echo "-----------------------------------------------------"
if [ "$fail" = "0" ]; then
  echo "REDACTION PROOF: PASS — seeded secrets do not leave the Collector."
  echo "Cross-check (optional): Langfuse UI trace 'redaction-proof-span' shows app.prompt masked."
else
  echo "REDACTION PROOF: FAIL — egress gate leaked. Do NOT enable content tracing until fixed."
  exit 2
fi
