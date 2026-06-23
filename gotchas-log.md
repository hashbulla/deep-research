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

## 2026-06-23 — newsletter `--since YYYY-MM` rejected → silent source loss

- **Trigger:** live AI-182 run — the orchestrator seeded the newsletter source with `--since 2026-04` (`YYYY-MM`) and piped `2>/dev/null`; all Phase-1 newsletter calls returned empty and were misread as "the corpus has nothing on this topic" (it had 322 LLM-judge + 34 observability items).
- **Gotcha:** `newsletter_search.py` `parse_date` accepted only `%Y-%m-%d`, so a `YYYY` / `YYYY-MM` value exits non-zero — but the skill's own `--since` flag is documented as `YYYY or YYYY-MM-DD`. The script fails loud *correctly*; the trap is the contract mismatch plus a caller that suppresses stderr, turning a hard fail into a silent degradation the Methodology note never records.
- **Resolution:** `parse_date` hardened to accept `YYYY`, `YYYY-MM`, and `YYYY-MM-DD` (partials coerce to the first day), matching the documented `--since` contract; error string and `--help`/usage updated. Commit `a3a7203`.
- **Guard:** new positive case in `tests/check-newsletter-search.sh` ("--since accepts YYYY and YYYY-MM partials") asserts `--since 2026-06` and `--since 2026` are accepted and still filter; the existing `--since not-a-date` fail-loud case is unchanged.

## 2026-06-16 — The Phase-0 human approval gate was removed ON PURPOSE

- **Trigger:** user design decision (spec `docs/superpowers/specs/2026-06-15-remove-human-gate-design.md`), to make the skill usable by fully autonomous agents.
- **Gotcha:** the mandatory "HUMAN GATE — STOP" between Phase 0 and Phase 1 was, until 0.3.0, a documented **non-negotiable** (old anti-pattern A1, old README "The Human Gate" section). A future audit that sees no approval halt may "restore" it as a regression — **do not.** Its removal was deliberate and approved.
- **Resolution:** the halt is replaced by a **conditional pre-flight refinement** at Phase 0 step 3 — a single `AskUserQuestion` round fires only when the ambiguity-signal checklist (`references/methodology.md` §9, authoritative) or a safety trigger (sub-Tier-2 `--domains`, critical-rigor false premise) trips. A1 was rewritten from "no tool calls before approval" to "no retrieval before the plan is written and any triggered refinement has resolved" — planning still precedes retrieval; only the *human halt* is gone. The four-artifact contract is unchanged (`research-plan.md` is still artifact #1).
- **Guard:** `e2e-01` (well-formed query → zero AskUserQuestion, autonomous) + `e2e-10` (ambiguous query → exactly one AskUserQuestion before any Tavily call); rubric §3 names both as the first non-negotiable. Provenance untouched (the report never mentioned the gate; SHA-256 unchanged).

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
| MBFC static dataset (`~/.claude/deep-research/mbfc-overlay.json`, user-scope) | 4-weekly | 2026-06-12 (format + rules; dataset seeded at first use) | User-scope, not in the repo: bulk MBFC redistribution in a public repo is a licensing risk. Rules in methodology §6 "Credibility overlay". |
| Perplexity benchmark test-set (`evals/benchmark-testset.jsonl`) | 4-weekly | 2026-06-12 (v1, 5 questions, date-pinned) | The comparator itself drifts; a frozen test-set ages. Protocol in `scripts/eval_harness/README.md`. |
| `experts.yaml` seed (user-scope, planned, AI-121) | Quarterly | — | Lives outside the repo (PII); renormalization rule documented in github-research.md when created. |
