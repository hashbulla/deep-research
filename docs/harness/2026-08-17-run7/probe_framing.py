#!/usr/bin/env python3
"""Discriminating probe: is the neg-16 sonnet leak FRAMING-sensitive?

The corpus A/B (probe_owner.py) refuted the *corpus* hypothesis — the leak persists with the
legitimate owner in the index. It did NOT test finding #6's hypothesis, which is about the ROUTER
PROMPT's framing, not the corpus: `build_skill_index` rule 3 says "if multiple skills could match,
pick the most specific one", and for `synthese` that framing was measured to be the only lever —
strengthening the description closed no leaks, switching to a strict framing dropped them 5->2 with
the description unchanged.

Here the corpus is held CONSTANT and only rule 3 varies. One variable.

  Leak vanishes under strict framing -> framing-sensitive: the instrument cannot decide sonnet's
      real behavior, and description surgery is likely a dead end (calibrate the proxy first).
  Leak persists under strict framing  -> description defect is genuinely likely, with
      deep-research-specific evidence rather than synthese's counter-evidence.

Usage: probe_framing.py <skill_path> <reps> <model>
"""
from __future__ import annotations  # python3 here is 3.8.0

import importlib.util
import sys
from collections import Counter
from pathlib import Path

RUNNER = Path("/home/ouroz/second-brain/20-engineering/skills/skill-generator/scripts/run_evals.py")
NEG16 = "fan out a bunch of research agents on this topic and just give me the gist, no plan needed"

DEFAULT_RULE = "3. If multiple skills could match, pick the most specific one based on the user's exact intent.\n"
STRICT_RULE = ("3. Load a skill ONLY if the prompt is clearly within its stated scope. "
               "If you are uncertain, or if the prompt merely grazes a skill's domain, answer none.\n")


def main() -> int:
    spec = importlib.util.spec_from_file_location("run_evals", RUNNER)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)

    target = Path(sys.argv[1]).expanduser().resolve()
    reps = int(sys.argv[2])
    model = sys.argv[3]

    corpus = m.DEFAULT_CORPUS.expanduser().resolve()
    base_system = m.build_skill_index(corpus, target)

    if DEFAULT_RULE not in base_system:
        sys.exit("ABORT: default rule 3 not found verbatim in the index prompt — re-read build_skill_index")
    strict_system = base_system.replace(DEFAULT_RULE, STRICT_RULE)
    if strict_system == base_system:
        sys.exit("ABORT: strict substitution was a no-op")

    roster = {l[3:].strip() for l in base_system.splitlines() if l.startswith("## ")}
    if sum(1 for x in roster if x == "deep-research") != 1:
        sys.exit("ABORT: index does not carry exactly one deep-research entry")
    print(f"corpus held CONSTANT at {len(roster)} skills (owner present={'dispatching-parallel-agents' in roster})")
    print(f"only rule 3 varies; prompts differ by {abs(len(strict_system) - len(base_system))} chars\n")

    arms = {"DEFAULT framing (pick most specific)": base_system,
            "STRICT framing (only if clearly in scope)": strict_system}

    lock = m.acquire_run_lock(m._run_lock_path())
    results = {}
    try:
        for label, system in arms.items():
            verdicts = []
            for i in range(reps):
                verdicts.append(m.classify_verdict(m.router_query(NEG16, system, model, "cli")))
                print(f"  {label[:7]} {model} rep{i + 1}: {verdicts[-1]}", flush=True)
            results[label] = verdicts
    finally:
        lock.close()

    print(f"\n=== neg-16 / {model} / n={reps} per arm, cache bypassed, corpus constant ===")
    for label, vs in results.items():
        leaks = sum(1 for v in vs if v == "deep-research")
        print(f"  {label}\n     {dict(Counter(vs))}  -> LEAK {leaks}/{len(vs)}")

    d, s = list(results.values())
    ld = sum(1 for v in d if v == "deep-research")
    ls = sum(1 for v in s if v == "deep-research")
    print()
    if ls == 0 and ld > 0:
        print("VERDICT: FRAMING-SENSITIVE — strict framing closes the leak with the description")
        print("         unchanged. Same signature as finding #6 (synthese). Calibrate the proxy")
        print("         BEFORE editing a description at zero gate margin.")
    elif ls > 0:
        print("VERDICT: FRAMING-INSENSITIVE — the leak survives a strict framing, so it is not")
        print("         an artifact of rule 3. A description defect is genuinely likely.")
    else:
        print("VERDICT: INCONCLUSIVE — no leak in either arm at this n.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
