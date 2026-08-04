#!/usr/bin/env python3
"""Own-stack inventory sweep — category `own-stack` of the solution-space map.

This helper answers one question before the research pipeline is allowed to ask
the web anything: *do I already own a tool that solves this?* It greps the
operator's local stack corpus (playbooks, connector notes, subscription memory)
for the capability terms of the run and prints every matching line.

It runs in Phase 0/1b, BEFORE any web call (references/solution-space.md,
category `own-stack`). That ordering is the whole point: the miss it exists to
prevent — a paid unified-messaging subscription already covering the target
platform, invisible because every query named the *problem* ("Instagram
scraper") instead of the *capability class* ("unified messaging API") — is a
recall failure that no amount of downstream web search recovers.

Design posture: RECALL over precision. Every match is emitted with its file,
term, line number and excerpt, and the caller reads them. A near-miss costs one
line of reading; a silent drop costs the whole finding. There is deliberately
no relevance filter, no ranking and no threshold.

Stdlib-only, zero network — invariant I4a (.claude/CLAUDE.md).

Config (`--config`, default `~/.claude/deep-research/stack-paths.json`):

    {"schema_version": 1, "paths": ["~/.claude/playbooks", "~/notes/stack"]}

Unknown keys (`note`, `_comment`, …) are ignored. `~` is expanded; relative
paths resolve from the invocation CWD. The file is user-scope by design —
paths and subscriptions are operator context and never belong in a public repo.

Exit codes:
  0  config present and read — hits or no hits (hits are DATA, not success)
  1  bad invocation (no search terms)
  2  config absent or unparsable — the caller records the `own-stack` category
     as `degraded` in research-solution-space.json (visible, never silent)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCANNED_SUFFIXES = {".md", ".txt", ".json", ".yaml", ".yml"}
MAX_BYTES = 1024 * 1024  # 1 MiB — a bigger file is a corpus, not a stack note
EXCERPT_CHARS = 200


def parse_terms(raw: str) -> list[str]:
    """Split the comma-separated --terms value, dropping blanks, preserving order."""
    seen = []
    for chunk in (raw or "").split(","):
        term = chunk.strip()
        if term and term.lower() not in [t.lower() for t in seen]:
            seen.append(term)
    return seen


def candidate_files(base: Path) -> list[Path]:
    """Every scannable file under `base` (or `base` itself), sorted for determinism."""
    if base.is_file():
        return [base] if base.suffix.lower() in SCANNED_SUFFIXES else []
    return sorted(
        p for p in base.rglob("*")
        if p.is_file() and p.suffix.lower() in SCANNED_SUFFIXES
    )


def emit(payload: dict, out: str | None) -> None:
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if out:
        Path(out).write_text(text + "\n", encoding="utf-8")
    print(text)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--config",
        default=str(Path("~/.claude/deep-research/stack-paths.json")),
        help="stack-paths.json config (default: ~/.claude/deep-research/stack-paths.json)",
    )
    parser.add_argument(
        "--terms",
        default="",
        help="comma-separated capability terms, e.g. 'instagram,messaging,dm'",
    )
    parser.add_argument("--out", default=None, help="also write the JSON verdict to this file")
    args = parser.parse_args()

    terms = parse_terms(args.terms)
    config_path = Path(args.config).expanduser()

    if not terms:
        print(
            "FAIL: --terms is required (comma-separated capability terms, "
            "e.g. --terms 'instagram,messaging,dm')",
            file=sys.stderr,
        )
        return 1

    base_payload = {
        "config_present": False,
        "config_path": str(config_path),
        "paths_scanned": [],
        "missing_paths": [],
        "terms": terms,
        "hits": [],
        "hit_files": [],
        "skipped_files": [],
    }

    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        base_payload["error"] = f"{type(exc).__name__}: {exc}"
        emit(base_payload, args.out)
        return 2
    if not isinstance(config, dict) or not isinstance(config.get("paths"), list):
        base_payload["error"] = "config must be an object carrying a 'paths' array"
        emit(base_payload, args.out)
        return 2

    scanned: list[str] = []
    missing: list[str] = []
    skipped: list[dict] = []
    hits: list[dict] = []
    hit_files: list[str] = []
    lowered = [(t, t.lower()) for t in terms]

    for raw_path in config["paths"]:
        if not isinstance(raw_path, str) or not raw_path.strip():
            continue
        base = Path(raw_path).expanduser()
        if not base.exists():
            missing.append(str(base))
            continue
        scanned.append(str(base))
        for path in candidate_files(base):
            try:
                if path.stat().st_size > MAX_BYTES:
                    skipped.append({"file": str(path), "reason": "oversize"})
                    continue
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                skipped.append({"file": str(path), "reason": type(exc).__name__})
                continue
            name = str(path)
            for lineno, line in enumerate(text.splitlines(), start=1):
                haystack = line.lower()
                for term, needle in lowered:
                    if needle in haystack:
                        hits.append({
                            "file": name,
                            "term": term,
                            "line": lineno,
                            "excerpt": line.strip()[:EXCERPT_CHARS],
                        })
                        if name not in hit_files:
                            hit_files.append(name)

    base_payload.update({
        "config_present": True,
        "paths_scanned": scanned,
        "missing_paths": missing,
        "hits": hits,
        "hit_files": hit_files,
        "skipped_files": skipped,
    })
    emit(base_payload, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
