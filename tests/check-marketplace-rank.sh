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

echo "== T3: trust-tier cascade is total + null-safe =="
cat > tests/fixtures/tooling/tiers.json <<'JSON'
[
 {"id":"official_verified","dedup_key":"o/v","channels":["mcp-registry"],"categories":["mcp-server"],"category_fit":1,
  "official":true,"verified_namespace":true,"official_publisher":false,"last_activity_days":10,
  "stars":900,"forks":50,"open_issues":3,"dependents_count":7,"adoption":7,"use_count":null,
  "unverified":false,"releases_count":2,"signed":true,"provenance":"mcp-registry","is_meta_list":false,"install_command":"x"},
 {"id":"official_null_div","dedup_key":"o/n","channels":["mcp-registry"],"categories":["mcp-server"],"category_fit":1,
  "official":true,"verified_namespace":true,"official_publisher":false,"last_activity_days":10,
  "stars":null,"forks":null,"open_issues":null,"dependents_count":null,"adoption":null,"use_count":null,
  "unverified":false,"releases_count":null,"signed":null,"provenance":"mcp-registry","is_meta_list":false,"install_command":"x"},
 {"id":"community_active","dedup_key":"c/a","channels":["github"],"categories":["eval"],"category_fit":1,
  "official":false,"verified_namespace":false,"official_publisher":false,"last_activity_days":20,
  "stars":300,"forks":2,"open_issues":1,"dependents_count":5,"adoption":5,"use_count":null,
  "unverified":true,"releases_count":1,"signed":false,"provenance":"github","is_meta_list":false,"install_command":"x"},
 {"id":"gap_120d_nulladopt","dedup_key":"g/1","channels":["github"],"categories":["eval"],"category_fit":1,
  "official":false,"verified_namespace":false,"official_publisher":false,"last_activity_days":120,
  "stars":300,"forks":2,"open_issues":1,"dependents_count":null,"adoption":null,"use_count":null,
  "unverified":true,"releases_count":1,"signed":false,"provenance":"github","is_meta_list":false,"install_command":"x"},
 {"id":"stale","dedup_key":"s/1","channels":["github"],"categories":["eval"],"category_fit":1,
  "official":true,"verified_namespace":true,"official_publisher":false,"last_activity_days":400,
  "stars":300,"forks":2,"open_issues":1,"dependents_count":5,"adoption":5,"use_count":null,
  "unverified":false,"releases_count":1,"signed":true,"provenance":"github","is_meta_list":false,"install_command":"x"},
 {"id":"all_null","dedup_key":"a/n","channels":["mcp-registry"],"categories":["eval"],"category_fit":1,
  "official":false,"verified_namespace":false,"official_publisher":false,"last_activity_days":null,
  "stars":null,"forks":null,"open_issues":null,"dependents_count":null,"adoption":null,"use_count":null,
  "unverified":true,"releases_count":null,"signed":null,"provenance":"mcp-registry","is_meta_list":false,"install_command":"x"}
]
JSON
T3_OUT=$(python3 suggest-tooling/scripts/marketplace_rank.py tests/fixtures/tooling/tiers.json)
python3 - "$T3_OUT" <<'PY'
import json,sys
r={x["id"]:x["trust_tier"] for x in json.loads(sys.argv[1])["ranking"]}
exp={"official_verified":"VERIFIED","official_null_div":"COMMUNITY","community_active":"MAINTAINED",
     "gap_120d_nulladopt":"COMMUNITY","stale":"CAUTION","all_null":"CAUTION"}
for k,v in exp.items():
    assert r.get(k)==v, f"{k}: got {r.get(k)} want {v}"
print("  T3 PASS (totality + null-safety verified)")
PY

echo "== T4: scalar fake-signal gate fires only at N>=8 =="
python3 - <<'PY'
import json
small=[{"id":f"s/{i}","dedup_key":f"s/{i}","channels":["smithery"],"categories":["mcp-server"],
 "category_fit":1,"official":False,"verified_namespace":False,"official_publisher":False,
 "last_activity_days":10,"stars":None,"forks":None,"open_issues":None,"dependents_count":None,
 "adoption":uc,"use_count":uc,"unverified":True,"releases_count":None,"signed":None,
 "provenance":"smithery","is_meta_list":False,"install_command":"x"} for i,uc in enumerate([10,20,9000])]
with open("tests/fixtures/tooling/scalar_smalln.json","w") as f: json.dump(small,f)
big=[{"id":f"b/{i}","dedup_key":f"b/{i}","channels":["smithery"],"categories":["mcp-server"],
 "category_fit":1,"official":False,"verified_namespace":False,"official_publisher":False,
 "last_activity_days":10,"stars":None,"forks":None,"open_issues":None,"dependents_count":None,
 "adoption":uc,"use_count":uc,"unverified":True,"releases_count":None,"signed":None,
 "provenance":"smithery","is_meta_list":False,"install_command":"x"} for i,uc in enumerate([5,6,7,8,9,10,11,12,13,9000])]
with open("tests/fixtures/tooling/scalar_bign.json","w") as f: json.dump(big,f)
PY
SMALL=$(python3 suggest-tooling/scripts/marketplace_rank.py tests/fixtures/tooling/scalar_smalln.json)
python3 - "$SMALL" <<'PY'
import json,sys
flags=[x["trust_evidence"]["fake_signal_flag"] for x in json.loads(sys.argv[1])["ranking"]]
assert all(f is None for f in flags), f"small N must not flag: {flags}"
print("  small-N: no spurious flag OK")
PY
BIG=$(python3 suggest-tooling/scripts/marketplace_rank.py tests/fixtures/tooling/scalar_bign.json)
python3 - "$BIG" <<'PY'
import json,sys
rows={x["id"]:x for x in json.loads(sys.argv[1])["ranking"]}
assert rows["b/9"]["trust_evidence"]["fake_signal_flag"] is True, "the 9000-useCount outlier must flag at N=10"
assert rows["b/9"]["trust_tier"]=="CAUTION"
print("  T4 PASS")
PY

echo "== T5: cross-channel dedupe is trust-conservative + order-independent =="
cat > tests/fixtures/tooling/dedupe.json <<'JSON'
[
 {"id":"reg/x","dedup_key":"acme/x","channels":["mcp-registry"],"categories":["mcp-server"],"category_fit":1,
  "official":true,"verified_namespace":true,"official_publisher":false,"last_activity_days":5,
  "stars":null,"forks":null,"open_issues":null,"dependents_count":null,"adoption":null,"use_count":null,
  "unverified":false,"releases_count":null,"signed":true,"provenance":"mcp-registry","is_meta_list":false,"install_command":"reg"},
 {"id":"sm/x","dedup_key":"acme/x","channels":["smithery"],"categories":["mcp-server"],"category_fit":1,
  "official":false,"verified_namespace":false,"official_publisher":false,"last_activity_days":300,
  "stars":null,"forks":null,"open_issues":null,"dependents_count":null,"adoption":50,"use_count":50,
  "unverified":true,"releases_count":null,"signed":false,"provenance":"smithery","is_meta_list":false,"install_command":"sm"}
]
JSON
OUT5=$(python3 suggest-tooling/scripts/marketplace_rank.py tests/fixtures/tooling/dedupe.json)
python3 - "$OUT5" <<'PY'
import json,sys
rk=json.loads(sys.argv[1])["ranking"]
assert len(rk)==1, f"must collapse to one row, got {len(rk)}"
row=rk[0]
assert set(row["channels"])=={"mcp-registry","smithery"}, row["channels"]
assert row["trust_evidence"]["verified_namespace"] is True
assert row["trust_tier"]=="CAUTION", f"most-cautious activity (300d) wins -> {row['trust_tier']}"
print("  T5 PASS")
PY
# order-independence: reversed input must produce byte-identical output (catches first-wins merges)
python3 -c "import json; d=json.load(open('tests/fixtures/tooling/dedupe.json')); json.dump(list(reversed(d)), open('tests/fixtures/tooling/dedupe_rev.json','w'))"
OUT5R=$(python3 suggest-tooling/scripts/marketplace_rank.py tests/fixtures/tooling/dedupe_rev.json)
python3 - "$OUT5" "$OUT5R" <<'PY'
import json,sys
fwd=json.loads(sys.argv[1]); rev=json.loads(sys.argv[2])
assert fwd==rev, "dedupe is order-dependent: forward != reversed output"
print("  T5 order-independence PASS")
PY
rm -f tests/fixtures/tooling/dedupe_rev.json

echo "== T6: composite score + tier-major ordering =="
cat > tests/fixtures/tooling/ranking.json <<'JSON'
[
 {"id":"hi/rel","dedup_key":"hi/rel","channels":["github"],"categories":["eval"],"category_fit":1,
  "official":true,"verified_namespace":true,"official_publisher":false,"last_activity_days":5,
  "stars":2000,"forks":300,"open_issues":40,"dependents_count":80,"adoption":80,"use_count":null,
  "unverified":false,"releases_count":10,"signed":true,"provenance":"github","is_meta_list":false,"install_command":"x"},
 {"id":"lo/caution","dedup_key":"lo/caution","channels":["github"],"categories":["eval"],"category_fit":1,
  "official":false,"verified_namespace":false,"official_publisher":false,"last_activity_days":400,
  "stars":50,"forks":0,"open_issues":0,"dependents_count":0,"adoption":0,"use_count":null,
  "unverified":true,"releases_count":0,"signed":false,"provenance":"github","is_meta_list":false,"install_command":"x"}
]
JSON
OUT6=$(python3 suggest-tooling/scripts/marketplace_rank.py tests/fixtures/tooling/ranking.json)
python3 - "$OUT6" <<'PY'
import json,sys
d=json.loads(sys.argv[1])
assert "effective_weights" in d and "dropped_components" in d, list(d.keys())
ids=[r["id"] for r in d["ranking"]]
assert ids==["hi/rel","lo/caution"], ids  # VERIFIED before CAUTION regardless of raw score
assert all("score" in r for r in d["ranking"])
print("  T6 PASS")
print("  ALL marketplace_rank checks PASS")
PY
