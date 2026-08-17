#!/usr/bin/env python3
"""Grade a run_evals loading matrix against deep-research evals/rubric.md:17.

Implements SCORING-POLICY.md (pre-registered 2026-08-17, before the data existed).
The runner emits raw verdicts only; this script does the pass/fail arithmetic.

Usage: grade.py <matrix.json> <fixtures.jsonl>
"""
import json
import sys
from pathlib import Path

TARGET = "deep-research"
NO_VERDICT = "NO_VERDICT"
BLOCKERS = ("neg-07", "neg-16")  # succession graded on neg-16 only


def main() -> int:
    matrix = json.loads(Path(sys.argv[1]).read_text())
    fixtures = {
        r["id"]: r
        for r in (json.loads(line) for line in Path(sys.argv[2]).read_text().splitlines() if line.strip())
    }
    rows = matrix["suites"]["loading"]
    models = list(rows[0]["verdicts"].keys())

    print(f"fixtures graded: {len(rows)} | models: {', '.join(models)}\n")

    overall_ok = True
    for model in models:
        pos_pass = pos_fail = pos_nv = 0
        neg_pass = neg_leak = neg_nv = 0
        leaks, novs = [], []

        for row in rows:
            fid = row.get("id")
            verdict = row["verdicts"].get(model)
            expects_fire = row["expected_fire"]

            if expects_fire:
                if verdict == NO_VERDICT:
                    pos_nv += 1
                    novs.append(fid)
                elif verdict == TARGET:
                    pos_pass += 1
                else:
                    pos_fail += 1
                    leaks.append(f"{fid}:SILENT->{verdict}")
            else:
                if verdict == NO_VERDICT:
                    neg_nv += 1
                    novs.append(fid)
                elif verdict == TARGET:
                    neg_leak += 1
                    leaks.append(f"{fid}:LEAK")
                else:
                    neg_pass += 1

        # Rule 4: NO_VERDICT shrinks the measurable denominator, never the numerator.
        pos_total, neg_total = pos_pass + pos_fail + pos_nv, neg_pass + neg_leak + neg_nv
        pos_bar_ok = pos_pass >= 14
        neg_bar_ok = neg_pass >= 15
        measurable = (pos_total - pos_nv) >= 14 and (neg_total - neg_nv) >= 15

        # Release blockers need a USABLE, clean verdict.
        blocker_state = {}
        for bid in BLOCKERS:
            brow = next((r for r in rows if r.get("id") == bid), None)
            v = brow["verdicts"].get(model) if brow else "ABSENT"
            if v == NO_VERDICT:
                blocker_state[bid] = "UNUSABLE(NO_VERDICT)"
            elif v == TARGET:
                blocker_state[bid] = "BLOCKER-LEAK"
            else:
                blocker_state[bid] = f"clean({v})"
        blockers_ok = all(s.startswith("clean") for s in blocker_state.values())

        if not measurable:
            status = "UNMEASURABLE (rule 4 — not a failure, still no push)"
        elif pos_bar_ok and neg_bar_ok and blockers_ok:
            status = "PASS"
        else:
            status = "FAIL"
        overall_ok &= status == "PASS"

        print(f"### {model}")
        print(f"  positives : {pos_pass}/15 pass, {pos_fail} silent, {pos_nv} NO_VERDICT   (bar >=14: {'OK' if pos_bar_ok else 'NO'})")
        print(f"  negatives : {neg_pass}/16 pass, {neg_leak} LEAK,   {neg_nv} NO_VERDICT   (bar >=15: {'OK' if neg_bar_ok else 'NO'})")
        print(f"  blockers  : " + ", ".join(f"{k}={v}" for k, v in blocker_state.items()))
        if leaks:
            print(f"  anomalies : {', '.join(leaks)}")
        if novs:
            print(f"  no_verdict: {', '.join(novs)}")
        print(f"  => {status}\n")

    print("no_verdict_counts (runner tally):", json.dumps(matrix.get("no_verdict_counts", {})))

    # Opus must replay run #6 byte-identically, else the baseline is void.
    print("\n### corpus-drift check (opus column must be a cache replay)")
    if "opus" in models:
        wrong = [r["id"] for r in rows
                 if r["verdicts"]["opus"] == NO_VERDICT]
        print(f"  opus NO_VERDICT rows: {len(wrong)} {wrong if wrong else ''}")
        print("  (run #6 recorded 0 NO_VERDICT, 15/15 + 16/16 — any change here voids the baseline)")

    print(f"\nOVERALL: {'PASS on every model' if overall_ok else 'NOT clean — see per-model status'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
