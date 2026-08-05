#!/usr/bin/env bash
# check-solution-space.sh
# Drives the solution-space layer of the deterministic gates:
#
#   1. verify_gates.py check-solution-space over tests/fixtures/solution-space/
#      — one golden manifest plus twelve single-mutation violation fixtures,
#      each asserted to fire ITS OWN violation (not merely "some" failure: a
#      gate that fails everything is worth as little as one that fails nothing).
#   2. stack_inventory.py over the frozen SOTA-recall corpus
#      (evals/fixtures/sota-recall/) — the deterministic half of the recall
#      regression: the own-stack sweep must surface the unified-messaging
#      bridge BEFORE any web call, and must not match everything it is asked.
#
# CI-only — never invoked by the skill at runtime.
set -euo pipefail
cd "$(dirname "$0")/.."

F=tests/fixtures/solution-space
GATE=(python3 scripts/verify_gates.py check-solution-space --manifest)
STACK=scripts/stack_inventory.py
CONFIG=evals/fixtures/sota-recall/stack-paths.fixture.json
CORPUS_UNIPILE=unipile-playbook.md
CORPUS_DECOY=scrapling-note.md
fail=0

command -v jq >/dev/null      || { echo "FAIL: jq required" >&2; exit 1; }
command -v python3 >/dev/null || { echo "FAIL: python3 required" >&2; exit 1; }
[ -f "$STACK" ]  || { echo "FAIL: $STACK not found" >&2; exit 1; }
[ -f "$CONFIG" ] || { echo "FAIL: $CONFIG not found" >&2; exit 1; }

eq() { # <label> <actual> <expected>
  if [ "$2" = "$3" ]; then echo "ok: $1"; else echo "MISS [$1]: expected '$3', got '$2'"; fail=1; fi
}
ge() { # <label> <actual> <floor>
  if [ "$2" -ge "$3" ]; then echo "ok: $1"; else echo "MISS [$1]: expected >= $3, got $2"; fail=1; fi
}
gt() { # <label> <actual> <bar>
  if [ "$2" -gt "$3" ]; then echo "ok: $1"; else echo "MISS [$1]: expected > $3, got $2"; fail=1; fi
}

# 1. The golden manifest passes -------------------------------------------------
set +e
out="$("${GATE[@]}" "$F/valid.json")"; rc=$?
set -e
eq "valid.json exits 0"        "$rc" "0"
eq "valid.json verdict"        "$(jq -r '.verdict' <<<"$out")" "PASS"
eq "valid.json counts waivers" "$(jq -r '.summary.waived' <<<"$out")" "1"
eq "valid.json counts findings" "$(jq -r '.summary.findings' <<<"$out")" "6"

# 2. Each violation fixture fails, naming its own offending category/field ------
# The needle per fixture is the distinctive fragment of the violation the single
# mutation is supposed to trigger. A fixture that fails for a DIFFERENT reason
# than its name claims is a broken test, not a passing one.
while IFS='|' read -r name needle; do
  [ -z "$name" ] && continue
  set +e
  out="$("${GATE[@]}" "$F/$name.json")"; rc=$?
  set -e
  if [ "$rc" -ne 1 ]; then
    echo "MISS [$name]: expected exit 1, got $rc"; fail=1
  elif [ "$(jq -r '.verdict' <<<"$out")" != "FAIL" ]; then
    echo "MISS [$name]: verdict is not FAIL"; fail=1
  elif ! grep -qF "$needle" <<<"$out"; then
    echo "MISS [$name]: violations never mention '$needle'"; fail=1
  else
    echo "ok: $name -> $needle"
  fi
done <<'EOF'
waived-no-reason|substitution-channels: status 'waived' requires a non-empty reason
swept-no-queries|own-stack: status 'swept' requires >=1 non-empty query
swept-no-findings|open-source: status 'swept' requires >=1 finding
empty-no-control|mcp-registries: status 'empty' requires a control probe
empty-control-not-found|mcp-registries: control probe did not find its expected hit
na-mixed|solution_space_applicable=false requires status 'not-applicable', found 'swept'
applicable-with-na|substitution-channels: solution_space_applicable=true forbids status 'not-applicable'
no-critic|critic.ran must be true
waived-unreviewed|critic.waivers_reviewed must be true when a category is waived
commercial-no-riskclass|commercial-vendors/HikerAPI: class 'commercial' requires a risk_class
registries-missing|mcp-registries: status 'empty' requires a non-empty registries list
oss-prose-only|open-source: status 'swept' requires >=1 GitHub-native query
EOF

# 3. Own-stack sweep over the frozen SOTA-recall corpus -------------------------
# Recall property (ground-truth.json, case `ig`, item `unipile`): the sweep must
# surface the unified-messaging bridge as covering Instagram DMs — on the terms
# `instagram` AND `dm`, before any web call.
set +e
out="$(python3 "$STACK" --config "$CONFIG" --terms "instagram,messaging,dm")"; rc=$?
set -e
eq "stack sweep exits 0"           "$rc" "0"
eq "stack sweep reads its config"  "$(jq -r '.config_present' <<<"$out")" "true"
uni_hits="$(jq "[.hits[] | select(.file | endswith(\"$CORPUS_UNIPILE\"))] | length" <<<"$out")"
ge "own-stack sweep surfaces the unified-messaging bridge" "$uni_hits" 1
uni_terms="$(jq -r "[.hits[] | select(.file | endswith(\"$CORPUS_UNIPILE\")) | .term] | unique | join(\",\")" <<<"$out")"
eq "...on instagram AND dm AND messaging" "$uni_terms" "dm,instagram,messaging"
eq "...and it lands in hit_files" \
   "$(jq "[.hit_files[] | select(endswith(\"$CORPUS_UNIPILE\"))] | length" <<<"$out")" "1"

# Precision: the decoy must not surface at all. (Its disclaimer was reworded
# 2026-08-04 — the original literally contained the sweep terms, a fixture bug
# no substring matcher could exclude; fixed at the source, ground truth intact.)
eq "decoy contributes zero hits" \
   "$(jq "[.hits[] | select(.file | endswith(\"$CORPUS_DECOY\"))] | length" <<<"$out")" "0"
eq "decoy absent from hit_files" \
   "$(jq "[.hit_files[] | select(endswith(\"$CORPUS_DECOY\"))] | length" <<<"$out")" "0"

# 4. Control-negative: the matcher does not match everything --------------------
set +e
out="$(python3 "$STACK" --config "$CONFIG" --terms "zzz-quasar-nonexistent")"; rc=$?
set -e
eq "control-negative exits 0"                "$rc" "0"
eq "control-negative keeps config_present"   "$(jq -r '.config_present' <<<"$out")" "true"
eq "control-negative yields zero hits"       "$(jq -r '.hits | length' <<<"$out")" "0"
eq "control-negative yields zero hit_files"  "$(jq -r '.hit_files | length' <<<"$out")" "0"

# 5. Absent config degrades LOUDLY (exit 2 -> own-stack recorded `degraded`) ----
set +e
out="$(python3 "$STACK" --config /nonexistent/stack-paths.json --terms "instagram" 2>/dev/null)"; rc=$?
set -e
eq "absent config exits 2"           "$rc" "2"
eq "absent config says so in JSON"   "$(jq -r '.config_present' <<<"$out")" "false"

# 6. Bad invocation is exit 1, NOT exit 2 --------------------------------------
# The two must stay distinguishable: exit 2 tells the caller to record the
# own-stack category as `degraded`, so a forgotten --terms must never be able to
# masquerade as a missing config.
set +e
python3 "$STACK" --config "$CONFIG" >/dev/null 2>&1; rc=$?
set -e
eq "missing --terms exits 1" "$rc" "1"

if [ "$fail" -eq 0 ]; then
  echo "check-solution-space: PASS"
else
  echo "check-solution-space: FAIL"; exit 1
fi
