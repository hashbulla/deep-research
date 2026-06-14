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
from typing import Any

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
SCALAR_MIN_N = 8
SCALAR_PCTL = 0.90
MAINTAINED_DAYS = 90
STALE_DAYS = 180


def percentile(values: list[float], q: float) -> float:
    s = sorted(values)
    if not s:
        return 0.0
    # nearest-rank via midpoint rounding (deterministic; not numpy linear interpolation)
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
        c["fake_signal_flag"] = bool(c.get("unverified") and loud and no_trace)


def merge_pair(a: dict, b: dict) -> dict:
    """Trust-conservative, commutative merge of two same-key candidates."""
    def strongest(k: str) -> bool:
        return bool(a.get(k)) or bool(b.get(k))

    def oldest(k: str) -> int | None:  # most-cautious activity = largest idle days; None = unknown
        vals = [v for v in (a.get(k), b.get(k)) if v is not None]
        return max(vals) if vals else None

    def cautious_flag() -> bool | None:  # True if either flags
        fa, fb = a.get("fake_signal_flag"), b.get("fake_signal_flag")
        if fa is True or fb is True:
            return True
        if fa is None and fb is None:
            return None
        return False

    # Canonical representative for trust-neutral DISPLAY fields (id/install_command/
    # provenance/releases_count): pick deterministically (smallest id) so the whole
    # merge is order-independent, not just the trust signals.
    rep = a if (a.get("id") or "") <= (b.get("id") or "") else b
    m = dict(rep)
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
    # Inverted signals: True is the unsafe value -> OR is the trust-conservative,
    # order-independent merge (without this, unverified/is_meta_list are first-wins,
    # and unverified leaks into apply_scalar_gate's flag, breaking order-independence).
    m["unverified"] = bool(a.get("unverified")) or bool(b.get("unverified"))
    m["is_meta_list"] = bool(a.get("is_meta_list")) or bool(b.get("is_meta_list"))
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


def load_json(path: str) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        sys.exit(f"FAIL: cannot load {path}: {exc}")


def official_of(c: dict) -> bool:
    return bool(
        c.get("official") or c.get("verified_namespace") or c.get("official_publisher")
    )


def trust_tier(cand: dict) -> str:
    official = official_of(cand)
    lad = cand.get("last_activity_days")
    activity_known = lad is not None
    maintained = activity_known and lad <= MAINTAINED_DAYS
    stale = activity_known and lad > STALE_DAYS
    adoption = cand.get("adoption")
    adoption_known = adoption is not None
    adopted = adoption_known and adoption > 0
    flag = cand.get("fake_signal_flag")
    divergence_known = flag is not None
    signed = bool(cand.get("signed"))
    # VERIFIED needs a corroborating signal beyond identity alone (anti-vacuity):
    # the fake-signal gate actually ran, OR adoption is known, OR provenance is signed.
    corroborated = divergence_known or adoption_known or signed

    if flag is True:
        return "CAUTION"
    if stale:
        return "CAUTION"
    if official and maintained and corroborated and flag is not True:
        return "VERIFIED"
    if (not official) and maintained and adopted and flag is not True:
        return "MAINTAINED"
    if maintained or adoption_known or divergence_known:
        return "COMMUNITY"
    return "CAUTION"


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

    rows = dedupe(rows)

    hats, cat_hat = DEFAULT_HATS, DEFAULT_CATEGORY_HAT
    if args.hats:
        cfg = load_json(args.hats)
        hats = cfg.get("hats", DEFAULT_HATS)
        cat_hat = cfg.get("category_hat", DEFAULT_CATEGORY_HAT)

    for c in rows:
        if "github" in c.get("channels", []):
            c["fake_signal_flag"] = fake_star_gate(
                c.get("stars"), c.get("forks"),
                c.get("open_issues"), c.get("dependents_count"),
            )
        else:
            c.setdefault("fake_signal_flag", None)

    apply_scalar_gate(rows)

    ranked = []
    for c in rows:
        if c.get("is_meta_list"):
            continue
        rel = relevance(c, hats, cat_hat)
        if rel == 0.0:
            continue
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

    ranked.sort(key=lambda x: x["relevance"], reverse=True)
    print(json.dumps({"ranking": ranked[: args.top]}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
