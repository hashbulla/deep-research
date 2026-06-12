#!/usr/bin/env python3
"""Dual-track academic ranking + BibTeX/RIS export.

Stdlib-only, zero network, zero LLM calls (invariant I4a). Scoring and
export only: retrieval happens upstream via the open scholarly graph
(OpenAlex / arXiv / Semantic Scholar / Crossref — see
references/academic-research.md); this script consumes the pre-collected
paper JSON and emits:

  Track A (Foundational): authority — influential citations + venue
      h-index, no recency penalty.
  Track B (Emerging): 12–24-month-old papers ranked by citation
      velocity + relevance.

Components missing for the WHOLE set are dropped with weights
renormalized and printed (no silent zero-signals).

Usage:
  python3 scripts/academic_graph.py papers.json \
      [--bibtex out.bib] [--ris out.ris] [--top 10]

papers.json: array of objects with id (doi or arxivId), title, authors
(list), year, venue, published_date (ISO), citation_count,
influential_citation_count, venue_h_index (int or null), relevance
(0–1, optional), oa_status (string, optional), url.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

TRACK_A_WEIGHTS = {"influential": 0.6, "citations": 0.25, "venue_h": 0.15}
TRACK_B_WEIGHTS = {"velocity": 0.7, "relevance": 0.3}
EMERGING_WINDOW_MONTHS = (12, 24)


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


def score_track(rows: list[dict], raw: dict[str, list[float | None]], weights: dict[str, float]) -> tuple[list[float], dict[str, float]]:
    active = {
        k: w for k, w in weights.items()
        if any(v is not None for v in raw[k]) and any(v for v in raw[k] if v is not None)
    }
    if not active:
        return [0.0] * len(rows), {}
    total = sum(active.values())
    effective = {k: round(w / total, 4) for k, w in active.items()}
    norm = {k: minmax([v if v is not None else 0.0 for v in raw[k]]) for k in active}
    return [sum(effective[k] * norm[k][i] for k in active) for i in range(len(rows))], effective


def bibtex_entry(p: dict) -> str:
    key = (p.get("id") or "paper").replace("/", "_").replace(".", "_").replace(":", "_")
    authors = " and ".join(p.get("authors") or ["Unknown"])
    return (
        f"@article{{{key},\n"
        f"  title   = {{{p.get('title', 'Untitled')}}},\n"
        f"  author  = {{{authors}}},\n"
        f"  year    = {{{p.get('year', '')}}},\n"
        f"  journal = {{{p.get('venue', '')}}},\n"
        f"  url     = {{{p.get('url', '')}}},\n"
        f"  note    = {{{p.get('id', '')}}}\n"
        f"}}\n"
    )


def ris_entry(p: dict) -> str:
    lines = ["TY  - JOUR", f"TI  - {p.get('title', 'Untitled')}"]
    lines += [f"AU  - {a}" for a in (p.get("authors") or ["Unknown"])]
    lines += [
        f"PY  - {p.get('year', '')}",
        f"JO  - {p.get('venue', '')}",
        f"UR  - {p.get('url', '')}",
        f"DO  - {p.get('id', '')}",
        "ER  - ",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("papers", help="pre-collected paper JSON")
    parser.add_argument("--bibtex", default=None)
    parser.add_argument("--ris", default=None)
    parser.add_argument("--top", type=int, default=10)
    args = parser.parse_args()

    try:
        rows = json.loads(Path(args.papers).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        sys.exit(f"FAIL: cannot load papers: {exc}")
    if not isinstance(rows, list) or not rows:
        sys.exit("FAIL: papers must be a non-empty JSON array")

    # Dedupe by stable ID, first occurrence wins.
    seen: set[str] = set()
    rows = [r for r in rows if (rid := str(r.get("id", ""))) and not (rid in seen or seen.add(rid))]

    reference = max(
        (d for r in rows if (d := parse_when(r.get("published_date")))), default=None
    )
    if reference is None:
        sys.exit("FAIL: no parseable published_date in any paper")

    raw_a: dict[str, list[float | None]] = {"influential": [], "citations": [], "venue_h": []}
    raw_b: dict[str, list[float | None]] = {"velocity": [], "relevance": []}
    age_months: list[float] = []
    for r in rows:
        pub = parse_when(r.get("published_date"))
        months = max(((reference - pub).days / 30.44), 1.0) if pub else 999.0
        age_months.append(months)
        raw_a["influential"].append(float(r.get("influential_citation_count") or 0))
        raw_a["citations"].append(float(r.get("citation_count") or 0))
        vh = r.get("venue_h_index")
        raw_a["venue_h"].append(float(vh) if vh is not None else None)
        raw_b["velocity"].append((r.get("citation_count") or 0) / months)
        rel = r.get("relevance")
        raw_b["relevance"].append(float(rel) if rel is not None else None)

    scores_a, weights_a = score_track(rows, raw_a, TRACK_A_WEIGHTS)
    scores_b, weights_b = score_track(rows, raw_b, TRACK_B_WEIGHTS)

    lo, hi = EMERGING_WINDOW_MONTHS
    foundational, emerging = [], []
    for i, r in enumerate(rows):
        entry = {
            "id": r.get("id"),
            "title": r.get("title"),
            "url": r.get("url"),
            "evidence": {
                "citation_count": r.get("citation_count"),
                "influential_citation_count": r.get("influential_citation_count"),
                "velocity_per_month": round(raw_b["velocity"][i] or 0, 2),
                "venue": r.get("venue"),
                "venue_h_index": r.get("venue_h_index"),
                "age_months": round(age_months[i], 1),
                "oa_status": r.get("oa_status"),
            },
        }
        if lo <= age_months[i] <= hi:
            emerging.append({**entry, "score": round(scores_b[i], 4)})
        foundational.append({**entry, "score": round(scores_a[i], 4)})

    foundational.sort(key=lambda x: x["score"], reverse=True)
    emerging.sort(key=lambda x: x["score"], reverse=True)
    foundational = foundational[: args.top]
    emerging = emerging[: args.top]

    # Reading list = union of both tracks, deduplicated by id.
    reading_ids = {e["id"] for e in foundational} | {e["id"] for e in emerging}
    reading = [r for r in rows if r.get("id") in reading_ids]
    if args.bibtex:
        Path(args.bibtex).write_text("".join(bibtex_entry(p) for p in reading), encoding="utf-8")
    if args.ris:
        Path(args.ris).write_text("".join(ris_entry(p) for p in reading), encoding="utf-8")

    print(
        json.dumps(
            {
                "reference_date": str(reference),
                "track_a_effective_weights": weights_a,
                "track_b_effective_weights": weights_b,
                "foundational": foundational,
                "emerging": emerging,
                "exports": {"bibtex": args.bibtex, "ris": args.ris, "papers": len(reading)},
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
