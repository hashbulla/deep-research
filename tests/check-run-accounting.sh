#!/usr/bin/env bash
# check-run-accounting.sh
# Drives scripts/run_accounting.py: the classification rule must match the
# pre-registered instrument, and the output must never present a cost or token
# figure — those are not measurable from inside a run, and claiming otherwise is
# the failure this artifact exists to prevent.
#
# CI-only. Exits 0 when all cases hold.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

SCRIPT="scripts/run_accounting.py"
[ -f "$SCRIPT" ] || { echo "FAIL: $SCRIPT not found" >&2; exit 1; }

SANDBOX="$(mktemp -d)"
trap 'rm -rf "$SANDBOX"' EXIT

FAILURES=0
fail() { echo "FAIL: $1" >&2; FAILURES=$((FAILURES + 1)); }

# I4a: stdlib only, zero network. Same posture the repo already demands of
# verify_gates.py — a retrieval accounting script that opened a socket would be
# absurd, so make it a checked property rather than a promise.
if grep -nE '^\s*(import|from)\s+(requests|urllib|http|socket|httpx|aiohttp)' "$SCRIPT"; then
  fail "network-capable import in $SCRIPT (invariant I4a: zero network)"
fi

cat > "$SANDBOX/steps.json" <<'EOF'
{"steps": [
  {"phase": "0", "tools": ["Read", "Bash"]},
  {"phase": "1", "tools": ["mcp__tavily__tavily_search"]},
  {"phase": "1", "tools": ["mcp__tavily__tavily_search", "mcp__tavily__tavily_map"]},
  {"phase": "1", "tools": ["mcp__scrapling__stealthy_fetch", "Write"]},
  {"phase": "4", "tools": ["WebFetch"]},
  {"phase": "6", "tools": ["Bash", "Write"]},
  {"phase": "6", "tools": []}
]}
EOF

python3 "$SCRIPT" --steps "$SANDBOX/steps.json" --out "$SANDBOX/out.json" --length standard >/dev/null \
  || fail "script exited non-zero on a well-formed input"

# Case 1 — the classification rule, including the mixed-step convention.
python3 - "$SANDBOX/out.json" <<'PY' || fail "case 1: classification does not match the pre-registered rule"
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
s, c = d["steps"], d["calls"]
assert s["total"] == 7, s
# engine steps: the 3 tavily/scrapling ones + the WebFetch one
assert s["engine"] == 4, s
assert s["contract"] == 3, s
# only the scrapling+Write step mixes both kinds
assert s["mixed_counted_engine"] == 1, s
# Oracle derived from the fixture, not guessed: retrieval = 1 + 2 + 1 + 1 = 5
# (steps 2,3,4,5); other = 2 (Read,Bash) + 1 (Write) + 2 (Bash,Write) = 5.
assert c["retrieval"] == 5, c
assert c["other"] == 5, c
assert c["total"] == 10, c
assert d["by_phase"]["1"]["engine_steps"] == 3, d["by_phase"]["1"]
assert d["by_phase"]["1"]["retrieval_calls"] == 4, d["by_phase"]["1"]
assert d["by_phase"]["6"]["engine_steps"] == 0, d["by_phase"]["6"]
assert d["by_tool"]["mcp__tavily__tavily_search"] == 2, d["by_tool"]
assert d["length"] == "standard", d["length"]
PY

# Case 2 — no cost or token figure anywhere. The vector reports counts; the
# moment it reports a dollar it is lying about what a run can observe.
python3 - "$SANDBOX/out.json" <<'PY' || fail "case 2: output presents a token/cost figure, or drops the non-measurable declaration"
import json, sys
raw = open(sys.argv[1], encoding="utf-8").read()
d = json.loads(raw)

banned = ("cost_usd", "usd", "dollars_spent", "total_tokens", "input_tokens", "output_tokens")
def walk(node, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            assert k not in banned, f"banned measurement key {k!r} at {path}"
            walk(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            walk(v, f"{path}[{i}]")
walk(d)

# Declared, never silently absent.
nm = d["not_measurable_in_run"]
for key in ("tokens", "dollars", "context_carry", "how_to_obtain"):
    assert key in nm and nm[key].strip(), f"missing or empty declaration: {key}"
assert "result" in nm["tokens"], "the tokens declaration must name WHY (the result event)"
assert d["shares"]["basis"], "shares must carry a basis note"
assert "NOT a cost share" in d["shares"]["basis"], "shares must refuse the cost reading explicitly"
PY

# Case 3 — the rule travels with the data, so a reader can audit the numbers.
python3 - "$SANDBOX/out.json" <<'PY' || fail "case 3: rule provenance missing from the artifact"
import json, sys
r = json.load(open(sys.argv[1], encoding="utf-8"))["rule"]
assert "decompose-moteur-contrat.py" in r["provenance"], r["provenance"]
assert set(r["retrieval_tools"]["exact"]) == {"WebFetch", "WebSearch"}, r
assert r["retrieval_tools"]["prefixes"] == ["mcp__tavily__", "mcp__scrapling__"], r
PY

# Case 4 — an empty run degrades to null shares, never a division by zero and
# never a fabricated 0%.
echo '{"steps": []}' > "$SANDBOX/empty.json"
python3 "$SCRIPT" --steps "$SANDBOX/empty.json" --out - >"$SANDBOX/empty-out.json" 2>/dev/null \
  || fail "case 4: script crashed on an empty run"
python3 - "$SANDBOX/empty-out.json" <<'PY' || fail "case 4: empty run does not degrade cleanly"
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
assert d["steps"]["total"] == 0
assert d["shares"]["engine_steps"] is None, d["shares"]
assert d["shares"]["retrieval_calls"] is None, d["shares"]
PY

# Case 5 — malformed input fails loudly instead of emitting an empty vector.
echo 'not json at all' > "$SANDBOX/bad.json"
if python3 "$SCRIPT" --steps "$SANDBOX/bad.json" --out "$SANDBOX/bad-out.json" 2>/dev/null; then
  fail "case 5: malformed input did not fail"
fi

if [ "$FAILURES" -eq 0 ]; then
  echo "OK: run accounting holds the pre-registered rule and refuses cost claims (5 cases)."
  exit 0
fi
echo "FAIL: $FAILURES run-accounting case(s) failed." >&2
exit 1
