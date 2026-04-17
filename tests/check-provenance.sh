#!/usr/bin/env bash
# check-provenance.sh
# Re-computes SHA-256 of deep-research-report.md and verifies it starts with
# the hash prefix declared on SKILL.md line 8. Defends invariant I1 from
# .claude/CLAUDE.md.
#
# Exits 0 on match, 1 on mismatch with a remediation message.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

REPORT="deep-research-report.md"
SKILL="SKILL.md"

[ -f "$REPORT" ] || { echo "FAIL: $REPORT not found" >&2; exit 1; }
[ -f "$SKILL" ]  || { echo "FAIL: $SKILL not found"  >&2; exit 1; }

# Compute current SHA-256 (portable: prefer sha256sum, fall back to shasum).
if command -v sha256sum >/dev/null 2>&1; then
  ACTUAL_FULL="$(sha256sum "$REPORT" | awk '{print $1}')"
elif command -v shasum >/dev/null 2>&1; then
  ACTUAL_FULL="$(shasum -a 256 "$REPORT" | awk '{print $1}')"
else
  echo "FAIL: neither sha256sum nor shasum available" >&2
  exit 1
fi

# Extract declared prefix from SKILL.md line 8. Example string:
#   Hash at generation time: `cb2fe20dced3c4bb…` (sha256, April 2026 version).
DECLARED_PREFIX="$(sed -n '8p' "$SKILL" | grep -oE '`[0-9a-f]{8,}' | head -n1 | tr -d '`' || true)"

if [ -z "$DECLARED_PREFIX" ]; then
  echo "FAIL: could not extract SHA-256 prefix from $SKILL line 8" >&2
  echo "Line 8 content:" >&2
  sed -n '8p' "$SKILL" >&2
  exit 1
fi

case "$ACTUAL_FULL" in
  "$DECLARED_PREFIX"*)
    echo "OK: $REPORT SHA-256 matches declared prefix '$DECLARED_PREFIX'."
    exit 0
    ;;
  *)
    echo "FAIL: SHA-256 mismatch for $REPORT" >&2
    echo "  declared prefix on $SKILL line 8: $DECLARED_PREFIX" >&2
    echo "  actual SHA-256:                    $ACTUAL_FULL" >&2
    echo "" >&2
    echo "Remediation: update $SKILL line 8 to reference the new hash:" >&2
    echo "  '\`${ACTUAL_FULL:0:16}…\`'" >&2
    exit 1
    ;;
esac
