#!/usr/bin/env bash
# check-schema.sh
# Validates JSON artifact file(s) against the appropriate schema under
# tests/schema/. Detects artifact type from the first element's keys:
#   - contains "claim_id"  -> research-evidence.schema.json
#   - contains "url"       -> research-sources.schema.json
# Uses npx ajv-cli (draft-07).
#
# Usage: bash tests/check-schema.sh FILE [FILE...]
# Exits 0 on all-pass, 1 on first validation failure.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

if [ "$#" -lt 1 ]; then
  echo "usage: $0 FILE [FILE...]" >&2
  exit 1
fi

if ! command -v npx >/dev/null 2>&1; then
  echo "FAIL: npx not available (Node.js required to run ajv-cli)" >&2
  exit 1
fi

SOURCES_SCHEMA="tests/schema/research-sources.schema.json"
EVIDENCE_SCHEMA="tests/schema/research-evidence.schema.json"

fail_count=0

for f in "$@"; do
  if [ ! -f "$f" ]; then
    echo "FAIL: $f not found" >&2
    fail_count=$((fail_count + 1))
    continue
  fi

  # Detect schema by inspecting first object's keys.
  schema=""
  if grep -q '"claim_id"' "$f"; then
    schema="$EVIDENCE_SCHEMA"
  elif grep -q '"url"' "$f"; then
    schema="$SOURCES_SCHEMA"
  else
    echo "FAIL: cannot determine schema for $f (neither claim_id nor url found)" >&2
    fail_count=$((fail_count + 1))
    continue
  fi

  echo "Validating $f against $schema"
  if ! npx -y ajv-cli@5 validate --spec=draft7 -s "$schema" -d "$f"; then
    fail_count=$((fail_count + 1))
  fi
done

if [ "$fail_count" -gt 0 ]; then
  echo "FAIL: $fail_count file(s) failed schema validation" >&2
  exit 1
fi
echo "OK: all files passed schema validation."
exit 0
