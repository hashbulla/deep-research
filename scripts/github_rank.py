#!/usr/bin/env python3
"""Composite ranking for GitHub repository candidates.

Stdlib-only, zero network, zero LLM calls (invariant I4a). Scoring only:
retrieval happens upstream via the gh CLI and ecosyste.ms (see
references/github-research.md); this script consumes the pre-collected
candidate JSON and emits a deterministic, auditable ranking.

Weights (AI-121): expert_overlap 0.30 · log_stars 0.20 · recency 0.20 ·
velocity 0.15 · dependents 0.10 · contributors 0.05 − fake-star penalty.
Components unavailable for the WHOLE candidate set (no experts index,
dependents service down) are dropped and their weight redistributed
proportionally — the effective weights are printed in the output, never
applied silently.

Usage:
  python3 scripts/github_rank.py candidates.json \
      [--experts-index experts-index.json] [--top 10]

candidates.json: array of objects with full_name, stars, pushed_at,
created_at, forks, open_issues, releases_count, contributors_count,
dependents_count (int or null), expert_stars (int, optional).
experts-index.json: {"<owner>/<repo>": ["expert_handle", ...]} (optional).

Exit 0 on success; the ranked JSON goes to stdout.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import date, datetime
from pathlib import Path

BASE_WEIGHTS = {
    "expert_overlap": 0.30,
    "log_stars": 0.20,
    "recency": 0.20,
    "velocity": 0.15,
    "dependents": 0.10,
    "contributors": 0.05,
}
FAKE_STAR_PENALTY = 0.25


def parse_when(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def minmax(values: list[float]) -> list[float]:
    lo, hi = min(values), max(values)
    if hi == lo:
        return [0.5] * len(values)
    return [(v - lo) / (hi - lo) for v in values]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidates", help="candidate JSON (pre-collected via gh CLI)")
    parser.add_argument("--experts-index", default=None)
    parser.add_argument("--top", type=int, default=10)
    args = parser.parse_args()

    try:
        rows = json.loads(Path(args.candidates).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        sys.exit(f"FAIL: cannot load candidates: {exc}")
    if not isinstance(rows, list) or not rows:
        sys.exit("FAIL: candidates must be a non-empty JSON array")

    experts: dict[str, list[str]] = {}
    if args.experts_index:
        try:
            experts = json.loads(Path(args.experts_index).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            sys.exit(f"FAIL: cannot load experts index: {exc}")

    today = max(
        (d for r in rows if (d := parse_when(r.get("pushed_at")))), default=None
    )
    if today is None:
        sys.exit("FAIL: no parseable pushed_at in any candidate")

    raw: dict[str, list[float]] = {k: [] for k in BASE_WEIGHTS}
    flags: list[bool] = []
    for r in rows:
        stars = max(int(r.get("stars") or 0), 0)
        pushed = parse_when(r.get("pushed_at"))
        created = parse_when(r.get("created_at"))
        age_days = max((today - created).days, 30) if created else 365
        idle_days = (today - pushed).days if pushed else 9999

        expert_count = r.get("expert_stars")
        if expert_count is None:
            expert_count = len(experts.get(r.get("full_name", ""), []))
        raw["expert_overlap"].append(float(expert_count))
        raw["log_stars"].append(math.log10(stars + 1))
        raw["recency"].append(1.0 / (1.0 + idle_days / 30.0))
        raw["velocity"].append(stars / (age_days / 365.0))
        dep = r.get("dependents_count")
        raw["dependents"].append(math.log10(dep + 1) if dep is not None else math.nan)
        raw["contributors"].append(math.log10((r.get("contributors_count") or 0) + 1))

        # Fake-star divergence (StarScout-derived): high stars, flat usage.
        usage = (r.get("forks") or 0) + (r.get("open_issues") or 0) + (dep or 0)
        flags.append(stars >= 500 and usage < stars / 200)

    # Drop set-wide-unavailable components, renormalize the rest.
    active = {
        k: w
        for k, w in BASE_WEIGHTS.items()
        if any(not math.isnan(v) for v in raw[k]) and any(v != 0 for v in raw[k] if not math.isnan(v))
    }
    total_w = sum(active.values())
    effective = {k: round(w / total_w, 4) for k, w in active.items()}

    normalized = {
        k: minmax([0.0 if math.isnan(v) else v for v in raw[k]]) for k in active
    }

    ranked = []
    for i, r in enumerate(rows):
        score = sum(effective[k] * normalized[k][i] for k in active)
        if flags[i]:
            score -= FAKE_STAR_PENALTY
        ranked.append(
            {
                "full_name": r.get("full_name"),
                "score": round(score, 4),
                "fake_star_suspect": flags[i],
                "components": {k: round(normalized[k][i], 4) for k in active},
                "evidence": {
                    "stars": r.get("stars"),
                    "pushed_at": r.get("pushed_at"),
                    "dependents_count": r.get("dependents_count"),
                    "contributors_count": r.get("contributors_count"),
                    "expert_stars": raw["expert_overlap"][i]
                    if "expert_overlap" in active
                    else None,
                    "experts": experts.get(r.get("full_name", ""), []),
                },
            }
        )

    ranked.sort(key=lambda x: x["score"], reverse=True)
    print(
        json.dumps(
            {
                "effective_weights": effective,
                "dropped_components": sorted(set(BASE_WEIGHTS) - set(active)),
                "reference_date": str(today),
                "ranking": ranked[: args.top],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
