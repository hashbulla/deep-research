#!/usr/bin/env python3
"""Repeat named fixtures n times per model with the response cache BYPASSED.

Generalises repeat_blockers.py: takes fixture ids on the command line, so the same instrument
covers release blockers (must not leak) and the positives nearest a new negative clause (must
still fire — the silent-skill failure mode a boundary edit risks).

Cache is bypassed on purpose (router_query, not cached_router_query): re-invoking run_evals.py
replays sha256(prompt+system+model) from disk and would print a fabricated "stable". The backend
flock is still held — concurrent `claude -p` calls corrupt each other's replies.

Usage: repeat_fixtures.py <skill_path> <reps> <model[,model...]> <id[,id...]> [corpus]
"""
from __future__ import annotations  # python3 here is 3.8.0

import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

RUNNER = Path("/home/ouroz/second-brain/20-engineering/skills/skill-generator/scripts/run_evals.py")


def main() -> int:
    spec = importlib.util.spec_from_file_location("run_evals", RUNNER)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)

    target = Path(sys.argv[1]).expanduser().resolve()
    reps = int(sys.argv[2])
    models = sys.argv[3].split(",")
    ids = sys.argv[4].split(",")

    # optional 5th arg: corpus root (defaults to the runner's own DEFAULT_CORPUS)
    corpus = (Path(sys.argv[5]) if len(sys.argv) > 5 else m.DEFAULT_CORPUS).expanduser().resolve()
    system = m.build_skill_index(corpus, target)

    fm, _ = m.split_frontmatter((target / "SKILL.md").read_text())
    name = fm["name"]
    if system.count("## " + name + "\n") != 1:
        sys.exit(f"ABORT: index does not carry exactly one entry named {name!r}")
    print(f"index OK: 1 entry for {name!r} among {system.count(chr(10) + '## ') + 1} skills")
    print(f"description chars: {len(fm['description'])} | reps={reps} models={models} ids={ids}\n")

    fixtures = {r["id"]: r for r in
                (json.loads(l) for l in (target / "evals/loading.jsonl").read_text().splitlines() if l.strip())
                if r.get("id")}
    missing = [i for i in ids if i not in fixtures]
    if missing:
        sys.exit(f"ABORT: unknown fixture ids {missing}")

    lock = m.acquire_run_lock(m._run_lock_path())
    results = {}
    try:
        for fid in ids:
            fx = fixtures[fid]
            must_fire = str(fx.get("expect", "")).lower() == "load"
            for model in models:
                verdicts = []
                for i in range(reps):
                    verdicts.append(m.classify_verdict(m.router_query(fx["prompt"], system, model, "cli")))
                    print(f"  {fid:8s} {model:7s} rep{i + 1}: {verdicts[-1]}", flush=True)
                results[(fid, model, must_fire)] = verdicts
    finally:
        lock.close()

    print(f"\n=== stability, n={reps} per pair, cache bypassed ===")
    bad = []
    for (fid, model, must_fire), vs in results.items():
        c = Counter(vs)
        if must_fire:
            hits = sum(1 for v in vs if v == name)
            ok = hits == len(vs)
            note = f"FIRES {hits}/{len(vs)}" + ("" if ok else "  <-- SILENT-SKILL RISK")
        else:
            leaks = sum(1 for v in vs if v == name)
            ok = leaks == 0
            note = f"LEAK {leaks}/{len(vs)}" + ("" if ok else "  <-- BLOCKER LEAK")
        nv = sum(1 for v in vs if v == m.NO_VERDICT)
        if nv:
            note += f"  +{nv}xNO_VERDICT"
            ok = False
        if not ok:
            bad.append(f"{fid}/{model}")
        print(f"  {fid:8s} {model:7s} {'must fire ' if must_fire else 'must skip '} {dict(c)}  -> {note}")

    print(f"\nOVERALL: {'all pairs clean' if not bad else 'REVIEW: ' + ', '.join(bad)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
