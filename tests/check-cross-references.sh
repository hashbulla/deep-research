#!/usr/bin/env bash
# check-cross-references.sh
# Walks every relative markdown link in SKILL.md, README.md, .claude/CLAUDE.md,
# and references/*.md, verifying each target exists. Then walks every [R§n] /
# [R§n.m] back-reference in references/methodology.md and verifies a matching
# numbered section heading exists in deep-research-report.md.
#
# Exits 0 on success, 1 with the first broken reference on failure.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

fail_count=0
check_count=0

check_link() {
  local source_file="$1"
  local target="$2"
  local base_dir
  base_dir="$(dirname "$source_file")"

  # Strip any URL fragment (#heading) — we only check file existence.
  target="${target%%#*}"

  # Empty target after fragment strip = pure in-document anchor, skip.
  if [ -z "$target" ]; then
    return 0
  fi

  # Absolute or protocol links — skip.
  case "$target" in
    http://*|https://*|mailto:*|/*) return 0 ;;
  esac

  local resolved="$base_dir/$target"
  check_count=$((check_count + 1))
  if [ ! -e "$resolved" ]; then
    echo "BROKEN LINK: $source_file -> $target (resolved: $resolved)" >&2
    fail_count=$((fail_count + 1))
  fi
}

# --- Pass 1: relative markdown links [text](path) ---

MD_FILES=(SKILL.md README.md .claude/CLAUDE.md)
while IFS= read -r -d '' f; do
  MD_FILES+=("$f")
done < <(find references -maxdepth 1 -name "*.md" -print0)

for f in "${MD_FILES[@]}"; do
  if [ ! -f "$f" ]; then
    continue
  fi
  # Extract markdown link targets: [text](target). Multi-line is rare in this
  # repo; single-line grep is sufficient.
  while IFS= read -r target; do
    [ -n "$target" ] && check_link "$f" "$target"
  done < <(grep -oE '\]\([^)]+\)' "$f" | sed -E 's/^\]\(//; s/\)$//')
done

# --- Pass 2: [R§n] and [R§n.m] back-references in references/methodology.md ---

METH="references/methodology.md"
REPORT="deep-research-report.md"

if [ -f "$METH" ] && [ -f "$REPORT" ]; then
  # Collect distinct top-level section numbers referenced, e.g. §1, §2 ... §11.
  while IFS= read -r ref; do
    # ref looks like "R§3" or "R§3.1"; extract the top-level number.
    top="$(echo "$ref" | sed -E 's/^R§([0-9]+).*$/\1/')"
    check_count=$((check_count + 1))
    # Report headings follow "## <n>" or "## <n>." convention.
    if ! grep -qE "^##[[:space:]]+${top}([.[:space:]]|$)" "$REPORT"; then
      echo "BROKEN BACKREF: references/methodology.md cites [R§${top}] but no '## ${top}' section exists in ${REPORT}" >&2
      fail_count=$((fail_count + 1))
    fi
  done < <(grep -oE '\[R§[0-9]+(\.[0-9]+)?\]' "$METH" | sed -E 's/^\[//; s/\]$//' | sort -u)
fi

echo "Checked ${check_count} references. Failures: ${fail_count}."
if [ "$fail_count" -gt 0 ]; then
  exit 1
fi
exit 0
