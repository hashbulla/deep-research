#!/usr/bin/env python3
"""Emit a run's engine/contract accounting vector — the run's own cost anatomy.

Why this exists
---------------
The adoption eval of 2026-08 had to mine a session transcript to answer "how
much of a run is the retrieval engine, and how much is the contract?". That
answer (engine ~14% of a 18.72$ run) shaped the refonte, and re-deriving it cost
a full instrument twice. A run should hand over its own accounting instead.

What is measurable from inside a run, and what is not
----------------------------------------------------
This script deliberately does NOT report tokens or dollars, and that is not an
omission — it is the honest boundary:

- Token counts and cost live on the session's `result` event, which the running
  agent never observes. The offline instrument reads it post-hoc.
- Per-message `output_tokens` in a transcript UNDER-REPORT badly (measured
  2026-08: 283 cumulative against 155,052 at the `result` event — the per-message
  values are streaming snapshots). Anything derived from them in-run would be
  wrong by two orders of magnitude.

What IS observable in-run is the agent's own behaviour: which tools it called,
how many times, under which phase. So this emits call-level accounting plus the
classification rule, and declares the rest non-measurable — declared, never
silently absent (the house eval standard's rule).

Classification rule — ported verbatim from the pre-registered instrument
-----------------------------------------------------------------------
    engine   = a step emitting >=1 retrieval tool call
               (mcp__tavily__*, mcp__scrapling__*, WebFetch, WebSearch)
    contract = every other step (Bash, Write/Edit, Read, Agent, pure text)

A step calling both kinds counts as **engine**, exactly as the instrument
counted mixed messages, so the two accountings stay comparable.

Contract: stdlib only, zero network, zero LLM call (invariant I4a).

Usage
-----
    python3 scripts/run_accounting.py --steps steps.json [--out FILE] [--length standard]

`steps.json` is what the agent observed of its own run:

    {"steps": [{"phase": "1", "tools": ["mcp__tavily__tavily_search", ...]},
               {"phase": "6", "tools": ["Bash"]}]}
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"

# Ported verbatim from instrument/decompose-moteur-contrat.py (pre-registered
# 2026-08-11). Changing either list breaks comparability with the eval's
# published figures — amend both, and say so in the run's Methodology note.
RETRIEVAL_PREFIXES: tuple[str, ...] = ("mcp__tavily__", "mcp__scrapling__")
RETRIEVAL_EXACT: frozenset[str] = frozenset({"WebFetch", "WebSearch"})

NOT_MEASURABLE_IN_RUN: dict[str, str] = {
    "tokens": (
        "Token totals live on the session 'result' event, which the running agent "
        "never observes. Per-message output_tokens in a transcript are streaming "
        "snapshots and under-report by orders of magnitude (measured 2026-08: 283 "
        "cumulative vs 155052 at 'result')."
    ),
    "dollars": (
        "Cost is derived from the result event's modelUsage, for the same reason. "
        "It also depends on a price list and a plan (marginal cost is zero under a "
        "flat subscription), neither of which is a property of the run."
    ),
    "context_carry": (
        "The dominant cost item measured in 2026-08 (76% of a run: output re-read "
        "across turns, plus a stable preamble re-read every turn) is a property of "
        "the whole conversation, not of any step. Only a transcript exposes it."
    ),
    "how_to_obtain": (
        "Run the offline instrument over the session transcript: "
        "40-research/2026-08-09-deep-research-vs-natives/instrument/"
        "decompose-moteur-contrat.py (engine/contract by caller) and "
        "DECOMPOSITION-MOTEUR-CONTRAT.md (by token nature)."
    ),
}


def is_retrieval(tool: str) -> bool:
    """Whether a tool name counts as retrieval under the pre-registered rule."""
    return tool in RETRIEVAL_EXACT or tool.startswith(RETRIEVAL_PREFIXES)


def classify_step(tools: list[str]) -> str:
    """Classify one step. A step touching both kinds counts as engine."""
    return "engine" if any(is_retrieval(t) for t in tools) else "contract"


def build_accounting(steps: list[dict[str, Any]], length: str | None = None) -> dict[str, Any]:
    """Compute the accounting vector from the steps the agent observed."""
    step_counts = {"total": 0, "engine": 0, "contract": 0, "mixed_counted_engine": 0}
    call_counts = {"total": 0, "retrieval": 0, "other": 0}
    by_tool: dict[str, int] = {}
    by_phase: dict[str, dict[str, int]] = {}

    for step in steps:
        tools = list(step.get("tools") or [])
        phase = str(step.get("phase", "unknown"))

        kind = classify_step(tools)
        step_counts["total"] += 1
        step_counts[kind] += 1
        if kind == "engine" and any(not is_retrieval(t) for t in tools):
            step_counts["mixed_counted_engine"] += 1

        phase_row = by_phase.setdefault(
            phase, {"steps": 0, "engine_steps": 0, "retrieval_calls": 0, "other_calls": 0}
        )
        phase_row["steps"] += 1
        if kind == "engine":
            phase_row["engine_steps"] += 1

        for tool in tools:
            by_tool[tool] = by_tool.get(tool, 0) + 1
            call_counts["total"] += 1
            if is_retrieval(tool):
                call_counts["retrieval"] += 1
                phase_row["retrieval_calls"] += 1
            else:
                call_counts["other"] += 1
                phase_row["other_calls"] += 1

    engine_step_share = (
        step_counts["engine"] / step_counts["total"] if step_counts["total"] else None
    )
    retrieval_call_share = (
        call_counts["retrieval"] / call_counts["total"] if call_counts["total"] else None
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "length": length,
        "rule": {
            "engine": "a step emitting >=1 retrieval tool call",
            "contract": "every other step",
            "mixed_step": "counted as engine, as in the pre-registered instrument",
            "retrieval_tools": {
                "prefixes": list(RETRIEVAL_PREFIXES),
                "exact": sorted(RETRIEVAL_EXACT),
            },
            "provenance": (
                "ported verbatim from instrument/decompose-moteur-contrat.py, "
                "pre-registered 2026-08-11 for the deep-research adoption eval"
            ),
        },
        "steps": step_counts,
        "calls": call_counts,
        "shares": {
            "engine_steps": engine_step_share,
            "retrieval_calls": retrieval_call_share,
            "basis": (
                "counts of steps and calls only. NOT a cost share: the 2026-08 eval "
                "measured the engine at ~14% of a run's cost while emitting a far "
                "larger fraction of its calls, so reading these as cost is the exact "
                "error the eval had to correct."
            ),
        },
        "by_tool": dict(sorted(by_tool.items())),
        "by_phase": dict(sorted(by_phase.items())),
        "not_measurable_in_run": NOT_MEASURABLE_IN_RUN,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--steps", required=True, help="JSON file of observed steps, or - for stdin")
    parser.add_argument("--out", default="research-run-accounting.json", help="output path, or - for stdout")
    parser.add_argument("--length", default=None, help="the run's --length, recorded as context")
    args = parser.parse_args(argv)

    raw = sys.stdin.read() if args.steps == "-" else Path(args.steps).read_text(encoding="utf-8")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"FAIL: --steps is not valid JSON: {exc}", file=sys.stderr)
        return 1

    steps = payload.get("steps") if isinstance(payload, dict) else payload
    if not isinstance(steps, list):
        print("FAIL: expected {'steps': [...]} or a bare list of steps", file=sys.stderr)
        return 1

    accounting = build_accounting(steps, length=args.length)
    rendered = json.dumps(accounting, indent=2, ensure_ascii=False) + "\n"

    if args.out == "-":
        sys.stdout.write(rendered)
    else:
        Path(args.out).write_text(rendered, encoding="utf-8")
        print(f"OK: wrote {args.out} ({accounting['steps']['total']} steps, "
              f"{accounting['calls']['retrieval']} retrieval calls)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
