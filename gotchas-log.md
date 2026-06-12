# Gotchas log

> Append-only operational memory for maintainers. One entry per gotcha: what triggered it, what the trap was, how it was resolved, and which eval fixture or CI check now guards it. Newest first.

## Entry template

```markdown
## YYYY-MM-DD — <short title>
- **Trigger:** <what surfaced the problem>
- **Gotcha:** <the trap, in one or two sentences>
- **Resolution:** <what was changed, with commit ref>
- **Guard:** <eval fixture / CI check added, or "none — accepted risk">
```

---

## 2026-06-12 — Example fixture drifted from the skill's own gates

- **Trigger:** adversarial review finding ADV-7 (verified by direct jq count).
- **Gotcha:** the canonical example shipped 12 cited sources against a 35-source floor and announced metrics (groundedness 0.97, corroboration 0.85 over 8 claims) that were arithmetically impossible as multiples of 1/8. Schema validation passed throughout — schemas check shape, not invariants.
- **Resolution:** example regenerated as `--length short` with exact-arithmetic metrics (commit `98eece2`).
- **Guard:** `tests/check-example-invariants.sh` recomputes the cascade, routing, and counts in CI; `scripts/verify_gates.py check-artifacts` runs on the example as a CI step.

## 2026-06-12 — Credibility rule diverged across four files

- **Trigger:** adversarial finding ADV-2 + independent harness XCUT (two isolated review contexts found the same drift — strongest convergence signal of the session).
- **Gotcha:** "single Tier 1 uncorroborated" appeared in both the credibility-2 and credibility-3 rules depending on the file; prose tables drift, precedence cascades do not.
- **Resolution:** methodology §4.1 carries the normative precedence cascade; other surfaces carry verbatim copies or a conformed rendering (commit `ab65f8d`).
- **Guard:** cascade conformance recomputed by both `tests/check-example-invariants.sh` and `scripts/verify_gates.py` — any artifact labeled against a drifted rule fails CI.

## 2026-06-12 — "Deterministic" gates were LLM self-reports

- **Trigger:** adversarial finding ADV-12 (punycode checks, medians, ratios demanded of an LLM with no tool, while invariant I4 banned executable code).
- **Gotcha:** a threshold is not a gate if nothing computes it. The skill's strongest selling point (deterministic grading) was structurally unverifiable.
- **Resolution:** I4 amended to I4a with user approval; `scripts/verify_gates.py` (stdlib-only, zero network) computes everything arithmetic; Phase 6 must quote its verdict (commit `9a63cba`).
- **Guard:** CI lints and runs the script on the example; SKILL.md forbids self-reported metrics as completion evidence.

---

## Maintenance cadences (perishable assets)

Review each asset on its cadence; log the re-validation (or the drift found) as a new entry above.

| Asset | Cadence | Created | Notes |
|---|---|---|---|
| Tier registry (`references/methodology.md §6`) | Quarterly | 2026-04-17 | Domains rot: acquisitions, paywall changes, editorial collapse. |
| `examples/eu-ai-act-2026/` fixture | Re-validate when gates change | 2026-04-17 | CI catches drift automatically since 0.2.0. |
| MBFC static dataset (planned, AI-125) | 4 weeks after creation, then 4-weekly | — | Per the playbook re-validation convention. |
| Perplexity benchmark test-set (planned, AI-124) | 4-weekly | — | The comparator itself drifts; a frozen test-set ages. |
| `experts.yaml` seed (user-scope, planned, AI-121) | Quarterly | — | Lives outside the repo (PII); renormalization rule documented in github-research.md when created. |
