#!/usr/bin/env bash
# run_ci_judges.sh — CI runner for the LLM-judged harness layers (2: entailment).
#
# Maintainer infrastructure ONLY (decision D-4): consumers never need a key.
# Without ANTHROPIC_API_KEY this script SKIPs with exit 0 — the deterministic
# layer (verify_gates.py, a separate CI step) has already gated the build.
# With the secret, it judges every claim of the example fixture against its
# cited source titles using the versioned layer-2 prompt, and fails the build
# when the entailment pass-rate drops below the threshold.
#
# Judge model is pinned and intentionally different from the documented
# synthesis default (cross-model decorrelation, AI-124 layer 3 rationale).

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

SOURCES="${1:-examples/eu-ai-act-2026/research-sources.json}"
EVIDENCE="${2:-examples/eu-ai-act-2026/research-evidence.json}"
THRESHOLD="${ENTAILMENT_THRESHOLD:-0.95}"
JUDGE_MODEL="${JUDGE_MODEL:-claude-sonnet-4-6}"
PROMPT_FILE="scripts/eval_harness/judge_prompts/entailment.md"

if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  echo "SKIP: ANTHROPIC_API_KEY absent — LLM judge layers not run (deterministic layer already gates the build)."
  exit 0
fi

command -v jq >/dev/null || { echo "FAIL: jq required" >&2; exit 1; }
command -v curl >/dev/null || { echo "FAIL: curl required" >&2; exit 1; }
[ -f "$PROMPT_FILE" ] || { echo "FAIL: $PROMPT_FILE missing" >&2; exit 1; }

judge_prompt="$(cat "$PROMPT_FILE")"
total=0
passed=0

claim_count="$(jq 'length' "$EVIDENCE")"
for i in $(seq 0 $((claim_count - 1))); do
  claim="$(jq -r ".[$i].claim_text" "$EVIDENCE")"
  # Span proxy in CI: titles + notes of the supporting sources (the example
  # fixture carries no full snapshots). Runtime judging uses real spans.
  spans="$(jq -r --argjson idx "$i" '
    (.[$idx].supporting_source_ids) as $ids
    | $ids | join(",")' "$EVIDENCE")"
  span_text="$(jq -r --arg ids "$spans" '
    [.[] | select(.id as $i | ($ids | split(",")) | index($i))
     | "- \(.title) (\(.publisher), \(.published_date // "n.d.")): \(.notes // "")"]
    | join("\n")' "$SOURCES")"

  body="$(jq -n \
    --arg model "$JUDGE_MODEL" \
    --arg system "$judge_prompt" \
    --arg user "CLAIM: ${claim}

SPAN(S):
${span_text}" \
    '{model: $model, max_tokens: 512,
      system: $system,
      messages: [{role: "user", content: $user}]}')"

  response="$(curl -s https://api.anthropic.com/v1/messages \
    -H "Content-Type: application/json" \
    -H "x-api-key: ${ANTHROPIC_API_KEY}" \
    -H "anthropic-version: 2023-06-01" \
    -d "$body")"

  verdict="$(echo "$response" | jq -r '
    [.content[]? | select(.type == "text") | .text] | join("")
    | capture("\"verdict\"\\s*:\\s*\"(?<v>[A-Z_]+)\"").v // "PARSE_ERROR"')"

  total=$((total + 1))
  if [ "$verdict" = "ENTAILED" ]; then
    passed=$((passed + 1))
  else
    echo "layer-2 NOT_ENTAILED: claim $i — $(echo "$claim" | head -c 100)…"
  fi
done

rate="$(python3 -c "print(round(${passed}/${total}, 4))")"
echo "layer-2 entailment pass-rate: ${rate} (${passed}/${total}; threshold ${THRESHOLD}; judge ${JUDGE_MODEL})"

ok="$(python3 -c "print(1 if ${rate} >= ${THRESHOLD} else 0)")"
if [ "$ok" -ne 1 ]; then
  echo "FAIL: entailment pass-rate below threshold" >&2
  exit 1
fi
echo "OK: LLM judge layers passed."
exit 0
