# Edge cases — full handling

> Moved out of `SKILL.md` on 2026-08-04 (harness run #3, D3 load-tier remediation). `SKILL.md` §Edge Cases keeps the trigger→verdict index — every trigger and every verdict is named there, so the agent knows a case exists without loading this file. **Read this file the moment one of them fires**; it carries the reasoning and the second-order rules behind each verdict.
>
> Nothing here overrides [methodology.md](methodology.md) (normative for methodology), [quality-gate.md](quality-gate.md) (normative for thresholds), or [anti-patterns.md](anti-patterns.md) (normative for forbidden behavior).

## Report file missing from CWD

`references/methodology.md` is the skill-local authoritative copy; proceed using it. Do NOT downgrade methodology discipline — a missing CWD report changes the provenance path, not the rigor. See `SKILL.md` §Provenance for the hash rule that governs a report that *is* present.

## Input question is missing or ambiguous

Handled by the Phase 0 step-3 pre-flight refinement: the ambiguity-signal checklist ([methodology.md](methodology.md) §9) fires one `AskUserQuestion` round to resolve it. If the user confirms ambiguity is intentional (open-ended exploration), classify as `mixed` and decompose across all four sub-question categories.

## Language mismatch between flag and question

The flag wins. Translate the question internally but preserve original-language key terms for search queries — proper nouns and domain-specific terminology retrieve better in their source language.

## User-provided `--domains` conflicts with tier profile

Union them; never drop user-specified domains. Any user-added domain below Tier 2 is a step-3 safety trigger: confirm its inclusion via the pre-flight `AskUserQuestion` round and record the decision in `research-plan.md`.

## Tavily returns `score < 0.7` across an entire sub-question

Do not proceed with low-quality sources. Either broaden the allowlist (add adjacent Tier 1/2 domains), rephrase the sub-question, or mark the sub-question as "Insufficient sources — moved to Needs Verification" in the final report.

## Tavily research endpoint hits rate limit (20 req/min)

Back off with exponential delay (30 s, 60 s, 120 s) up to 3 retries. If still failing, degrade to `tavily_search` + manual multi-step decomposition for the affected sub-questions.

## All Tavily tools unreachable

Halt, report the outage to the user, and ask whether to (a) wait and retry, or (b) proceed with `WebSearch` fallback (with an explicit quality-degradation warning appended to every affected source in `research-sources.json`).

## Paywalled sources (report §11)

Prefer open-access equivalents (PubMed Central, arXiv preprint of a journal paper). If only the abstract is retrievable, flag the claim as `admiralty_credibility: 3` unless a second independent source corroborates.

## Two phases produce contradicting claims from equally authoritative sources

Do not silently pick one. List both in a "Contradictions & open debates" subsection with each side's evidence. This is explicit report guidance (§1, §5.3 CRAG handling).

## User asks for a re-run with different flags

Re-run from Phase 0. Do not reuse prior `research-sources.json` without re-grading — scores and freshness may have shifted.

## `stack-paths.json` config absent

`scripts/stack_inventory.py` finds no `~/.claude/deep-research/stack-paths.json` (template: [../stack-paths.json.example](../stack-paths.json.example)). Record `own-stack` as `degraded` with that reason and continue the other five categories — a missing own-stack inventory is visible, never a silent `empty`.

## Artifact tool unavailable (headless surface)

`allowed-tools` pre-approves the Artifact tool, it does not guarantee its presence. If the tool is absent, record the degradation in the Methodology note and finish the run on the five file artifacts. Never fail, retry, or substitute another publishing path.

## Exhaustive run trending under 100 sources by end of Phase 3

Expand the domain allowlist to the full Tier 1+2 union and add 2–4 contextual / recency sub-questions before Phase 4. **One expansion round maximum** — if the run still trends under 100 after it, proceed to Phase 4 and document the shortfall in the Methodology note. The 100-source target is a quality calibration, not a hard contract (report §1 "dozens of searches against hundreds of sources").
