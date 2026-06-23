#!/usr/bin/env bash
# Drives verify_gates.py over the OSINT/SOCMINT fixtures and asserts each
# gate fires (or stays silent) as designed. CI-only — never invoked by the
# skill at runtime.
set -euo pipefail
cd "$(dirname "$0")/.."
F=tests/fixtures/osint
G=(python3 scripts/verify_gates.py check-artifacts --length short)
fail=0

assert_contains() { # <label> <output> <needle>
  if ! grep -qF "$3" <<<"$2"; then echo "MISS [$1]: expected '$3'"; fail=1; fi
}
assert_absent() {
  if grep -qF "$3" <<<"$2"; then echo "LEAK [$1]: unexpected '$3'"; fail=1; fi
}

out=$("${G[@]}" --sources $F/bad-tier-map.json --evidence $F/bad-tier-map-evidence.json || true)
assert_contains tier-map "$out" "must map to domain_tier 2, found 1"

out=$("${G[@]}" --sources $F/cap-violation.json --evidence $F/socmint-evidence.json --max-stealth 2 || true)
assert_contains cap "$out" "stealth cap exceeded: 3"

out=$("${G[@]}" --sources $F/bad-status.json --evidence $F/socmint-evidence.json || true)
assert_contains status "$out" "needs retrieval_status in {stealth, robots_overridden}"

out=$("${G[@]}" --sources $F/amplification-sources.json --evidence $F/amplification-evidence.json || true)
assert_contains amp "$out" "B13 amplification masquerade"

out=$("${G[@]}" --sources $F/amplification-sources.json --evidence $F/amplification-cleared-evidence.json || true)
assert_absent amp-cleared "$out" "B13 amplification masquerade"

if [ "$fail" -eq 0 ]; then echo "check-osint-gates: PASS"; else echo "check-osint-gates: FAIL"; exit 1; fi
