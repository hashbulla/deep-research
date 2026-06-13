#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
echo "== T1: fake_star_gate is importable and github_rank output unchanged =="

# (a) function is importable
python3 - <<'PY'
import sys; sys.path.insert(0, "scripts")
from github_rank import fake_star_gate
assert fake_star_gate(1000, 0, 0, 0) is True, "high stars + flat usage must flag"
assert fake_star_gate(1000, 500, 500, 500) is False, "real usage must not flag"
assert fake_star_gate(100, 0, 0, 0) is False, "below 500-star floor never flags"
assert fake_star_gate(1000, None, None, None) is None, "all-usage-absent -> unknown"
assert fake_star_gate(None, 1, 1, 1) is None, "absent stars -> unknown"
print("  import + unit OK")
PY

# (b) github_rank.py output byte-identical on the dogfood candidate set
CAND="docs/superpowers/specs/research/tooling-discovery-2026/github-candidates.json"
python3 scripts/github_rank.py "$CAND" --top 10 > /tmp/gh_after.json
python3 - <<'PY'
import json
d=json.load(open("/tmp/gh_after.json"))
flags=[r["fake_star_suspect"] for r in d["ranking"]]
assert flags==[False]*len(flags), f"dogfood set must stay all-clean: {flags}"
print("  github_rank dogfood output stable")
PY
echo "  T1 PASS"
