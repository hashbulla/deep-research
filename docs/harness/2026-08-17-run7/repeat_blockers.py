#!/usr/bin/env python3
"""n>=3 repetitions on the release-blocker fixtures ONLY, with the cache bypassed.

Why this exists: re-invoking run_evals.py replays sha256(prompt+system+model) from disk and
returns byte-identical replies, manufacturing a fake-stable n=3 out of a single sample. This
driver calls router_query() directly — no cache_dir, so every call is live.

Scope: neg-07 plus the neg-08/neg-15/neg-16 succession. The succession is ONE prompt string
(verified: 29 distinct prompts across 31 fixture rows), so "4 blocker fixtures" is 2 distinct
prompts. Positives are not repeated here — DIM-1-02 asks for stability on the blockers.

Usage: repeat_blockers.py <skill_path> <reps> <model[,model...]>
"""
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

RUNNER = Path("/home/ouroz/second-brain/20-engineering/skills/skill-generator/scripts/run_evals.py")
BLOCKER_IDS = ("neg-07", "neg-16")  # neg-08/neg-15 share neg-16's prompt


def load_runner():
    spec = importlib.util.spec_from_file_location("run_evals", RUNNER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    m = load_runner()
    skill_path = Path(sys.argv[1]).expanduser().resolve()
    reps = int(sys.argv[2])
    models = sys.argv[3].split(",")

    corpus = m.DEFAULT_CORPUS.expanduser().resolve()
    system = m.build_skill_index(corpus, skill_path)

    # Assert the index before trusting anything (addendum precaution #1).
    fm, _ = m.split_frontmatter((skill_path / "SKILL.md").read_text())
    name = fm["name"]
    n_entries = system.count(f"## {name}\n")
    if n_entries != 1:
        sys.exit(f"ABORT: index carries {n_entries} entries named {name!r}, expected exactly 1")
    print(f"index assertion OK: 1 entry for {name!r}, {system.count(chr(10) + '## ') + 1} skills\n")

    fixtures = [json.loads(l) for l in (skill_path / "evals/loading.jsonl").read_text().splitlines() if l.strip()]
    targets = [f for f in fixtures if f.get("id") in BLOCKER_IDS]
    if len(targets) != len(BLOCKER_IDS):
        sys.exit(f"ABORT: found {len(targets)} blocker fixtures, expected {len(BLOCKER_IDS)}")

    lock = m.acquire_run_lock(m._run_lock_path())  # serialise against any other run_evals
    results = {}
    try:
        for fx in targets:
            fid = fx["id"]
            for model in models:
                verdicts = []
                for i in range(reps):
                    # cache bypassed on purpose: router_query, not cached_router_query
                    reply = m.router_query(fx["prompt"], system, model, "cli")
                    verdicts.append(m.classify_verdict(reply))
                    print(f"  {fid:8s} {model:7s} rep{i + 1}: {verdicts[-1]}", flush=True)
                results[f"{fid}/{model}"] = verdicts
    finally:
        lock.close()

    print("\n=== stability ===")
    unstable = []
    for key, vs in results.items():
        c = Counter(vs)
        stable = len(c) == 1
        leaked = any(v == "deep-research" for v in vs)
        nv = sum(1 for v in vs if v == m.NO_VERDICT)
        flag = "STABLE" if stable else "UNSTABLE"
        if leaked:
            flag += " +LEAK"
        if nv:
            flag += f" +{nv}xNO_VERDICT"
        if not stable or leaked or nv:
            unstable.append(key)
        print(f"  {key:22s} {dict(c)}  -> {flag}")

    print(f"\nOVERALL: {'all blocker/model pairs stable and clean' if not unstable else 'review: ' + ', '.join(unstable)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
