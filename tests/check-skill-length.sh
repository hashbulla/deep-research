#!/usr/bin/env bash
# check-skill-length.sh
# SKILL.md is the prompt served on every activation, so its length is a budget,
# not a style preference. The house rule is <=150 lines (context-engineering
# guidance: longer entry points lose attention). Brought from 209 to 150 on
# 2026-08-17 (AI-372 / PRD R6); this gate is what keeps it there.
#
# Exits 0 within budget, 1 over it.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

SKILL="SKILL.md"
LIMIT="${SKILL_LINE_LIMIT:-150}"

[ -f "$SKILL" ] || { echo "FAIL: $SKILL not found" >&2; exit 1; }

ACTUAL="$(wc -l < "$SKILL" | tr -d ' ')"

if [ "$ACTUAL" -le "$LIMIT" ]; then
  echo "OK: $SKILL is $ACTUAL lines (budget $LIMIT)."
  exit 0
fi

echo "FAIL: $SKILL is $ACTUAL lines, over the $LIMIT-line budget by $((ACTUAL - LIMIT))." >&2
echo "" >&2
echo "Densify or move detail into references/ — one level deep, never cross-linked." >&2
echo "Do NOT delete a rule to fit: every rule of the 209-line version survived the" >&2
echo "2026-08-17 compression, and that property is what made it safe. See the" >&2
echo "gotchas-log entry of that date before trimming anything." >&2
exit 1
