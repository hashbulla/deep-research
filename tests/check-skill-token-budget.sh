#!/usr/bin/env bash
# check-skill-token-budget.sh
# Guards the load tier in TOKENS, the unit the model actually pays.
#
# Why this exists, in one sentence: harness run #6 (2026-08-17) measured this
# branch at -59 lines and +41 tokens simultaneously, proving the sibling
# line-count gate cannot stand in for a token budget. Published guidance names
# BOTH caps — platform.claude.com states its "Token budgets" rule in lines
# ("under 500 lines"), agentskills.io publishes them co-equal ("under 500 lines
# and 5,000 tokens") — and until this file existed only the line cap was gated.
# Keep BOTH gates: lines guard attention, tokens guard cost. They are not proxies
# for each other, as this branch demonstrated.
#
# Method, and its honest limit: a real tokenizer would need tiktoken, which would
# break the repo's stdlib-only, zero-dependency contract for anything CI runs. So
# this counts CHARACTERS and converts at a ratio CALIBRATED against the
# authoritative instrument (`skill-generator/scripts/token_budget.py`, cl100k_base):
#
#     2026-08-17 — body 29,527 chars = 7,240 tok  =>  4.078 chars/token
#
# The ratio is a property of this file's prose, not a universal. Re-calibrate when
# the body changes character (more code blocks, more tables, another language):
#
#     python3 <skill-generator>/scripts/token_budget.py . --json
#
# and update CHARS_PER_TOKEN below in the same commit. A drifted ratio makes this
# gate lie in the direction of leniency, which is the failure mode to fear.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

SKILL="SKILL.md"
CHARS_PER_TOKEN="${CHARS_PER_TOKEN:-4.078}"
TARGET_TOKENS="${SKILL_TOKEN_TARGET:-5000}"   # published recommendation
HARD_TOKENS="${SKILL_TOKEN_HARD:-7500}"       # local hard cap (looser than published)

[ -f "$SKILL" ] || { echo "FAIL: $SKILL not found" >&2; exit 1; }

# Body only — the frontmatter is the index tier and is budgeted separately.
BODY_CHARS="$(python3 - "$SKILL" <<'PY'
import re, sys
text = open(sys.argv[1], encoding="utf-8").read()
if text.startswith("---"):
    end = re.search(r"\n---\s*\n", text)
    if end:
        text = text[end.end():]
print(len(text))
PY
)"

EST_TOKENS="$(python3 -c "print(round($BODY_CHARS / $CHARS_PER_TOKEN))")"

printf 'load tier: %s chars / %s = ~%s tok (target %s, hard %s)\n' \
  "$BODY_CHARS" "$CHARS_PER_TOKEN" "$EST_TOKENS" "$TARGET_TOKENS" "$HARD_TOKENS"

if [ "$EST_TOKENS" -gt "$HARD_TOKENS" ]; then
  echo "FAIL: estimated load tier ~$EST_TOKENS tok exceeds the $HARD_TOKENS hard cap." >&2
  echo "" >&2
  echo "Densifying will NOT fix this — measured: a 28% line reduction moved the" >&2
  echo "load tier 1.4% (7,199 -> 7,099). RELOCATE content into references/ instead," >&2
  echo "which is what actually worked historically (10,036 -> 7,199 on 2026-08-04)." >&2
  echo "Confirm against the real tokenizer before acting:" >&2
  echo "  python3 <skill-generator>/scripts/token_budget.py . --json" >&2
  exit 1
fi

if [ "$EST_TOKENS" -gt "$TARGET_TOKENS" ]; then
  echo "WARNING: ~$EST_TOKENS tok is over the $TARGET_TOKENS target (published recommendation)."
  echo "  Under the $HARD_TOKENS local hard cap, so this does not fail CI — but it is"
  echo "  hygiene debt, and CHANGELOG.md must carry a current justification with a"
  echo "  RE-MEASURED figure. A stale figure is the run-#6 DIM-3-01 finding."
fi

echo "OK: load tier within the hard cap."
exit 0
