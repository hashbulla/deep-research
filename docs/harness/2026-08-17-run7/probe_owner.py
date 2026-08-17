#!/usr/bin/env python3
"""Decisive A/B: is the neg-16 sonnet leak a corpus artifact or a description defect?

One variable changed. Arm A = the corpus run #6 and #7 used (~/.claude/skills, 29 skills, the
legitimate owner ABSENT). Arm B = the same 29 skills PLUS `dispatching-parallel-agents`, the owner
neg-16's boundary names, symlinked from the installed superpowers plugin.

Leak collapses in arm B  -> artifact of an under-inclusive corpus (rubric.md:9 violation).
Leak persists in arm B   -> real routing defect in the compressed description.

Cache is bypassed (router_query, not cached_router_query); the backend flock is still held.

Usage: probe_owner.py <skill_path> <reps> <model>
"""
from __future__ import annotations  # python3 here is 3.8.0; PEP 585 generics need this

import importlib.util
import sys
from collections import Counter
from pathlib import Path

RUNNER = Path("/home/ouroz/second-brain/20-engineering/skills/skill-generator/scripts/run_evals.py")
OWNER_SRC = Path.home() / ".claude/plugins/cache/claude-plugins-official/superpowers/6.3.0/skills/dispatching-parallel-agents"
FARM = Path("/tmp/claude-1000/-home-ouroz-second-brain/19de15ba-6285-41ab-9632-d14f32e100d4/scratchpad/corpus-farm")
NEG16 = "fan out a bunch of research agents on this topic and just give me the gist, no plan needed"


def build_farm(base: Path) -> Path:
    """Mirror every corpus entry as a symlink, then add the missing owner. One variable changed."""
    FARM.mkdir(parents=True, exist_ok=True)
    for child in sorted(base.iterdir()):
        link = FARM / child.name
        if link.is_symlink() or link.exists():
            continue
        link.symlink_to(child.resolve())
    owner = FARM / OWNER_SRC.name
    if not (owner.is_symlink() or owner.exists()):
        if not (OWNER_SRC / "SKILL.md").exists():
            sys.exit(f"ABORT: owner source missing: {OWNER_SRC}")
        owner.symlink_to(OWNER_SRC)
    return FARM


def roster(m, corpus: Path, target: Path) -> set[str]:
    idx = m.build_skill_index(corpus, target)
    return {l[3:].strip() for l in idx.splitlines() if l.startswith("## ")}


def main() -> int:
    m_spec = importlib.util.spec_from_file_location("run_evals", RUNNER)
    m = importlib.util.module_from_spec(m_spec)
    m_spec.loader.exec_module(m)

    target = Path(sys.argv[1]).expanduser().resolve()
    reps = int(sys.argv[2])
    model = sys.argv[3]

    base = m.DEFAULT_CORPUS.expanduser().resolve()
    farm = build_farm(base)

    arms = {"A: owner ABSENT (run #6/#7 corpus)": base, "B: owner PRESENT (+dispatching-parallel-agents)": farm}

    # Assert each arm before trusting it.
    for label, corpus in arms.items():
        r = roster(m, corpus, target)
        n_target = sum(1 for x in r if x == "deep-research")
        has_owner = "dispatching-parallel-agents" in r
        print(f"{label}\n   skills={len(r)}  deep-research entries={n_target}  owner present={has_owner}")
        if n_target != 1:
            sys.exit(f"ABORT: {label} carries {n_target} deep-research entries")
    print()

    lock = m.acquire_run_lock(m._run_lock_path())
    results = {}
    try:
        for label, corpus in arms.items():
            system = m.build_skill_index(corpus, target)
            verdicts = []
            for i in range(reps):
                verdicts.append(m.classify_verdict(m.router_query(NEG16, system, model, "cli")))
                print(f"  {label[:1]} {model} rep{i + 1}: {verdicts[-1]}", flush=True)
            results[label] = verdicts
    finally:
        lock.close()

    print(f"\n=== neg-16 / {model} / n={reps} per arm, cache bypassed ===")
    for label, vs in results.items():
        c = Counter(vs)
        leaks = sum(1 for v in vs if v == "deep-research")
        print(f"  {label}\n     {dict(c)}  -> LEAK {leaks}/{len(vs)}")

    a, b = list(results.values())
    la, lb = sum(1 for v in a if v == "deep-research"), sum(1 for v in b if v == "deep-research")
    print()
    if lb == 0 and la > 0:
        print("VERDICT: ARTIFACT — the leak disappears once the rubric-mandated owner is in the corpus.")
    elif lb > 0:
        print("VERDICT: REAL DEFECT — the leak survives with the legitimate owner present.")
    else:
        print("VERDICT: INCONCLUSIVE — no leak in either arm at this n; the earlier 2/3 was not reproduced.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
