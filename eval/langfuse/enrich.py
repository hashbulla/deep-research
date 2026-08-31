"""Post-run enricher: read Collector log JSONL, redact, PATCH Langfuse observations."""
from __future__ import annotations

import argparse
import base64
import os
import sys
from pathlib import Path

from enrich_parse import parse_jsonl
from enrich_route import build_updates
from enrich_langfuse import build_request_id_index, post_updates


def _load_auth() -> tuple[str, str]:
    """Load Langfuse credentials from the secret store and compose Basic auth.

    Returns:
        (base_url, auth_header) — the secret is never printed or logged.

    Raises:
        FileNotFoundError: if the secrets file is absent.
        KeyError: if a required key is missing from the file.
    """
    env_path = Path.home() / "second-brain" / ".secrets" / "langfuse.env"
    vals: dict[str, str] = {}
    with open(env_path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            vals[k.strip()] = v.strip().strip('"').strip("'")

    pub = vals["LANGFUSE_PUBLIC_KEY"]
    sec = vals["LANGFUSE_SECRET_KEY"]
    base = vals["LANGFUSE_BASE_URL"]

    if not base.startswith("http"):
        base = "https://" + base
    base = base.rstrip("/")

    token = base64.b64encode(f"{pub}:{sec}".encode()).decode()
    auth = "Basic " + token
    return base, auth


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Enrich Langfuse observations from Collector log JSONL.",
    )
    ap.add_argument("--run", required=True, metavar="JSONL",
                    help="Path to the Collector log JSONL (e.g. .logs/claude-logs.jsonl)")
    args = ap.parse_args()

    base, auth = _load_auth()

    records = parse_jsonl(args.run)
    trace_ids = {r.trace_id for r in records if r.trace_id}

    if not trace_ids:
        print("no trace ids found in JSONL — nothing to do", file=sys.stderr)
        sys.exit(1)

    total = 0
    for tid in sorted(trace_ids):
        idx = build_request_id_index(base, auth, tid)
        trace_recs = [r for r in records if r.trace_id == tid]
        updates = build_updates(trace_recs, idx)

        if not updates:
            print(f"trace {tid}: 0 updates — skipping")
            continue

        resp = post_updates(base, auth, updates)
        errs = resp.get("errors") or []
        if errs:
            for e in errs:
                print(f"trace {tid}: ingestion error — {e}", file=sys.stderr)

        total += len(updates)
        print(f"trace {tid}: {len(updates)} observation update(s) posted")

    print(f"done: {total} update(s) across {len(trace_ids)} trace(s)")


if __name__ == "__main__":
    main()
