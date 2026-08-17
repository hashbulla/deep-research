#!/usr/bin/env bash
# check-precommit-hook.sh
# Exercises .githooks/pre-commit against a throwaway repository: the hook must
# refresh the SHA-256 provenance prefix (invariant I1) when the report changes,
# and must refuse to stage SKILL.md when doing so would sweep in unreviewed work.
#
# CI-only, like every script under tests/. Exits 0 when all cases hold.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOOK="$REPO_ROOT/.githooks/pre-commit"

[ -x "$HOOK" ] || { echo "FAIL: $HOOK missing or not executable" >&2; exit 1; }

SANDBOX="$(mktemp -d)"
trap 'rm -rf "$SANDBOX"' EXIT

FAILURES=0
report_fail() { echo "FAIL: $1" >&2; FAILURES=$((FAILURES + 1)); }

sha_prefix_of() {  # $1 = file, $2 = prefix length
  sha256sum "$1" | awk '{print $1}' | cut -c "1-$2"
}

declared_prefix_in() {
  grep -m1 'Hash at generation time:' "$1" | grep -oE '`[0-9a-f]{8,}' | head -n1 | tr -d '`'
}

# A minimal repo carrying only the two files the invariant binds together.
setup_repo() {
  local dir="$1"
  rm -rf "$dir"; mkdir -p "$dir"; cd "$dir"
  git init -q .
  git config user.email "test@example.invalid"
  git config user.name "provenance test"
  git config commit.gpgsign false
  mkdir -p .githooks
  cp "$HOOK" .githooks/pre-commit
  git config core.hooksPath .githooks

  printf 'original report body\n' > deep-research-report.md
  local full; full="$(sha256sum deep-research-report.md | awk '{print $1}')"
  cat > SKILL.md <<EOF
---
name: fixture
---
- Hash at generation time: \`${full:0:16}…\` (sha256, fixture).
EOF
  git add -A
  git commit -qm "seed" --no-verify
}

# Case 1 — chain already consistent: the hook stays out of the way.
setup_repo "$SANDBOX/case1"
printf 'unrelated change\n' > other.md
git add other.md
if git commit -qm "unrelated"; then
  [ "$(declared_prefix_in SKILL.md)" = "$(sha_prefix_of deep-research-report.md 16)" ] \
    || report_fail "case 1: hook rewrote the prefix on an unrelated commit"
else
  report_fail "case 1: hook blocked a commit that touched neither side of the chain"
fi

# Case 2 — report changed, SKILL.md clean: refreshed, re-staged, commit proceeds.
setup_repo "$SANDBOX/case2"
printf 'edited report body\n' > deep-research-report.md
git add deep-research-report.md
EXPECTED="$(sha_prefix_of deep-research-report.md 16)"
if git commit -qm "edit report"; then
  COMMITTED="$(git show HEAD:SKILL.md | grep -m1 'Hash at generation time:' | grep -oE '`[0-9a-f]{8,}' | head -n1 | tr -d '`')"
  [ "$COMMITTED" = "$EXPECTED" ] \
    || report_fail "case 2: committed prefix '$COMMITTED' != expected '$EXPECTED'"
  git diff --quiet -- SKILL.md \
    || report_fail "case 2: SKILL.md left dirty after the hook re-staged it"
else
  report_fail "case 2: hook blocked a commit it should have repaired"
fi

# Case 3 — report changed AND SKILL.md carries unstaged edits: commit blocked.
setup_repo "$SANDBOX/case3"
printf 'edited report body\n' > deep-research-report.md
git add deep-research-report.md
printf '\nunreviewed line the author never staged\n' >> SKILL.md
if git commit -qm "edit report with dirty skill" 2>/dev/null; then
  report_fail "case 3: hook staged SKILL.md despite unreviewed unstaged edits"
else
  grep -q 'unreviewed line the author never staged' SKILL.md \
    || report_fail "case 3: hook destroyed the author's unstaged edit"
  [ "$(declared_prefix_in SKILL.md)" = "$(sha_prefix_of deep-research-report.md 16)" ] \
    || report_fail "case 3: hook blocked without repairing the working tree"
fi

# Case 4 — marker line gone: the chain is unverifiable, so the commit is blocked.
setup_repo "$SANDBOX/case4"
grep -v 'Hash at generation time:' SKILL.md > SKILL.tmp && mv SKILL.tmp SKILL.md
printf 'edited report body\n' > deep-research-report.md
git add -A
if git commit -qm "drop the marker" 2>/dev/null; then
  report_fail "case 4: hook allowed a commit that removed the provenance marker"
fi

cd "$REPO_ROOT"
if [ "$FAILURES" -eq 0 ]; then
  echo "OK: pre-commit hook holds the provenance chain across all 4 cases."
  exit 0
fi
echo "FAIL: $FAILURES pre-commit hook case(s) failed." >&2
exit 1
