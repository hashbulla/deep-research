#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
echo "== T1: fake_star_gate is importable and github_rank output unchanged =="

# (a) function is importable and tri-valued contract holds
python3 - <<'PY'
import sys; sys.path.insert(0, "scripts")
from github_rank import fake_star_gate
assert fake_star_gate(1000, 0, 0, 0) is True, "high stars + flat usage must flag"
assert fake_star_gate(1000, 500, 500, 500) is False, "real usage must not flag"
assert fake_star_gate(100, 0, 0, 0) is False, "below 500-star floor never flags"
assert fake_star_gate(1000, None, None, None) is None, "all-usage-absent -> unknown"
assert fake_star_gate(None, 1, 1, 1) is None, "absent stars -> unknown"

# Verify main() guard preserves old all-None-usage semantics:
# old inline code: usage=0 -> flags iff stars>=500. None gate must map to same.
gate_hi = fake_star_gate(1000, None, None, None)
assert gate_hi is None
result_hi = (1000 >= 500) if gate_hi is None else gate_hi
assert result_hi is True, "all-None, stars=1000: old behavior was True (usage=0, 1000>=500)"

gate_lo = fake_star_gate(200, None, None, None)
assert gate_lo is None
result_lo = (200 >= 500) if gate_lo is None else gate_lo
assert result_lo is False, "all-None, stars=200: old behavior was False (200<500)"

print("  import + unit + behavior-preservation OK")
PY

# (b) github_rank dogfood output byte-stable against committed golden file
CAND="docs/superpowers/specs/research/tooling-discovery-2026/github-candidates.json"
GOLDEN="tests/fixtures/tooling/github-rank-dogfood-golden.json"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

python3 scripts/github_rank.py "$CAND" --top 10 > "$TMP/gh_after.json"

if ! diff "$GOLDEN" "$TMP/gh_after.json" >/dev/null 2>&1; then
  echo "FAIL: github_rank dogfood output differs from golden file" >&2
  diff "$GOLDEN" "$TMP/gh_after.json" >&2 || true
  exit 1
fi
echo "  github_rank dogfood output byte-stable"

echo "  T1 PASS"

echo "== T2: relevance = category_fit x max(hat weight); 0 -> excluded =="
cat > tests/fixtures/tooling/relevance.json <<'JSON'
[
 {"id":"a/eval","dedup_key":"a/eval","channels":["github"],"categories":["eval"],"category_fit":1,
  "official":false,"verified_namespace":false,"official_publisher":false,"last_activity_days":10,
  "stars":100,"forks":5,"open_issues":1,"dependents_count":2,"adoption":2,"use_count":null,
  "unverified":true,"releases_count":1,"signed":false,"provenance":"github","is_meta_list":false,
  "install_command":"x"},
 {"id":"b/vat","dedup_key":"b/vat","channels":["github"],"categories":["fr-b2b-ops"],"category_fit":1,
  "official":false,"verified_namespace":false,"official_publisher":false,"last_activity_days":10,
  "stars":100,"forks":5,"open_issues":1,"dependents_count":2,"adoption":2,"use_count":null,
  "unverified":true,"releases_count":1,"signed":false,"provenance":"github","is_meta_list":false,
  "install_command":"x"},
 {"id":"c/none","dedup_key":"c/none","channels":["github"],"categories":["medieval"],"category_fit":0,
  "official":false,"verified_namespace":false,"official_publisher":false,"last_activity_days":10,
  "stars":100,"forks":5,"open_issues":1,"dependents_count":2,"adoption":2,"use_count":null,
  "unverified":true,"releases_count":1,"signed":false,"provenance":"github","is_meta_list":false,
  "install_command":"x"}
]
JSON
# Note: `cmd | python3 - <<'HEREDOC'` is broken under bash (heredoc wins for stdin, pipe
# output is unreadable via sys.stdin). Capture to variable first, then inject via heredoc.
t2_out=$(python3 suggest-tooling/scripts/marketplace_rank.py tests/fixtures/tooling/relevance.json)
python3 - <<PY
import json
d=json.loads("""${t2_out}"""); rows={r["id"]:r for r in d["ranking"]}
assert "c/none" not in rows, "category_fit=0 must be excluded"
assert abs(rows["a/eval"]["relevance"]-1.0)<1e-9, rows["a/eval"]
assert abs(rows["b/vat"]["relevance"]-0.4)<1e-9, rows["b/vat"]
print("  T2 PASS")
PY
