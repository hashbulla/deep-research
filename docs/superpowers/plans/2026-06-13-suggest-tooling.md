# suggest-tooling Recommender Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a sibling skill `suggest-tooling` that consumes a finished `/deep-research` run and proposes work-relevant Claude Code skills/plugins/MCP servers — relevance-ranked, trust-tier-graded, never auto-installed — plus a default-OFF `--suggest-tooling` delegation flag in `deep-research`.

**Architecture:** The deterministic core is one stdlib-only script `suggest-tooling/scripts/marketplace_rank.py` (composite rank + total trust-tier cascade + scalar fake-signal gate + cross-channel dedupe), reusing a `fake_star_gate()` extracted from the existing `scripts/github_rank.py` (single source of truth). All discovery (6 channels) and topic→category classification are markdown-orchestration in `suggest-tooling/SKILL.md` (Bash/MCP/LLM layer) that emits a pre-classified candidate JSON to the script — keeping the script zero-network/zero-LLM (invariant I4a). The skill writes a 5th artifact `research-toolbox.md`; the four-artifact contract of `deep-research` is untouched.

**Tech Stack:** Python 3.11 stdlib only (no pytest, no PyYAML — repo convention). Tests are bash `tests/check-*.sh` harness scripts invoking the Python and asserting on JSON output via inline `python3 -c`, mirroring `tests/check-newsletter-search.sh`. CI is `.github/workflows/validate.yml`.

**Source of truth:** `docs/superpowers/specs/2026-06-13-tooling-recommender-design.md` (survived two adversarial review passes; all P1 closed). Grounded by the dogfood run in `docs/superpowers/specs/research/tooling-discovery-2026/`.

**Repo placement decision:** `suggest-tooling/` is a sibling skill directory at the root of the existing `deep-research` repo (the repo becomes a two-skill repo). This makes the `marketplace_rank.py` → `github_rank.py` import a same-repo `__file__`-relative path insert (`parents[2]/scripts`), avoiding cross-repo duplication of the gate.

**Plan refinement vs spec (flag to maintainer):** the spec's `tooling-hats.yaml` becomes **`tooling-hats.json`** because the helper is stdlib-only and stdlib has no YAML parser. Same content, JSON shape. The `.example` ships as `tooling-hats.json.example`.

---

## File structure

| Path | Responsibility | Phase |
|---|---|---|
| `scripts/github_rank.py` (MODIFY) | Extract `fake_star_gate()` as importable function; `main()` calls it (behavior-preserving) | 1 |
| `suggest-tooling/scripts/marketplace_rank.py` (CREATE) | THE single ranker: relevance arithmetic, trust-tier cascade, scalar fake-signal gate, dedupe, composite score | 1 |
| `tests/check-marketplace-rank.sh` (CREATE) | Bash harness: feeds fixture candidate JSONs, asserts tiers/dedupe/gate/totality | 1 |
| `tests/fixtures/tooling/*.json` (CREATE) | Candidate fixtures incl. totality gap cases, dedupe case, small-N case | 1 |
| `suggest-tooling/SKILL.md` (CREATE) | Skill entry: trigger, 6-connector orchestration, candidate-JSON contract, degradation, no-auto-install banner | 2 |
| `suggest-tooling/references/tooling-discovery.md` (CREATE) | Per-channel query mechanics (spec §4) + ranking/tier rules (spec §5) | 2 |
| `suggest-tooling/references/tooling-categories.md` (CREATE) | Closed versioned category→hat taxonomy | 2 |
| `suggest-tooling/references/toolbox-output.md` (CREATE) | `research-toolbox.md` + `.json` output shape (spec §7) | 2 |
| `suggest-tooling/tooling-hats.json.example` (CREATE) | Hat weights + category→hat map template (user copies to `~/.claude/deep-research/`) | 2 |
| `SKILL.md` (MODIFY) | Add `--suggest-tooling` flag row + Phase-6 delegation line | 3 |
| `README.md` (MODIFY) | Propagate the new skill + flag (I5, same commit) | 3 |
| `suggest-tooling/evals/*.jsonl` + `rubric.md` (CREATE) | loading + e2e fixtures (5 failure modes) | 4 |
| `.github/workflows/validate.yml` (MODIFY) | Run `check-marketplace-rank.sh` + `py_compile marketplace_rank.py` | 1 |

---

## Phase 1 — Deterministic core (stdlib Python + bash test harness)

### Task 1: Extract `fake_star_gate()` from github_rank.py (behavior-preserving)

**Files:**
- Modify: `scripts/github_rank.py:111-113` (the inline gate) + add a module-level function
- Test: `tests/check-marketplace-rank.sh` (regression assertion added here; full file in Task 7)

- [ ] **Step 1: Write the failing regression assertion**

Create `tests/check-marketplace-rank.sh` with just this much for now:

```bash
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
```

- [ ] **Step 2: Run it to verify it fails**

Run: `bash tests/check-marketplace-rank.sh`
Expected: FAIL — `ImportError: cannot import name 'fake_star_gate'`.

- [ ] **Step 3: Extract the function in github_rank.py**

In `scripts/github_rank.py`, add this function above `def main()`:

```python
def fake_star_gate(
    stars: int | None,
    forks: int | None,
    open_issues: int | None,
    dependents: int | None,
) -> bool | None:
    """StarScout-derived divergence test: high stars with flat usage.

    Returns None (unknown) when stars is absent, or when ALL three usage
    inputs (forks, open_issues, dependents) are absent — there is then
    nothing to diverge from. Present-but-zero usage counts as usage data.
    Below the 500-star floor a repo never flags (too small to be worth gaming).
    """
    if stars is None:
        return None
    if forks is None and open_issues is None and dependents is None:
        return None
    usage = (forks or 0) + (open_issues or 0) + (dependents or 0)
    return stars >= 500 and usage < stars / 200
```

Then replace the inline block at the old `:111-113`:

```python
        # Fake-star divergence (StarScout-derived): high stars, flat usage.
        usage = (r.get("forks") or 0) + (r.get("open_issues") or 0) + (dep or 0)
        flags.append(stars >= 500 and usage < stars / 200)
```

with a call (preserving the original truthiness — `None` becomes `False` in main's flag list, matching prior behavior since GitHub candidates always have non-null forks/issues):

```python
        gate = fake_star_gate(stars, r.get("forks"), r.get("open_issues"), dep)
        flags.append(bool(gate))
```

- [ ] **Step 4: Run to verify it passes**

Run: `bash tests/check-marketplace-rank.sh`
Expected: `T1 PASS`. Also run `python3 -m py_compile scripts/github_rank.py` — no output.

- [ ] **Step 5: Commit**

```bash
git add scripts/github_rank.py tests/check-marketplace-rank.sh
git commit -m "refactor(github_rank): extract importable fake_star_gate() (suggest-tooling reuse)"
```

---

### Task 2: marketplace_rank.py — input contract, relevance arithmetic

**Files:**
- Create: `suggest-tooling/scripts/marketplace_rank.py`
- Create: `tests/fixtures/tooling/relevance.json`
- Test: `tests/check-marketplace-rank.sh` (append T2 block)

The candidate JSON contract (one row, emitted upstream by the skill — every field deterministic, no LLM in this script):

```
{ "id": "owner/repo", "dedup_key": "owner/repo", "channels": ["github"],
  "categories": ["eval","rag"], "category_fit": 1,
  "official": false, "verified_namespace": false, "official_publisher": false,
  "last_activity_days": 12, "stars": 800, "forks": 40, "open_issues": 5,
  "dependents_count": 3, "adoption": 3, "use_count": null, "unverified": true,
  "releases_count": 4, "signed": false, "provenance": "github",
  "is_meta_list": false, "install_command": "npx skills add owner/repo" }
```

- [ ] **Step 1: Write the failing test (append to `tests/check-marketplace-rank.sh`)**

```bash
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
python3 suggest-tooling/scripts/marketplace_rank.py tests/fixtures/tooling/relevance.json | python3 - <<'PY'
import json,sys
d=json.load(sys.stdin); rows={r["id"]:r for r in d["ranking"]}
assert "c/none" not in rows, "category_fit=0 must be excluded"
assert abs(rows["a/eval"]["relevance"]-1.0)<1e-9, rows["a/eval"]
assert abs(rows["b/vat"]["relevance"]-0.4)<1e-9, rows["b/vat"]
print("  T2 PASS")
PY
```

- [ ] **Step 2: Run to verify it fails**

Run: `bash tests/check-marketplace-rank.sh`
Expected: FAIL — file `marketplace_rank.py` not found.

- [ ] **Step 3: Create marketplace_rank.py (skeleton + relevance)**

```python
#!/usr/bin/env python3
"""Composite rank + trust grading for suggest-tooling candidates.

Stdlib-only, zero network, zero LLM (invariant I4a). Discovery and
topic->category classification happen UPSTREAM in the suggest-tooling skill's
Bash/MCP/LLM layer; this script consumes a pre-classified candidate JSON and
emits a deterministic, auditable ranking with discrete trust tiers.

Reuses fake_star_gate() from the sibling scripts/github_rank.py (single source
of truth for the GitHub fake-star divergence test).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from github_rank import fake_star_gate  # noqa: E402

DEFAULT_HATS = {"ai-engineer": 1.0, "devsecops": 0.7, "platform": 0.5, "fr-b2b": 0.4}
DEFAULT_CATEGORY_HAT = {
    "eval": "ai-engineer", "rag": "ai-engineer", "mcp-server": "ai-engineer",
    "prompt-eng": "ai-engineer", "agent-orchestration": "ai-engineer",
    "observability": "platform", "k8s-security": "devsecops",
    "secrets-mgmt": "devsecops", "ci-cd": "devsecops", "scraping": "ai-engineer",
    "fr-b2b-ops": "fr-b2b",
}


def load_json(path: str):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        sys.exit(f"FAIL: cannot load {path}: {exc}")


def relevance(cand: dict, hats: dict, cat_hat: dict) -> float:
    if not cand.get("category_fit"):
        return 0.0
    weights = [
        hats.get(cat_hat.get(c, ""), 0.0) for c in cand.get("categories", [])
    ]
    return max(weights, default=0.0)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("candidates")
    p.add_argument("--hats", default=None, help="tooling-hats.json (user-scope)")
    p.add_argument("--top", type=int, default=25)
    args = p.parse_args()

    rows = load_json(args.candidates)
    if not isinstance(rows, list):
        sys.exit("FAIL: candidates must be a JSON array")

    hats, cat_hat = DEFAULT_HATS, DEFAULT_CATEGORY_HAT
    if args.hats:
        cfg = load_json(args.hats)
        hats = cfg.get("hats", DEFAULT_HATS)
        cat_hat = cfg.get("category_hat", DEFAULT_CATEGORY_HAT)

    ranked = []
    for c in rows:
        if c.get("is_meta_list"):
            continue
        rel = relevance(c, hats, cat_hat)
        if rel == 0.0:
            continue
        ranked.append({"id": c.get("id"), "relevance": round(rel, 4)})

    ranked.sort(key=lambda x: x["relevance"], reverse=True)
    print(json.dumps({"ranking": ranked[: args.top]}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run to verify it passes**

Run: `bash tests/check-marketplace-rank.sh`
Expected: `T2 PASS`.

- [ ] **Step 5: Commit**

```bash
git add suggest-tooling/scripts/marketplace_rank.py tests/fixtures/tooling/relevance.json tests/check-marketplace-rank.sh
git commit -m "feat(marketplace_rank): candidate contract + hat-weighted relevance"
```

---

### Task 3: Trust-tier cascade (total, null-safe) — spec §5.2

**Files:**
- Modify: `suggest-tooling/scripts/marketplace_rank.py` (add `trust_tier`, wire into output)
- Create: `tests/fixtures/tooling/tiers.json`
- Test: append T3 block

- [ ] **Step 1: Write the failing test**

```bash
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
python3 suggest-tooling/scripts/marketplace_rank.py tests/fixtures/tooling/tiers.json | python3 - <<'PY'
import json,sys
r={x["id"]:x["trust_tier"] for x in json.load(sys.stdin)["ranking"]}
exp={"official_verified":"VERIFIED","official_null_div":"COMMUNITY","community_active":"MAINTAINED",
     "gap_120d_nulladopt":"COMMUNITY","stale":"CAUTION","all_null":"CAUTION"}
for k,v in exp.items():
    assert r.get(k)==v, f"{k}: got {r.get(k)} want {v}"
print("  T3 PASS (totality + null-safety verified)")
PY
```

Note the load-bearing cases: `official_null_div` (official but the divergence gate never ran → COMMUNITY, not vacuous-VERIFIED), `gap_120d_nulladopt` (90–180d + null adoption → COMMUNITY, not a gap), `all_null` (null activity → else→CAUTION, no crash).

- [ ] **Step 2: Run to verify it fails**

Run: `bash tests/check-marketplace-rank.sh`
Expected: FAIL — `KeyError: 'trust_tier'`.

- [ ] **Step 3: Add the cascade to marketplace_rank.py**

Add this function (verbatim implementation of spec §5.2; `fake_signal_flag` is set in Task 4 — for now compute it inline for GitHub via the gate, scalar channels get `None`):

```python
def trust_tier(cand: dict) -> str:
    official = bool(
        cand.get("official")
        or cand.get("verified_namespace")
        or cand.get("official_publisher")
    )
    lad = cand.get("last_activity_days")
    activity_known = lad is not None
    maintained = activity_known and lad <= 90
    stale = activity_known and lad > 180
    adoption = cand.get("adoption")
    adoption_known = adoption is not None
    adopted = adoption_known and adoption > 0
    flag = cand.get("fake_signal_flag")
    divergence_known = flag is not None

    if flag is True:
        return "CAUTION"
    if stale:
        return "CAUTION"
    if official and maintained and divergence_known and flag is not True:
        return "VERIFIED"
    if (not official) and maintained and adopted and flag is not True:
        return "MAINTAINED"
    if maintained or adoption_known or divergence_known:
        return "COMMUNITY"
    return "CAUTION"
```

In `main()`, before computing tiers, set the GitHub divergence flag inline (Task 4 generalizes this):

```python
        if "github" in c.get("channels", []):
            c["fake_signal_flag"] = fake_star_gate(
                c.get("stars"), c.get("forks"),
                c.get("open_issues"), c.get("dependents_count"),
            )
        else:
            c.setdefault("fake_signal_flag", None)
```

And enrich the appended row: `ranked.append({"id": c.get("id"), "relevance": round(rel, 4), "trust_tier": trust_tier(c)})`.

- [ ] **Step 4: Run to verify it passes**

Run: `bash tests/check-marketplace-rank.sh`
Expected: `T3 PASS (totality + null-safety verified)`.

- [ ] **Step 5: Commit**

```bash
git add suggest-tooling/scripts/marketplace_rank.py tests/fixtures/tooling/tiers.json tests/check-marketplace-rank.sh
git commit -m "feat(marketplace_rank): total null-safe trust-tier cascade (spec 5.2)"
```

---

### Task 4: Scalar fake-signal gate + small-N guard — spec §5.3

**Files:**
- Modify: `suggest-tooling/scripts/marketplace_rank.py`
- Create: `tests/fixtures/tooling/scalar_smalln.json` (N=3) and `tests/fixtures/tooling/scalar_bign.json` (N=10)
- Test: append T4 block

- [ ] **Step 1: Write the failing test**

```bash
echo "== T4: scalar fake-signal gate fires only at N>=8 =="
python3 - <<'PY'
import json
# N=3 smithery set: high-useCount unverified, no github dependents -> must NOT flag (small N)
small=[{"id":f"s/{i}","dedup_key":f"s/{i}","channels":["smithery"],"categories":["mcp-server"],
 "category_fit":1,"official":False,"verified_namespace":False,"official_publisher":False,
 "last_activity_days":10,"stars":None,"forks":None,"open_issues":None,"dependents_count":None,
 "adoption":uc,"use_count":uc,"unverified":True,"releases_count":None,"signed":None,
 "provenance":"smithery","is_meta_list":False,"install_command":"x"} for i,uc in enumerate([10,20,9000])]
json.dump(small, open("tests/fixtures/tooling/scalar_smalln.json","w"))
big=[{"id":f"b/{i}","dedup_key":f"b/{i}","channels":["smithery"],"categories":["mcp-server"],
 "category_fit":1,"official":False,"verified_namespace":False,"official_publisher":False,
 "last_activity_days":10,"stars":None,"forks":None,"open_issues":None,"dependents_count":None,
 "adoption":uc,"use_count":uc,"unverified":True,"releases_count":None,"signed":None,
 "provenance":"smithery","is_meta_list":False,"install_command":"x"} for i,uc in enumerate([5,6,7,8,9,10,11,12,13,9000])]
json.dump(big, open("tests/fixtures/tooling/scalar_bign.json","w"))
PY
python3 suggest-tooling/scripts/marketplace_rank.py tests/fixtures/tooling/scalar_smalln.json | python3 - <<'PY'
import json,sys
flags=[x["trust_evidence"]["fake_signal_flag"] for x in json.load(sys.stdin)["ranking"]]
assert all(f is None for f in flags), f"small N must not flag: {flags}"
print("  small-N: no spurious flag OK")
PY
python3 suggest-tooling/scripts/marketplace_rank.py tests/fixtures/tooling/scalar_bign.json | python3 - <<'PY'
import json,sys
rows={x["id"]:x for x in json.load(sys.stdin)["ranking"]}
assert rows["b/9"]["trust_evidence"]["fake_signal_flag"] is True, "the 9000-useCount outlier must flag at N=10"
assert rows["b/9"]["trust_tier"]=="CAUTION"
print("  T4 PASS")
PY
```

- [ ] **Step 2: Run to verify it fails**

Run: `bash tests/check-marketplace-rank.sh`
Expected: FAIL — `trust_evidence` key missing / flag not computed.

- [ ] **Step 3: Implement the scalar gate + emit trust_evidence**

Add constants near the top: `SCALAR_MIN_N = 8` and `SCALAR_PCTL = 0.90`. Add:

```python
def percentile(values: list[float], q: float) -> float:
    s = sorted(values)
    if not s:
        return 0.0
    idx = min(int(q * (len(s) - 1) + 0.5), len(s) - 1)
    return s[idx]


def apply_scalar_gate(rows: list[dict]) -> None:
    """Flag non-GitHub scalar-count outliers; only meaningful at N>=8."""
    scalar = [
        c for c in rows
        if "github" not in c.get("channels", []) and c.get("use_count") is not None
    ]
    if len(scalar) < SCALAR_MIN_N:
        for c in scalar:
            c.setdefault("fake_signal_flag", None)
        return
    thresh = percentile([c["use_count"] for c in scalar], SCALAR_PCTL)
    for c in scalar:
        loud = c["use_count"] >= thresh
        no_trace = not c.get("dependents_count")
        c["fake_signal_flag"] = bool(
            c.get("unverified") and loud and no_trace
        )
```

In `main()`, after the GitHub-flag loop and before tiering, call `apply_scalar_gate(rows)`. Replace the row append with the full evidence payload:

```python
        ranked.append({
            "id": c.get("id"),
            "channels": c.get("channels", []),
            "relevance": round(rel, 4),
            "trust_tier": trust_tier(c),
            "install_command": c.get("install_command"),
            "trust_evidence": {
                "official": official_of(c),
                "verified_namespace": bool(c.get("verified_namespace")),
                "signed": c.get("signed"),
                "last_activity_days": c.get("last_activity_days"),
                "adoption": c.get("adoption"),
                "stars": c.get("stars"),
                "fake_signal_flag": c.get("fake_signal_flag"),
            },
        })
```

Add a helper `def official_of(c): return bool(c.get("official") or c.get("verified_namespace") or c.get("official_publisher"))` and reuse it inside `trust_tier`.

- [ ] **Step 4: Run to verify it passes**

Run: `bash tests/check-marketplace-rank.sh`
Expected: `T4 PASS`.

- [ ] **Step 5: Commit**

```bash
git add suggest-tooling/scripts/marketplace_rank.py tests/fixtures/tooling/scalar_smalln.json tests/fixtures/tooling/scalar_bign.json tests/check-marketplace-rank.sh
git commit -m "feat(marketplace_rank): scalar fake-signal gate with N>=8 guard (spec 5.3)"
```

---

### Task 5: Cross-channel dedupe + trust-conservative merge — spec §5.4

**Files:**
- Modify: `suggest-tooling/scripts/marketplace_rank.py`
- Create: `tests/fixtures/tooling/dedupe.json`
- Test: append T5 block

- [ ] **Step 1: Write the failing test**

```bash
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
python3 suggest-tooling/scripts/marketplace_rank.py tests/fixtures/tooling/dedupe.json | python3 - <<'PY'
import json,sys
rk=json.load(sys.stdin)["ranking"]
assert len(rk)==1, f"must collapse to one row, got {len(rk)}"
row=rk[0]
assert set(row["channels"])=={"mcp-registry","smithery"}, row["channels"]
# strongest verification kept (verified), most cautious activity kept (300d -> stale -> CAUTION)
assert row["trust_evidence"]["verified_namespace"] is True
assert row["trust_tier"]=="CAUTION", f"most-cautious activity (300d) wins -> {row['trust_tier']}"
print("  T5 PASS")
PY
```

- [ ] **Step 2: Run to verify it fails**

Run: `bash tests/check-marketplace-rank.sh`
Expected: FAIL — two rows returned (no dedupe yet).

- [ ] **Step 3: Implement dedupe (commutative merge → order-independent)**

```python
def merge_pair(a: dict, b: dict) -> dict:
    """Trust-conservative, commutative merge of two same-key candidates."""
    def strongest(k):
        return bool(a.get(k)) or bool(b.get(k))
    def oldest(k):  # most-cautious activity = largest idle days; None = unknown
        va, vb = a.get(k), b.get(k)
        vals = [v for v in (va, vb) if v is not None]
        return max(vals) if vals else None
    def cautious_flag():  # True if either flags
        fa, fb = a.get("fake_signal_flag"), b.get("fake_signal_flag")
        if fa is True or fb is True:
            return True
        if fa is None and fb is None:
            return None
        return False
    m = dict(a)
    m["channels"] = sorted(set(a.get("channels", [])) | set(b.get("channels", [])))
    for k in ("official", "verified_namespace", "official_publisher", "signed"):
        m[k] = strongest(k)
    m["last_activity_days"] = oldest("last_activity_days")
    m["fake_signal_flag"] = cautious_flag()
    for k in ("adoption", "use_count", "stars", "dependents_count"):
        vals = [v for v in (a.get(k), b.get(k)) if v is not None]
        m[k] = max(vals) if vals else None
    m["categories"] = sorted(set(a.get("categories", [])) | set(b.get("categories", [])))
    m["category_fit"] = max(a.get("category_fit", 0), b.get("category_fit", 0))
    return m


def dedupe(rows: list[dict]) -> list[dict]:
    by_key: dict[str, dict] = {}
    order: list[str] = []
    for c in rows:
        k = c.get("dedup_key") or c.get("id")
        if k in by_key:
            by_key[k] = merge_pair(by_key[k], c)
        else:
            by_key[k] = c
            order.append(k)
    return [by_key[k] for k in order]
```

In `main()`, run `rows = dedupe(rows)` **before** the GitHub-flag loop and `apply_scalar_gate`. (Dedup first so flags/tiers compute on merged primitives.)

- [ ] **Step 4: Run to verify it passes**

Run: `bash tests/check-marketplace-rank.sh`
Expected: `T5 PASS`.

- [ ] **Step 5: Commit**

```bash
git add suggest-tooling/scripts/marketplace_rank.py tests/fixtures/tooling/dedupe.json tests/check-marketplace-rank.sh
git commit -m "feat(marketplace_rank): cross-channel trust-conservative dedupe (spec 5.4)"
```

---

### Task 6: Composite ranking score + component renormalization — spec §5.1

**Files:**
- Modify: `suggest-tooling/scripts/marketplace_rank.py`
- Create: `tests/fixtures/tooling/ranking.json`
- Test: append T6 block

- [ ] **Step 1: Write the failing test**

```bash
echo "== T6: composite score + renormalize printed; tier-then-relevance order =="
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
python3 suggest-tooling/scripts/marketplace_rank.py tests/fixtures/tooling/ranking.json | python3 - <<'PY'
import json,sys
d=json.load(sys.stdin)
assert "effective_weights" in d and "dropped_components" in d, d.keys()
ids=[r["id"] for r in d["ranking"]]
# VERIFIED ranks before CAUTION regardless of raw score
assert ids[0]=="hi/rel" and ids[1]=="lo/caution", ids
assert all("score" in r for r in d["ranking"])
print("  T6 PASS")
PY
echo "  ALL marketplace_rank checks PASS"
```

- [ ] **Step 2: Run to verify it fails**

Run: `bash tests/check-marketplace-rank.sh`
Expected: FAIL — no `effective_weights`/`score`.

- [ ] **Step 3: Implement composite scoring + tier-major ordering**

Add constants: `RANK_WEIGHTS = {"relevance": 0.40, "maintenance": 0.25, "adoption": 0.20, "popularity": 0.15}` and `TIER_ORDER = {"VERIFIED": 0, "MAINTAINED": 1, "COMMUNITY": 2, "CAUTION": 3}`.

```python
def minmax(values: list[float]) -> list[float]:
    lo, hi = min(values), max(values)
    if hi == lo:
        return [0.5] * len(values)
    return [(v - lo) / (hi - lo) for v in values]


def raw_components(rows: list[dict]) -> dict[str, list[float]]:
    import math
    rel = [r["_relevance"] for r in rows]
    maint = [
        1.0 / (1.0 + (r.get("last_activity_days") or 9999) / 30.0) for r in rows
    ]
    adopt = [math.log10((r.get("adoption") or 0) + 1) for r in rows]
    pop = [math.log10((r.get("stars") or r.get("use_count") or 0) + 1) for r in rows]
    return {"relevance": rel, "maintenance": maint, "adoption": adopt, "popularity": pop}
```

In `main()`, after dedupe/flags/relevance-filter, build the surviving list with `_relevance` stashed, compute components, drop set-wide-zero components and renormalize weights (same idiom as `github_rank.py:115-122`), compute each `score = sum(eff[k]*norm[k][i])`, then sort by `(TIER_ORDER[tier], -score)` and print `{"effective_weights", "dropped_components", "ranking": [...]}` with `score` rounded into each row. Reuse `github_rank.py`'s renormalization block structure (do not re-derive).

- [ ] **Step 4: Run to verify it passes**

Run: `bash tests/check-marketplace-rank.sh`
Expected: `T6 PASS` and `ALL marketplace_rank checks PASS`.

- [ ] **Step 5: Commit**

```bash
git add suggest-tooling/scripts/marketplace_rank.py tests/fixtures/tooling/ranking.json tests/check-marketplace-rank.sh
git commit -m "feat(marketplace_rank): composite score + tier-major ordering (spec 5.1)"
```

---

### Task 7: Wire into CI + py_compile

**Files:**
- Modify: `.github/workflows/validate.yml`

- [ ] **Step 1: Add the check + compile step**

In `.github/workflows/validate.yml`, after the existing check invocations, add:

```yaml
      - name: marketplace_rank unit + regression checks
        run: |
          python3 -m py_compile scripts/github_rank.py suggest-tooling/scripts/marketplace_rank.py
          bash tests/check-marketplace-rank.sh
```

- [ ] **Step 2: Run the full local suite to verify nothing regressed**

Run:
```bash
bash tests/check-marketplace-rank.sh
bash tests/check-cross-references.sh
bash tests/check-provenance.sh
python3 -m py_compile scripts/github_rank.py suggest-tooling/scripts/marketplace_rank.py
```
Expected: all pass; provenance unchanged (no report edit).

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/validate.yml
git commit -m "ci: run marketplace_rank checks in validate workflow"
```

---

## Phase 2 — suggest-tooling skill surface (markdown, no executable connector code)

### Task 8: suggest-tooling/SKILL.md

**Files:**
- Create: `suggest-tooling/SKILL.md`

- [ ] **Step 1: Author SKILL.md** following the `deep-research/SKILL.md` conventions (rules/ai-engineering.md frontmatter) and the spec. Required content, transcribed/derived from the spec — NOT placeholders:
  - **Frontmatter:** `name: suggest-tooling`; `description:` leads with semantics ("Propose work-relevant Claude Code skills/plugins/MCP servers from a finished deep-research run; trust-graded; never auto-installed") + FR/EN triggers + a `Do NOT activate for:` block (single-fact tool lookup, installing tools, non-Claude-ecosystem tools); `allowed-tools:` = `Read, Write, Glob, Grep, AskUserQuestion, Bash(python3 *), Bash(gh *), Bash(curl -s *), Bash(git *), mcp__tavily__tavily_search, mcp__tavily__tavily_extract`; `argument-hint: "<research-run-dir>"`; `user-invocable: true`.
  - **Trigger:** `/suggest-tooling <run-dir>` and delegation from `deep-research --suggest-tooling`.
  - **Workflow:** (1) read the run's `research-plan.md`/`research-report.md` to get work-relevant topics; (2) per §3, classify topics→categories (closed taxonomy in `references/tooling-categories.md`); (3) query the 6 connectors per `references/tooling-discovery.md`, each independently degradable; (4) build the candidate JSON (the contract in Task 2); (5) `python3 suggest-tooling/scripts/marketplace_rank.py candidates.json --hats ~/.claude/deep-research/tooling-hats.json`; (6) render `research-toolbox.md` + `.json` per `references/toolbox-output.md`.
  - **Non-negotiables:** propose-never-install (no `/plugin install`, no `npx skills add` executed); all listings/READMEs untrusted (A6); awesome-lists seed-only; the script is the only place scores/tiers are computed.
  - **Degradation table:** per channel (Smithery no key → skip+record; `gh` absent → Tavily fallback; etc.).

- [ ] **Step 2: Validate** `bash tests/check-cross-references.sh` (links resolve). Commit:

```bash
git add suggest-tooling/SKILL.md
git commit -m "feat(suggest-tooling): skill entry point + 6-connector orchestration"
```

---

### Task 9: references/ (discovery, categories) + hats example

**Files:**
- Create: `suggest-tooling/references/tooling-discovery.md` — transcribe spec §4 (per-channel query mechanics table + degradation) and §5 (ranking + the §5.2 tier cascade + §5.3 scalar gate + §5.4 dedupe). One level deep, no cross-links to the other reference file (ai-engineering rule).
- Create: `suggest-tooling/references/tooling-categories.md` — the **closed versioned** taxonomy: the category list (no ellipsis) + the category→hat map, matching `DEFAULT_CATEGORY_HAT` in `marketplace_rank.py` exactly.
- Create: `suggest-tooling/tooling-hats.json.example`:

```json
{
  "hats": {"ai-engineer": 1.0, "devsecops": 0.7, "platform": 0.5, "fr-b2b": 0.4},
  "category_hat": {
    "eval": "ai-engineer", "rag": "ai-engineer", "mcp-server": "ai-engineer",
    "prompt-eng": "ai-engineer", "agent-orchestration": "ai-engineer",
    "scraping": "ai-engineer", "observability": "platform",
    "k8s-security": "devsecops", "secrets-mgmt": "devsecops",
    "ci-cd": "devsecops", "fr-b2b-ops": "fr-b2b"
  }
}
```

- [ ] **Consistency gate:** the category keys in `tooling-categories.md`, `tooling-hats.json.example`, and `DEFAULT_CATEGORY_HAT` must be identical sets. Add this assertion to `tests/check-marketplace-rank.sh`:

```bash
echo "== T9: taxonomy parity (script default == example) =="
python3 - <<'PY'
import json,sys; sys.path.insert(0,"suggest-tooling/scripts")
import marketplace_rank as m
ex=json.load(open("suggest-tooling/tooling-hats.json.example"))
assert set(m.DEFAULT_CATEGORY_HAT)==set(ex["category_hat"]), "category sets diverged"
assert set(m.DEFAULT_HATS)==set(ex["hats"])
print("  T9 PASS")
PY
```

- [ ] **Commit:**

```bash
git add suggest-tooling/references/ suggest-tooling/tooling-hats.json.example tests/check-marketplace-rank.sh
git commit -m "feat(suggest-tooling): discovery + closed category taxonomy + hats example"
```

---

### Task 10: references/toolbox-output.md (the 5th artifact shape)

**Files:**
- Create: `suggest-tooling/references/toolbox-output.md`

- [ ] **Step 1: Author** the `research-toolbox.md` structure (spec §7): scope banner ("proposals only, never auto-installed; all listings untrusted") · recommendations grouped by category, each row `{tool, channels[], relevance, trust_tier, trust_evidence[], install_command (shown)}`, sorted tier-major then relevance · `CAUTION — vet manually` subheading rule · "no candidate surfaced" for empty categories · degradation note · `research-toolbox.json` sidecar mirroring `marketplace_rank.py` output. Commit:

```bash
git add suggest-tooling/references/toolbox-output.md
git commit -m "docs(suggest-tooling): research-toolbox output contract (spec 7)"
```

---

## Phase 3 — deep-research delegation flag (I5: same-commit propagation)

### Task 11: `--suggest-tooling` flag + Phase-6 delegation + README

**Files:**
- Modify: `SKILL.md` (flags table + Phase 6) — the ONLY change to the grounding engine
- Modify: `README.md` (propagate, same commit per I5)

- [ ] **Step 1: Add the flag row** to the `SKILL.md` Inputs flags table:

```
| `--suggest-tooling` | boolean | off | After Phase 6, delegate the finished run to the `suggest-tooling` sibling skill (proposes work-relevant tools; writes `research-toolbox.md`). Default OFF — runs are byte-identical without it. The four-artifact contract is unchanged: the sibling, not this engine, writes the 5th file. |
```

- [ ] **Step 2: Add a Phase-6 delegation line** at the end of the Phase 6 section (after artifact write + gate verification), explicitly scoped so it does not violate the "emit only four artifacts" constraint:

```
8. **Conditional delegation (only if `--suggest-tooling`).** After the four artifacts are written and the gate verdict is PASS/quoted, invoke the `suggest-tooling` sibling skill on the invocation CWD, passing the work-relevant topics flagged in Phase 0 step 3. This engine still emits exactly four artifacts; `suggest-tooling` (a separate skill) writes `research-toolbox.md`. If the sibling is absent, print one neutral line and finish — the four artifacts are unaffected. Default OFF: zero behavior change when the flag is unset.
```

- [ ] **Step 3: Verify the four-artifact contract prose is untouched** elsewhere — grep `SKILL.md` for "four artifacts" / "Emit only" and confirm those Scope-Constraint sentences are unchanged (the lock still binds the engine). The flag adds an *opt-in delegation*, not engine meta-commentary.

- [ ] **Step 4: Propagate to README.md** (I5): add `suggest-tooling` to the architecture/Extending section and the flag to any flags listing, same commit.

- [ ] **Step 5: Run provenance + cross-ref checks** (no report edit → provenance must still pass):

```bash
bash tests/check-provenance.sh
bash tests/check-cross-references.sh
```
Expected: both pass.

- [ ] **Step 6: Commit (single commit, both files):**

```bash
git add SKILL.md README.md
git commit -m "feat(deep-research): default-OFF --suggest-tooling delegation flag (4-artifact contract intact)"
```

---

## Phase 4 — evals (five failure modes)

### Task 12: suggest-tooling/evals/

**Files:**
- Create: `suggest-tooling/evals/loading.jsonl`, `suggest-tooling/evals/e2e.jsonl`, `suggest-tooling/evals/rubric.md`
- Create: `suggest-tooling/evals/fixtures/` (a minimal finished-run dir for e2e)

- [ ] **Step 1: Author fixtures, one per failure mode** (spec §9):
  - **hijacker:** a finished run on a non-work-relevant topic (French medieval history) + `--suggest-tooling` → expect empty toolbox + "no work-relevant topics" note.
  - **silent:** a "RAG eval" run → expect ≥1 candidate.
  - **fragile:** topic "retrieval evaluation" (near-miss of "RAG eval") → expect mapping to `eval`/`rag` + candidates surfaced.
  - **drifter:** multi-topic run → recommendations scoped to work-relevant topics only.
  - **overachiever:** assert no install executed, no write outside run CWD, no prose beyond evidence.
  - The `marketplace_rank.py` totality/dedupe/small-N unit cases already live in `tests/check-marketplace-rank.sh` (Phase 1).

- [ ] **Step 2: rubric.md** scores activation correctness + output well-formedness + tier correctness, mirroring `deep-research/evals/rubric.md`.

- [ ] **Step 3: Commit:**

```bash
git add suggest-tooling/evals/
git commit -m "test(suggest-tooling): loading + e2e fixtures for the five failure modes"
```

---

## Final verification (before declaring done)

- [ ] **Run the full local suite** (Extension protocol):

```bash
bash tests/check-marketplace-rank.sh
bash tests/check-cross-references.sh
bash tests/check-provenance.sh
bash tests/check-schema.sh tests/fixtures/research-sources.json tests/fixtures/research-evidence.json
python3 -m py_compile scripts/github_rank.py suggest-tooling/scripts/marketplace_rank.py
```
Expected: every command exits 0; quote the output.

- [ ] **Confirm CI green** on push (`.github/workflows/validate.yml`).

- [ ] **Close trackers** (spec §11): post a one-line outcome on Linear AI-30 (implemented as `suggest-tooling`) and AI-40 (subsumed by the six-channel connector set).

- [ ] **Run `skill-harness`** on `suggest-tooling/` for the adversarial skill-quality pass.
