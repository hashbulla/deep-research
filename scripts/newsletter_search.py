#!/usr/bin/env python3
"""Keyword + recency search over the newsletter-signal corpus.

Stdlib-only, zero network, zero LLM calls (invariant I4a). The git-versioned
JSONL corpus is the only durable store; this helper rebuilds an FTS5 index in
:memory: on each invocation (bm25 relevance blended with a recency boost) and
falls back to a pure-Python token-overlap ranker when the host SQLite was built
without FTS5. Nothing is persisted; there is no index file to drift.

The corpus is a routing/seed signal, never a citable authority: this script
returns ranked candidate items (each pointing at a primary URL) for the skill to
re-retrieve and grade through the normal Phase-2 battery. See
references/newsletter-signal.md.

Weights: relevance 0.70 · recency 0.30 (min-max normalized over the candidate
set, like github_rank.py). Reference date for the recency decay is --as-of, else
the most recent item date in the corpus, else today — derived from data, not the
wall clock, so runs are deterministic and testable.

Usage:
  python3 scripts/newsletter_search.py "<query>" \
      [--corpus DIR] [--since YYYY-MM-DD] [--bucket B] [--top N] \
      [--as-of YYYY-MM-DD] [--ranker auto|python]

Corpus absent/empty -> exit 0 with {"corpus_present": false, "items": []} so the
skill records the degradation. Exit non-zero only on bad args or a malformed
JSONL line. The ranked JSON goes to stdout.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sqlite3
import sys
from datetime import date, datetime
from pathlib import Path

W_RELEVANCE = 0.70
W_RECENCY = 0.30
DEFAULT_CORPUS = "~/.claude/deep-research/newsletter-corpus/"
TEXT_FIELDS = ("headline", "source", "why", "tool_name", "one_liner")
TOKEN_RE = re.compile(r"[a-z0-9]+")


def parse_date(value: object) -> date | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def item_text(record: dict) -> str:
    return " ".join(str(record[f]) for f in TEXT_FIELDS if record.get(f))


def minmax(values: list[float]) -> list[float]:
    lo, hi = min(values), max(values)
    if hi == lo:
        return [0.5] * len(values)
    return [(v - lo) / (hi - lo) for v in values]


def _unzip(pairs: list[tuple[dict, date | None]]) -> tuple[list[dict], list[date | None]]:
    """Split record/date pairs back into parallel lists (empty-safe)."""
    if not pairs:
        return [], []
    records, dates = zip(*pairs)
    return list(records), list(dates)


def load_corpus(corpus_dir: Path) -> list[dict]:
    """Read every *.jsonl line in the corpus dir into record dicts.

    Raises SystemExit with file:line on a malformed line.
    """
    records: list[dict] = []
    for path in sorted(corpus_dir.glob("*.jsonl")):
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                sys.exit(f"FAIL: malformed JSON at {path}:{line_no}: {exc}")
    return records


def fts5_relevance(records: list[dict], query_tokens: list[str]) -> list[float] | None:
    """bm25 relevance per record via an in-memory FTS5 index.

    Returns one relevance score per record (0.0 for non-matches), or None if
    this SQLite build lacks FTS5 (caller falls back to the Python ranker).
    """
    try:
        con = sqlite3.connect(":memory:")
        con.execute("CREATE VIRTUAL TABLE docs USING fts5(body)")
    except sqlite3.OperationalError:
        return None

    con.executemany(
        "INSERT INTO docs(rowid, body) VALUES (?, ?)",
        [(i + 1, item_text(r)) for i, r in enumerate(records)],
    )
    relevance = [0.0] * len(records)
    if not query_tokens:
        con.close()
        return relevance

    match = " OR ".join(f'"{tok}"' for tok in query_tokens)
    # bm25() returns lower (more negative) for better matches; negate so larger = better.
    for rowid, score in con.execute(
        "SELECT rowid, bm25(docs) FROM docs WHERE docs MATCH ?", (match,)
    ):
        relevance[rowid - 1] = -float(score)
    con.close()
    return relevance


def python_relevance(records: list[dict], query_tokens: list[str]) -> list[float]:
    """Fallback relevance: distinct query/item token-set overlap, length-normalized.

    Counts distinct query tokens present (not their frequency), so a
    keyword-stuffed item cannot outrank a genuine match.
    """
    qset = set(query_tokens)
    if not qset:
        return [0.0] * len(records)
    scores: list[float] = []
    for r in records:
        toks = set(tokenize(item_text(r)))
        overlap = len(qset & toks)
        scores.append(overlap / math.sqrt(len(toks) + 1))
    return scores


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="free-text query")
    parser.add_argument("--corpus", default=DEFAULT_CORPUS)
    parser.add_argument("--since", default=None, help="lower bound on item date (YYYY-MM-DD)")
    parser.add_argument("--bucket", default=None, help="restrict to one bucket")
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--as-of", dest="as_of", default=None, help="recency reference date")
    parser.add_argument("--ranker", choices=("auto", "python"), default="auto")
    args = parser.parse_args()

    # Fail loud on a malformed date flag — silently ignoring it would return
    # unfiltered results the caller believes were constrained.
    for flag, value in (("--since", args.since), ("--as-of", args.as_of)):
        if value is not None and parse_date(value) is None:
            sys.exit(f"FAIL: {flag} must be YYYY-MM-DD, got: {value!r}")
    if args.top < 0:
        sys.exit(f"FAIL: --top must be >= 0, got: {args.top}")

    # Every return path emits this same fixed-key envelope (value-level
    # sentinels where a field is inapplicable) so consumers branch on values,
    # never on key presence.
    result: dict = {
        "corpus_present": False,
        "ranker_used": None,
        "reference_date": None,
        "effective_weights": {"relevance": W_RELEVANCE, "recency": W_RECENCY},
        "item_count": 0,
        "items": [],
        "reason": None,
    }

    def emit(**overrides: object) -> int:
        result.update(overrides)
        print(json.dumps(result, indent=2))
        return 0

    corpus_dir = Path(args.corpus).expanduser()
    if not corpus_dir.is_dir():
        return emit(reason=f"corpus dir not found: {corpus_dir}")

    records = load_corpus(corpus_dir)
    if not records:
        return emit(reason=f"corpus dir empty: {corpus_dir}")

    # The corpus exists and has records: present from here on, even if the
    # filters below exclude everything (that is "no relevant items", not a
    # degradation). Parse each record's date once and carry it alongside.
    dates = [parse_date(r.get("date")) for r in records]

    since = parse_date(args.since)
    if since is not None:
        records, dates = _unzip([(r, d) for r, d in zip(records, dates) if d and d >= since])
    if args.bucket:
        records, dates = _unzip([(r, d) for r, d in zip(records, dates)
                                 if r.get("bucket") == args.bucket])

    if not records:
        return emit(corpus_present=True,
                    reason="corpus present but no records match the filters")

    ref_date = parse_date(args.as_of) or max((d for d in dates if d), default=None) or date.today()

    query_tokens = tokenize(args.query)
    if args.ranker == "auto" and (rel := fts5_relevance(records, query_tokens)) is not None:
        relevance, ranker_used = rel, "fts5"
    else:
        relevance, ranker_used = python_relevance(records, query_tokens), "python"

    # A non-empty query with zero token overlap must signal "nothing relevant"
    # (items:[]), not dump the whole corpus as recency-ranked seeds: min-max would
    # otherwise flatten an all-zero relevance vector to 0.5 and let pure recency
    # rank every record, silently neutralizing the 0.70 relevance weight. So drop
    # non-matching records before ranking. An empty-token query (no usable terms,
    # e.g. all punctuation) is exempt: the caller asked nothing specific, so
    # recency-ranked-all is the intended behavior there.
    if query_tokens:
        kept = [(r, d, s) for r, d, s in zip(records, dates, relevance) if s > 0.0]
        if not kept:
            return emit(corpus_present=True, ranker_used=ranker_used,
                        reference_date=str(ref_date),
                        reason="corpus present but no records match the query")
        records = [r for r, _, _ in kept]
        dates = [d for _, d, _ in kept]
        relevance = [s for _, _, s in kept]

    recency_raw = [1.0 / (1.0 + (max((ref_date - d).days, 0) if d else 3650) / 30.0)
                   for d in dates]
    rel_norm = minmax(relevance)
    rec_norm = minmax(recency_raw)

    ranked = []
    for i, r in enumerate(records):
        score = W_RELEVANCE * rel_norm[i] + W_RECENCY * rec_norm[i]
        ranked.append({
            "date": r.get("date"),
            "bucket": r.get("bucket"),
            "kind": r.get("kind"),
            "headline": r.get("headline"),
            "source": r.get("source"),
            "url": r.get("url"),
            "repo_url": r.get("repo_url"),
            "why": r.get("why"),
            "tool_name": r.get("tool_name"),
            "one_liner": r.get("one_liner"),
            "score": round(score, 4),
        })
    # Stable order: score desc, then newest, then url.
    ranked.sort(key=lambda x: (-x["score"], x["date"] or "", x["url"] or ""))

    return emit(corpus_present=True, ranker_used=ranker_used, reference_date=str(ref_date),
                item_count=len(ranked), items=ranked[: args.top])


if __name__ == "__main__":
    sys.exit(main())
