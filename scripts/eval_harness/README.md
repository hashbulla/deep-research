# Eval harness — five verification layers (AI-124)

> Permanent verification, not a one-off audit. Layer 1 is deterministic and runs on every run and in CI unconditionally. Layers 2–5 are LLM-judged: at runtime they run as decorrelated Claude Code subagents (zero API keys — decision D-4); in CI they run only when the maintainer repo secret `ANTHROPIC_API_KEY` exists, and skip gracefully otherwise. Consumers never need a key.

## The five layers

| # | Layer | Mechanism | Runtime (per run) | CI |
|---|---|---|---|---|
| 1 | Deterministic pre-flight | `scripts/verify_gates.py check-artifacts` — counts, ratios, cascade, anchors (`--rigor critical`), refuse-if-no-source | Always (Phase 6, verdict quoted) | Always (`validate.yml`) |
| 2 | Entailment | Judge prompt `judge_prompts/entailment.md` — does the cited span ENTAIL the claim (not merely mention the topic)? | Decorrelated subagent (different Claude model, claim+span only). Scope per rigor profile (`quality-gate.md`) | `run_ci_judges.sh` on the example fixture, secret-gated |
| 3 | Adversarial critique (cross-model) | Judge prompt `judge_prompts/adversarial.md` — actively try to BREAK each claim. Circularity broken per D-4: a **different Claude model + decorrelated context** (the option the ticket allows); external Gemini/GPT judges were dropped (no keys in a zero-key skill) | `critical` rigor only | secret-gated |
| 4 | Completeness / citation-recall | Judge prompt `judge_prompts/completeness.md` — every planned sub-question answered? every material source actually cited? | `critical` rigor; `standard` relies on the deterministic coverage gate | secret-gated |
| 5 | Sycophancy probe | Versioned false-premise probes `../../evals/sycophancy-probes.jsonl` — the system must CORRECT a false premise, never research it | Phase 0 presupposition probe (`critical`) | Probe set replayed against the skill, secret-gated |

**Thresholds (build fails under any):** layer 1 verdict PASS; layer 2 entailment pass-rate ≥ 0.95 on judged claims (the RAGAS-faithfulness analog, target ~1.0); layer 4 citation-recall ≥ 0.90; layer 5 zero reinforced false premises.

## CI wiring

`bash scripts/eval_harness/run_ci_judges.sh` — exits 0 with an explicit `SKIP` line when `ANTHROPIC_API_KEY` is absent (deterministic layers have already gated the build); with the secret, it samples claims from the example fixture, runs the layer-2 judge via the Messages API, and fails the build under threshold. The judge model is pinned in the script and is intentionally different from the documented synthesis default.

## Benchmark vs Perplexity Deep Research (frozen test-set)

`../../evals/benchmark-testset.jsonl` — frozen questions with date pins (4-weekly re-validation cadence, gotchas-log: the comparator drifts). Protocol: run each question through `/deep-research --length standard` and through Perplexity Deep Research on the same day; score both with the layer-2/3/4 judges on FACT-style citation-accuracy and RACE-style report quality (comprehensiveness, insight, instruction-following, readability); record scores + dataset version in Linear AI-124. The skill must match or beat Perplexity on citation-accuracy — that is the calibration target the README claims.

Deferred items consolidated here from earlier slices: the AI-121 golden-topic GitHub ranking benchmark and the AI-122 open-graph vs Exa/Valyu recall benchmark run on this same harness and record into their tickets.
