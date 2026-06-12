#!/usr/bin/env bash
# check-example-invariants.sh
# Cross-file invariant checks on a sources/evidence artifact pair that
# schema validation alone cannot see (guards the failure mode found as
# ADV-7: an example that violates the skill's own grading rules).
#
# Checks:
#   1. Every supporting/contradicting source ID resolves to a source record.
#   2. Source IDs and claim IDs are unique.
#   3. corroboration_count == count of distinct supporting_source_ids.
#   4. independent_tier12_count == recomputed Tier 1/2 supporting count.
#   5. admiralty_credibility matches the normative cascade
#      (references/methodology.md §4.1) recomputed from joined tiers.
#   6. label matches the credibility digit.
#   7. Routing: credibility >= 4 only in "Needs Verification"; <= 3 never there.
#   8. No Tier 4 source in supporting_source_ids (anti-pattern B5).
#   9. Non-null tavily_score < 0.7 requires a non-empty notes justification.
#
# Usage: bash tests/check-example-invariants.sh [SOURCES_JSON EVIDENCE_JSON]
# Defaults to the eu-ai-act-2026 example. Exits 0 on all-pass, 1 otherwise.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

SOURCES="${1:-examples/eu-ai-act-2026/research-sources.json}"
EVIDENCE="${2:-examples/eu-ai-act-2026/research-evidence.json}"

command -v jq >/dev/null || { echo "FAIL: jq required" >&2; exit 1; }
[ -f "$SOURCES" ]  || { echo "FAIL: $SOURCES not found" >&2; exit 1; }
[ -f "$EVIDENCE" ] || { echo "FAIL: $EVIDENCE not found" >&2; exit 1; }

errors="$(jq -n --slurpfile sources "$SOURCES" --slurpfile evidence "$EVIDENCE" '
  ($sources[0])  as $S |
  ($evidence[0]) as $E |
  ($S | map({key: .id, value: .domain_tier}) | from_entries) as $tier |

  def cascade($s12; $s1; $c):
    if   $s12 >= 2 and $c == 0 then 1
    elif $s1  >= 1 and $c == 0 then 2
    elif $s12 >= 2 and $c == 1 then 2
    elif $s12 == 1 and $c == 0 then 3
    elif $s12 >= 1 and $c >= 1 then 4
    elif $c >= 2               then 5
    else 6 end;

  ({"1":"CONFIRMED","2":"PROBABLY TRUE","3":"POSSIBLY TRUE",
    "4":"DOUBTFUL","5":"IMPROBABLE","6":"UNVERIFIED"}) as $labels |

  [
    # 1. dangling source references
    ($E[] | . as $cl | (.supporting_source_ids + .contradicting_source_ids)[]
      | select($tier[.] == null)
      | "\($cl.claim_id): references unknown source id \(.)"),

    # 2. duplicate IDs
    (($S | group_by(.id) | map(select(length > 1) | .[0].id)[])
      | "duplicate source id \(.)"),
    (($E | group_by(.claim_id) | map(select(length > 1) | .[0].claim_id)[])
      | "duplicate claim id \(.)"),

    # 3–6. per-claim recomputation
    ($E[] | . as $cl |
      ([$cl.supporting_source_ids[] | $tier[.] // 99] ) as $stiers |
      ([$cl.contradicting_source_ids[] | $tier[.] // 99]) as $ctiers |
      ([$stiers[] | select(. <= 2)] | length) as $s12 |
      ([$stiers[] | select(. == 1)] | length) as $s1 |
      ([$ctiers[] | select(. <= 2)] | length) as $c |
      (
        (if ($cl.supporting_source_ids | unique | length) != $cl.corroboration_count
         then "\($cl.claim_id): corroboration_count \($cl.corroboration_count) != distinct supporting sources \($cl.supporting_source_ids | unique | length)" else empty end),
        (if $s12 != $cl.independent_tier12_count
         then "\($cl.claim_id): independent_tier12_count \($cl.independent_tier12_count) != recomputed \($s12)" else empty end),
        (cascade($s12; $s1; $c) as $expected |
         if $expected != $cl.admiralty_credibility
         then "\($cl.claim_id): credibility \($cl.admiralty_credibility) != cascade result \($expected) (s12=\($s12), s1=\($s1), c=\($c))" else empty end),
        (if $labels[($cl.admiralty_credibility | tostring)] != $cl.label
         then "\($cl.claim_id): label \(.label) does not match credibility \($cl.admiralty_credibility)" else empty end),

        # 7. routing
        (if $cl.admiralty_credibility >= 4 and ($cl.section != "Needs Verification")
         then "\($cl.claim_id): credibility \($cl.admiralty_credibility) must be in Needs Verification, found in \($cl.section)" else empty end),
        (if $cl.admiralty_credibility <= 3 and ($cl.section == "Needs Verification")
         then "\($cl.claim_id): credibility \($cl.admiralty_credibility) must not be in Needs Verification" else empty end),

        # 8. Tier 4 as factual support (B5)
        ([$cl.supporting_source_ids[] | select(($tier[.] // 99) == 4)][] |
         "\($cl.claim_id): Tier 4 source \(.) used as factual support (B5)")
      )
    ),

    # 9. low-score sources need a notes justification
    ($S[] | select(.tavily_score != null and .tavily_score < 0.7 and (.notes == ""))
      | "\(.id): tavily_score \(.tavily_score) < 0.7 retained without notes justification")
  ] | .[]
' 2>&1)" || { echo "FAIL: jq evaluation error:" >&2; echo "$errors" >&2; exit 1; }

if [ -n "$errors" ]; then
  echo "FAIL: example invariant violations:" >&2
  echo "$errors" >&2
  exit 1
fi

src_n="$(jq 'length' "$SOURCES")"
cl_n="$(jq 'length' "$EVIDENCE")"
echo "OK: $SOURCES ($src_n sources) and $EVIDENCE ($cl_n claims) satisfy all cross-file invariants."
exit 0
