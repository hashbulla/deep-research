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
