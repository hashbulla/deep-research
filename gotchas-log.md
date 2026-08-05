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

## 2026-08-05 — W5 ablation: the FR trigger is not what carries the FR positives — and removing it correlated with release-blocker negative leaks

- **Trigger:** harness run #4 DIM-7-01 (WARNING, contested): `"deep research on X"` / `"recherche approfondie sur X"` graded as an FR/EN duplication slip; the Grounder surfaced contradicting evidence both ways; adjudication = measure before editing.
- **Gotcha:** both prior camps argued about the wrong cell. Ablation run (variant description without the FR form, full loading suite, opus/sonnet/haiku, 90 cells, cache-cold): **pos-03/09/15 held 9/9** — the semantic router resolves FR phrasing without the FR trigger, so "a francophone operator needs it" is unsupported *for the positives*. But the variant flipped **3 negative cells to leaks**: `neg-08`≡`neg-15` (the rubric's release-blocker boundary!) leaked on sonnet (`none`→`deep-research`) and haiku (NO_VERDICT→leak), `neg-12` leaked on haiku. At **n=1 per cell** this does not separate causation from router variance (the same boundary prompt was already unstable in baseline: haiku NO_VERDICT ×2) — but a variant that measures below the target's own negative bar cannot be read as "holds".
- **Resolution:** FR form **kept**, decision made on data per the adjudication ("casse → conservation consignée"). Run results: baseline 44/45 + 2 NOV; ablation 42/45 + 0 NOV (all three new failures are negative leaks). Evidence: `docs/harness/2026-08-05-run4/ablation_matrix.json`.
- **Guard:** none — accepted risk, with a named condition: re-open only with an n≥3-per-cell ablation (single-run routing measurements lie; cf. the open n≥3 harness debt). DIM-7-01 is closed as a **measured non-edit**, not as a validated slip.

---

## 2026-08-05 — A hardened gate leaks into every sibling fixture's unmutated substrate, and presence-only grep cannot see it

- **Trigger:** harness run #4 (PASS 7.61) measured with adversarial probes that Rule 7b enforced ≥1 GitHub-native query where its own doctrine mandates ≥3 topic combinations (a star-band-only manifest PASSed). Implementing the fix exposed a second, older defect: the eleven pre-existing mutation fixtures all carried the **pre-commit prose queries** in their `open-source` substrate, so Rule 7b had been firing a **parasite violation** on every one of them since `11a0439` — invisibly, because `check-solution-space.sh` greps for the expected needle only and never asserts the absence of others.
- **Gotcha:** two traps, one mechanism. (1) A gate that verifies a *shape* regresses to what its regex matches, not what its doctrine states — each mechanization step (doctrine → rule → regex → fixture) loses constraint, and only a probe against the gate itself measures the loss. (2) Mutation fixtures inherit the golden's substrate at creation time; when the gate hardens later, the substrate of every older fixture becomes retroactively non-conformant, and the "fires ITS OWN violation" claim silently voids. A presence-only assertion cannot distinguish "fires its violation" from "fires its violation *plus* a parasite".
- **Resolution (2026-08-05, post-run-#4 fix session, W1-W3 adjudicated fix-now):** Rule 7b gains a second tier — ≥3 **distinct** `topic:` combinations (distinct facet-sets across queries) when ≥1 native query exists; new `GITHUB_TOPIC_FACET` parses **both** runnable syntaxes (`topic:slug` and `--topic slug` — the CLI form was invisible to the original regex). Golden `valid.json` now carries 3 distinct combinations. The eleven fixtures' `open-source` substrate realigned to the corrected golden (an edit of *unmutated* substrate: it removes parasite failures, makes nothing pass that should fail — the eval-laundering rule protects prompts and expectations, not stale shared scaffolding). References aligned: `solution-space.md` query-vocabulary row + Instrument cell, `anti-patterns.md` B14.
- **Guard:** new fixture #13 `probe-starband-only.json` (GitHub-native but zero topic facets — must fire the tier-2 violation and nothing else), plus a **purity guard** loop in `check-solution-space.sh`: the Rule 7b violation strings must appear in no fixture other than the two that target them. This turns `e2e-15` mechanical check 2 (≥3 distinct topic combinations) into an *executed* CI assertion instead of an aspirational one. Residual, still open: Rule 7b validates query *shape*, not that GitHub was actually queried (`e2e-15` check 3, live-run only — see CHANGELOG Known limitations).

---

## 2026-08-05 — "OSS swept" was checkable only as a word, so it was true only as a word

- **Trigger:** Victor pointed at `Panniantong/Agent-Reach` (66,684 ★, tagged `claude-code`) after a hand-run web-interaction benchmark whose coverage manifest read `open-source: swept`. The repo was absent from the benchmark entirely.
- **Gotcha:** the six-category manifest could carry `swept` on **prose queries alone**. Rule 5 demanded ≥1 query and ≥1 finding, and prose satisfies both — nothing distinguished *swept via GitHub* from *swept via blogs about GitHub*. Prose retrieval surfaces comparison articles, which vendors write about vendors; it is structurally blind to a category whose vendors do not blog, and to a repo whose README is in a language nobody searched in. The miss was a **class**, not an instance: 8 repos, ~200k stars, including `jackwener/OpenCLI` (27,736 ★) — the leading implementation of the very class that same benchmark had named as *strongest* for its top use case. The sharpest form: **naming the right class buys nothing if it is then populated with the wrong instrument.** The query that was never run, `topic:claude-code+topic:web-scraper&sort=stars`, returns Agent-Reach first of eleven.
- **Second-order trap (why the golden fixture did not catch it):** `tests/fixtures/solution-space/valid.json` — the reference manifest, the thing a maintainer copies — carried the defect itself. Its `open-source` queries were `"instagram private API python client direct messages"` and `"github instagram dm library maintained 2026"`: both prose, the second merely *containing the word* github. A golden fixture encodes what "correct" looks like; when the bug is in the definition of correct, twelve adversarial mutation fixtures around it prove only that the mutations differ from the reference.
- **Resolution (2026-08-05):** new pipeline step `references/github-research.md` §2 — sweep ≥3 `topic:` combinations derived from the capability classes, sorted by stars, **before** star-band sharding, recorded verbatim in the manifest. New gate **Rule 7b** in `verify_gates.py`: `open-source` at `swept`/`empty` requires ≥1 GitHub-native query, matched by `GITHUB_NATIVE_QUERY` (`topic:` · `stars:` · `api.github.com/search` · `gh api`/`gh search`). The regex deliberately **rejects `site:github.com`** — prose retrieval wearing a GitHub costume. `valid.json` fixed; unit-tested the matcher against 8 cases including that negative.
- **Why `topic:` and not more keywords:** topics are author-assigned, language-independent, and drawn from a shared controlled vocabulary. They are the one retrieval axis immune to *my query words encode my hypothesis* (B14 one level deeper). Agent-Reach's README is Chinese-first and its self-description is "capability layer" — neither reachable from EN/FR problem-vocabulary — yet its topics are `claude-code`, `mcp`, `web-scraper`, in English, because topics are a taxonomy rather than prose.
- **Guard:** eval fixtures added — **yes**. Gate suite: new single-mutation violation fixture `oss-prose-only.json` (12 fixtures, up from 11), asserted in `tests/check-solution-space.sh` to fire *its own* violation. Behavioral: `evals/e2e.jsonl` +1 (`e2e-15`, five mechanical checks including the mutation test that Rule 7b fires on its own mutation), named in `evals/rubric.md` §3. Recall corpus: `evals/fixtures/sota-recall/` gains case `wi` (`wi-brief.md` + Agent-Reach and OpenCLI as ground truth — 6 items across 3 cases, up from 4 across 2), frozen 2026-08-05. **Known residual:** items 1 and 2 of the `evals/rubric.md` §"Adding fixtures" contract (positive loading fixture, territorial-neighbor negative) are **not** added — this change alters no routing surface and leaves `SKILL.md`'s description untouched, so a loading fixture would probe nothing new. The mutation pair `valid.json` (must pass) / `oss-prose-only.json` (must fail) plays the positive/negative role at the layer where this feature actually lives. Recorded here rather than silently skipped.

---

## 2026-08-04 — A hardening shipped its code and its hermetic tests, but not its paperwork or its behavioral fixtures

- **Trigger:** `/skill-harness` run #3 on the AI-355 worktree — **FAIL 6.84/10**, two dimensions under the 5.0 gate: D3 token-budget 4.0 and D5 append-mostly hygiene 4.0, with D4 eval coverage at 6.0 and D2 tax-test at 6.0.
- **Gotcha:** the two AI-355 commits added ~3,240 lines across 27 files — the solution-space sweep, the completeness critic, the fifth artifact, a new gate, twelve adversarial JSON fixtures, a CI check — and touched **zero** of `CHANGELOG.md`, `gotchas-log.md`, `evals/loading.jsonl`, `evals/e2e.jsonl`, `evals/progressive.jsonl`. Every failing dimension traced to that one omission, seen from four sides: no `[Unreleased]` entry for a description that changed **the same day** (D5's tier-4 clause, literally); no re-measurement of a body that grew +49% and crossed the 7,500-token hard cap by +33.8% (D3); none of the three additions the skill's **own** `evals/rubric.md` §"Adding fixtures" contract demands of any feature that changes the description (D4); and a Scope-Constraint sentence left asserting a human approval gate deleted in 0.3.0 (D2). The trap generalizes: **hermetic tests passing is not coverage of the behavior, and green CI says nothing about paperwork no CI step reads.** The deterministic layer here was genuinely strong — `tests/check-solution-space.sh` plus 12 single-mutation fixtures plus a JSON Schema — and it is exactly what made the gap invisible.
- **Second-order trap (why the fixtures read as green):** `run_evals.py` reads `entry["prompt"]`, which neither `progressive.jsonl` (keys on `when`) nor `e2e.jsonl` (keys on `invocation`) has. Both suites skip every row and report `[]` with `no_verdict_counts = 0` — **structurally identical to a perfect score**. Four fixtures asserting the superseded four-artifact contract sat green for that reason alone. *NOT RUN is not PASS*; do not read an empty suite array as a pass.
- **Resolution (this fix session, 2026-08-04):** `CHANGELOG.md` gains an `[Unreleased]` block covering the feature, the description change, the D3 remediation with before/after token figures and a context-budget justification, and an explicit **superseding note** for the now-false four-artifact line — appended, never edited, per this repo's append-only discipline. `SKILL.md` load tier taken from **10,036 → 7,199 tok** (under the 7,500 hard cap) by moving provenance, edge-case reasoning and flag semantics into `references/provenance.md`, `references/edge-cases.md` and `references/flags.md`, compressing the Phase-1 conditional-source block to a gate index, and making the 4,434-token `references/solution-space.md` a **conditional** read (inline minimal contract at Phase 0 step 5 covers a `not-applicable` run). The stale approval-gate sentence was rewritten to anti-pattern A1's current form — **the gate itself was NOT restored** (see the 2026-06-16 entry, which warns against exactly that).
- **Waiver — superseded fixtures, recorded per `evals/rubric.md:45`:** `neg-08`, `prog-09`, `e2e-01` and `e2e-08` assert the four-artifact contract and would fail against the current skill. They are **retained unedited** — editing them would be eval laundering, and each is an accurate record of the contract at its date. Successors carrying the corrected assertion and an explicit `SUPERSEDES <id> (2026-08-04)` marker in the row's own rationale field: `neg-15`, `prog-13`, `e2e-13`, `e2e-14`. The convention is now codified in `evals/rubric.md` §"Superseding a fixture whose contract changed".
- **Guard:** eval fixtures added — **yes**. `loading.jsonl` +4 (`pos-14` EN solution-space rider, `pos-15` FR sibling, `neg-14` solution-space-adjacent-but-quick over-fire guard, `neg-15`); `e2e.jsonl` +4 (`e2e-11` five artifacts + `check-solution-space` PASS + own-stack-before-web ordering, `e2e-12` obligations greppable in the first 10 lines of the report, `e2e-13`, `e2e-14`); `progressive.jsonl` +3 (`prog-11` NA geometry reads no solution-space reference, `prog-12` applicable geometry does and orders the stack grep first, `prog-13`). `evals/rubric.md` pass bars realigned to the fixture counts. **Known residual:** the runner still executes only the `loading` suite, so the `e2e` and `progressive` additions are mechanically checkable but not yet mechanically executed — recorded in `CHANGELOG.md` §"Known limitations", not silently assumed green.

## 2026-08-04 — An eval decoy fixture contained the very terms it was built to not match

- **Trigger:** the deterministic-layer agent building `tests/check-solution-space.sh` precision assertions for `scripts/stack_inventory.py`.
- **Gotcha:** the own-stack sweep's **decoy** corpus file — a document that must surface **zero** hits, proving the grep matcher does not match everything — carried a disclaimer whose prose literally spelled out the sweep terms it was supposed to be invisible to. The decoy therefore matched, and **no substring matcher could ever have excluded it**: the bug was in the fixture, not the instrument. A precision test whose negative sample contains the positive signal measures nothing, and it fails in the direction that looks like a real defect — you spend the debugging session hardening a matcher that was already correct.
- **Resolution:** the disclaimer was reworded at the source on 2026-08-04, leaving the decoy's ground truth intact (it is still a plausible near-miss document, just one that no longer states the terms). The reasoning is commented inline at `tests/check-solution-space.sh` so a future maintainer does not "restore" the original wording.
- **Guard:** eval fixture added — **yes**, as two **absence assertions** in `tests/check-solution-space.sh`: *"decoy contributes zero hits"* (`.hits[]` filtered to the decoy file is empty) and *"decoy absent from hit_files"*. They pin precision from the negative side; the paired control-negative case (`--terms zzz-quasar-nonexistent` yields zero `hit_files`) pins it from the other. Both run in CI via `.github/workflows/validate.yml`.

## 2026-06-23 — OSINT stealth cap default + GDPR persistence default + scrapling MCP optional

- **Trigger:** AI-183 wiring — documenting the three non-obvious defaults that callers and future maintainers are most likely to misconfigure.
- **Gotcha 1 (stealth cap).** The `--max-stealth` default is **12** dispatches per run, not unlimited. Raising it without a deliberate reason burns scrapling budget and extends runtime. The cap is enforced by `verify_gates.py check-artifacts --max-stealth N`; the default is 12 when the flag is omitted. Record the actual count in the Methodology note.
- **Gotcha 2 (GDPR persistence).** The default GDPR posture is **data-minimized**: only the cited-span snapshot is persisted into evidence anchors; full stealth-capture output is local-only and NEVER committed. The lawful-basis (legitimate-interest) determination is the owner's to record, not the skill's to infer.
- **Gotcha 3 (scrapling optional).** The scrapling MCP is optional. A Phase-0 availability probe decides at plan-composition time; if the MCP is absent, rung 3 is disabled for the entire run and `research-plan.md` records "scrapling MCP absent — OSINT rung 3 disabled". This is graceful degradation, not an error. Do not attempt to call scrapling tools or raise a hard failure when the MCP is missing.
- **Resolution:** documented in `references/osint-retrieval.md`, propagated to SKILL.md Phase 1 step 9, `CHANGELOG.md` AI-183 entry, and this log entry. Commit: feat(skill): wire OSINT/SOCMINT ladder + propagate docs (AI-183).
- **Guard:** `tests/check-osint-gates.sh` T2 asserts the cap violation fires at the declared threshold; T3 asserts `retrieval_status` is required on scrapling records; T4/T5 assert the B13 anti-amplification gate fires and clears.

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
