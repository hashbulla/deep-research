#!/usr/bin/env bash
# check-newsletter-search.sh
# Exercises scripts/newsletter_search.py (the newsletter-signal conditional
# source helper) against the committed fixture corpus, and validates every
# fixture line against the corpus-record JSON Schema.
#
# Asserts:
#   1. Relevance+recency ranking: "prompt cache" tops the 2026-06-10 item.
#   2. --since filters out items older than the window.
#   3. --bucket restricts results to one bucket.
#   4. Graceful degradation: a missing --corpus dir -> corpus_present:false, exit 0.
#   5. Pure-Python fallback ranker (--ranker python) returns well-formed output.
#   6. Per-line schema validation via ajv (NOT check-schema.sh, whose url-autodetect
#      would misroute corpus records to the sources schema).
#
# Usage: bash tests/check-newsletter-search.sh
# Exits 0 on all-pass, 1 on first failure.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

HELPER="scripts/newsletter_search.py"
CORPUS="tests/fixtures/newsletter-corpus"
SCHEMA="tests/schema/newsletter-corpus-record.schema.json"
FIXTURE="$CORPUS/2026-06.jsonl"

command -v jq >/dev/null      || { echo "FAIL: jq required" >&2; exit 1; }
command -v python3 >/dev/null || { echo "FAIL: python3 required" >&2; exit 1; }
[ -f "$HELPER" ]  || { echo "FAIL: $HELPER not found" >&2; exit 1; }
[ -f "$FIXTURE" ] || { echo "FAIL: $FIXTURE not found" >&2; exit 1; }

fail() { echo "FAIL: $1" >&2; exit 1; }
pass() { echo "ok: $1"; }

# 1. Relevance + recency ranking ------------------------------------------------
out="$(python3 "$HELPER" "prompt cache" --corpus "$CORPUS" --as-of 2026-06-12)"
[ "$(jq -r '.corpus_present' <<<"$out")" = "true" ] || fail "corpus_present should be true"
[ "$(jq -r '.items | length' <<<"$out")" -ge 2 ]    || fail "expected >=2 prompt-cache items"
top_date="$(jq -r '.items[0].date' <<<"$out")"
[ "$top_date" = "2026-06-10" ] || fail "top prompt-cache item should be 2026-06-10, got $top_date"
pass "ranking: 2026-06-10 prompt-cache item ranks first"

# 2. --since window -------------------------------------------------------------
out="$(python3 "$HELPER" "prompt cache" --corpus "$CORPUS" --as-of 2026-06-12 --since 2026-06-01)"
older="$(jq -r '[.items[] | select(.date < "2026-06-01")] | length' <<<"$out")"
[ "$older" = "0" ] || fail "--since 2026-06-01 leaked $older item(s) older than the window"
pass "--since filters out-of-window items"

# 3. --bucket restriction -------------------------------------------------------
out="$(python3 "$HELPER" "gpu scheduling" --corpus "$CORPUS" --as-of 2026-06-12 --bucket platform-ai-sre)"
offbucket="$(jq -r '[.items[] | select(.bucket != "platform-ai-sre")] | length' <<<"$out")"
[ "$offbucket" = "0" ] || fail "--bucket leaked $offbucket off-bucket item(s)"
[ "$(jq -r '.items | length' <<<"$out")" -ge 1 ] || fail "expected >=1 platform-ai-sre item"
pass "--bucket restricts to one bucket"

# 3b. Present corpus, filters exclude everything -> present:true, items:[] ------
out="$(python3 "$HELPER" "prompt cache" --corpus "$CORPUS" --as-of 2026-06-12 --since 2027-01-01)"
[ "$(jq -r '.corpus_present' <<<"$out")" = "true" ] || fail "present corpus filtered empty should stay corpus_present:true"
[ "$(jq -r '.items | length' <<<"$out")" = "0" ]    || fail "far-future --since should yield 0 items"
pass "present-but-filtered-empty keeps corpus_present:true (not a degradation)"

# 4. Graceful degradation -------------------------------------------------------
set +e
out="$(python3 "$HELPER" "anything" --corpus /nonexistent/newsletter-corpus 2>/dev/null)"
rc=$?
set -e
[ "$rc" = "0" ] || fail "missing corpus should exit 0, got $rc"
[ "$(jq -r '.corpus_present' <<<"$out")" = "false" ] || fail "missing corpus -> corpus_present:false"
[ "$(jq -r '.items | length' <<<"$out")" = "0" ]     || fail "missing corpus -> empty items"
pass "graceful degradation on absent corpus"

# 5. Pure-Python fallback ranker ------------------------------------------------
out="$(python3 "$HELPER" "prompt cache" --corpus "$CORPUS" --as-of 2026-06-12 --ranker python)"
[ "$(jq -r '.ranker_used' <<<"$out")" = "python" ] || fail "--ranker python should report ranker_used:python"
[ "$(jq -r '.items | length' <<<"$out")" -ge 1 ]   || fail "python ranker returned no items"
pass "pure-Python fallback ranker works"

# 5b. Malformed date flags fail loud (not silently ignored) ---------------------
set +e
python3 "$HELPER" "x" --corpus "$CORPUS" --since not-a-date >/dev/null 2>&1; rc_since=$?
python3 "$HELPER" "x" --corpus "$CORPUS" --as-of 06/12/2026 >/dev/null 2>&1; rc_asof=$?
python3 "$HELPER" "x" --corpus "$CORPUS" --top -3 >/dev/null 2>&1; rc_top=$?
set -e
[ "$rc_since" -ne 0 ] || fail "malformed --since should exit non-zero"
[ "$rc_asof" -ne 0 ]  || fail "malformed --as-of should exit non-zero"
[ "$rc_top" -ne 0 ]   || fail "negative --top should exit non-zero"
pass "malformed --since/--as-of/--top fail loud"

# 5c. Non-string date in a record degrades gracefully (no traceback) ------------
adhoc="$(mktemp -d)"
printf '%s\n' '{"date": 20260610, "bucket": "ai-engineering", "kind": "top", "headline": "int date", "source": "X", "url": "https://e.com"}' > "$adhoc/bad.jsonl"
set +e
out="$(python3 "$HELPER" "int date" --corpus "$adhoc" --as-of 2026-06-12 2>/dev/null)"; rc_bad=$?
set -e
rm -rf "$adhoc"
[ "$rc_bad" = "0" ] || fail "non-string date should degrade gracefully (exit 0), got $rc_bad"
[ "$(jq -r '.corpus_present' <<<"$out")" = "true" ] || fail "non-string date record should still be present"
pass "non-string date degrades gracefully"

# 6. Per-line schema validation -------------------------------------------------
if ! command -v npx >/dev/null 2>&1; then
  echo "SKIP: npx unavailable — schema validation skipped (CI runs it on Node 20)" >&2
else
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT
  line_no=0
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    line_no=$((line_no + 1))
    printf '%s' "$line" | jq -e '.' >/dev/null || fail "fixture line $line_no is not valid JSON"
    printf '%s' "$line" > "$tmp/rec.json"
    npx -y ajv-cli@5 validate --spec=draft7 -s "$SCHEMA" -d "$tmp/rec.json" >/dev/null \
      || fail "fixture line $line_no failed schema validation"
  done < "$FIXTURE"
  pass "all $line_no fixture lines validate against the schema"
fi

echo "OK: newsletter-search checks passed."
exit 0
