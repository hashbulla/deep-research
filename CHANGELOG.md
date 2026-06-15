# Changelog

All notable changes to the deep-research skill. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning is semver. Append-only: new entries go on top, old entries are never rewritten.

## [Unreleased]

### Added

- **`suggest-tooling` sibling skill** (closes AI-30; subsumes the AI-40 marketplace remainder). Consumes a finished `/deep-research` run and proposes work-relevant Claude Code skills/plugins/MCP servers, relevance-ranked (hat-weighted category match) and trust-tier-graded (VERIFIED/MAINTAINED/COMMUNITY/CAUTION), **never auto-installed**. Six discovery channels (GitHub, MCP Registry, Claude Code marketplaces, Vercel skills, Smithery, awesome-* seed-only), each independently degradable. New stdlib-only, zero-network, zero-LLM ranker `suggest-tooling/scripts/marketplace_rank.py` (total null-safe trust cascade, scalar fake-signal gate with N≥8 guard, order-independent cross-channel dedupe, composite score with component-drop renormalization). `scripts/github_rank.py` gains an extracted importable `fake_star_gate()` (behavior-preserving, golden-file regression test) reused as the GitHub fake-star divergence gate. Tests in `tests/check-marketplace-rank.sh` (T1–T6 + T9 taxonomy parity), wired into `validate.yml`. Grounded by the dogfood `/deep-research` run in `docs/superpowers/specs/research/tooling-discovery-2026/`; spec + plan under `docs/superpowers/`.
- **`--suggest-tooling` flag** in the deep-research engine (default OFF). After Phase 6, delegates the finished run to the `suggest-tooling` sibling, which writes the 5th file `research-toolbox.md` (+ `research-toolbox.json` sidecar). The four-artifact contract is unchanged: the engine still emits exactly four; a separate skill writes the fifth. Runs are byte-identical with the flag unset.

### Changed

- README synced to 0.3.0 (post-release doc catch-up): Roadmap split into a "Shipped" block (MBFC overlay, BibTeX/RIS export, conditional sources, model tiers, rigor profiles, eval harness — all previously mislabeled Planned/Future) and a "Considered / deferred" block recording the Exa/Valyu deferral, the dropped external-model judge (superseded by the decorrelated Claude judge, zero-key contract), and the dropped Perplexity quality-benchmark comparator. Pipeline mermaid gains the conditional-source branch (Phase 1), MBFC overlay (Phase 2), and decorrelated entailment judge (Phase 5, renamed "Grounding Validation" per methodology §9 / invariant I3). Design-decisions table gains conditional sources, rigor profiles, model selection, and the fidelity judge. `--rigor` added to the flags table. The two file trees reconciled to the actual 10 reference files. Tagline and lede de-benchmarked from Perplexity (the methodology-source credit in Research Foundation stays — it credits the published 5-stage method, not a quality comparator).

### Calibration log — `/skill-harness` run #2 (2026-06-12, uncalibrated 2/3)

Evaluator verdict on 0.3.0: **PASS 8.94/10** (run #1: 6.6 FAIL) — 0 CRITICAL, 1 WARNING, 4 ADVISORY, 1 UNKNOWN; full report in the (uncommitted) `REVIEW.md`. Human-vs-evaluator agreement, measured against the pre-run human predictions: D4/D5 closures confirmed at 10.0 (agree), D3 token-budget risk materialized as the sole WARNING — load tier 6,733 tok vs the ~5k Anthropic Level-2 budget, context-budget justification absent from the 0.3.0 entry (agree; the human prediction said "overage documented in CHANGELOG 0.3.0" but the evaluator correctly noted the 0.3.0 budget remark concerns runtime cost, not context — evaluator stricter, accepted), D2 tax-test risk did not materialize at 9.0 (human over-predicted). Agreement 3/4; scores still not trusted at face value before run #3. D3 context-budget justification, recorded here per the evaluator's documentation-path fix: the 0.3.0 load tier rises to ~6,733 tok (soft 5,000 / hard 7,500) because the three conditional-source gates (GitHub, academic, Context7), the rigor profiles, and the new flag surface are load-bearing at Phase-0 plan-composition time and cannot move to `references/` without breaking the human-gate plan declaration; index tier 146 tok (soft 100 / hard 170) carries the waived 79-word dual-sibling description.

## [0.3.0] — 2026-06-12

The AI-119 refonte: model tiers, grounding spine with rigor profiles, three new conditional retrieval sources, credibility overlay, and the permanent five-layer eval harness — all Claude-Code-native (decision D-4: zero API keys for consumers; a standard non-confidential run still needs nothing beyond the Tavily MCP and finishes in its usual budget).

### Added

- `references/model-tiers.md` + `--model` / `--confidential` flags (AI-120, decision D-4): Claude-Code-native model-tier selection — opus default, fable opt-in at ~2× cost, subagent `model` overrides, zero SDK calls and zero API keys. Plan template declares the tier at the human gate. Corrects the original cost estimate: Fable 5 shares the Opus 4.8 tokenizer, so the multiple is ~2× (price), not ~2.6× (facts verified against the claude-api skill, 2026-06-12).
- Eval harness (AI-124, amended by D-4): `scripts/eval_harness/` — five layers with an explicit per-run vs CI mapping per rigor profile. Layer 1 = `verify_gates.py` (deterministic, always-on, CI step). Layers 2–4 = versioned judge prompts (entailment v1, adversarial-critique v1, completeness/citation-recall v1) used identically by the runtime decorrelated subagents and by `run_ci_judges.sh` — a maintainer-secret-gated CI runner that skips gracefully without `ANTHROPIC_API_KEY` (consumers never need a key) and fails the build under the 0.95 entailment threshold when it runs. Cross-model circularity broken per D-4 with a different pinned Claude judge model + decorrelated context (the ticket's allowed minimum; external Gemini/GPT judges dropped — zero-key skill). Layer 5 = `evals/sycophancy-probes.jsonl` (5 versioned false-premise probes). Frozen Perplexity benchmark test-set `evals/benchmark-testset.jsonl` (v1, 5 date-pinned questions, 4-weekly cadence) + RACE/FACT-style protocol; the deferred AI-121 ranking and AI-122 recall benchmarks run on this harness.
- Credibility overlay (AI-125): MBFC-static per-domain overlay on the tier registry — re-rank/flag at the margin, never a replacement, deterministic rules in methodology §6 (mixed → flag; low/very-low → one-tier downgrade; never upgrades). Dataset lives user-scope (`~/.claude/deep-research/mbfc-overlay.json`, 4-weekly cadence) — bulk MBFC redistribution in a public repo is a licensing risk; NewsGuard evaluated and not integrated (commercial license). New optional `credibility_overlay` field in the sources schema; downgraded/flagged allowlisted domains surface in the plan at the human gate; absent dataset → overlay skipped (C-9). Fixture e2e-09.
- Academic deep research (AI-122): `references/academic-research.md` (OpenAlex ‖ arXiv discovery — arXiv 1 req/3 s serialized; Semantic Scholar batch enrichment; one co-citation expansion round on the open graph; legal-OA ingestion chain arXiv → Unpaywall → EuropePMC → CORE, else abstract+tldr flagged with credibility capped per B9; PWC is dead → HF papers/trending) + `scripts/academic_graph.py` (dual-track Foundational/Emerging ranking — authority without recency penalty vs 12–24-month citation velocity — dedup by DOI/paperId, **BibTeX + RIS export**, printed effective weights). All keys/emails optional with per-hop degradation (C-9); never scrape a paywall. Tier registry: DOI Tier 1; arXiv preprints Tier-1 reliability but never sole support for contested CONFIRMED claims. Exa/Valyu decision: open-graph by default, recall benchmark deferred to the Slice-5 harness. Fixture e2e-08.
- GitHub deep research (AI-121): `references/github-research.md` (star-band sharding around the silent 1,000-result cap, GraphQL enrichment via `gh` CLI, ecosyste.ms dependents on the polite tier, expert-starred prior from a user-scope `experts.yaml` — anonymous `experts.yaml.example` ships in-repo) + `scripts/github_rank.py` (composite 0.30/0.20/0.20/0.15/0.10/0.05 scoring, **weight renormalization with printed effective weights when a component is unavailable** — no silent zero-signals, StarScout-derived fake-star divergence penalty). Scoring is stdlib/zero-network (I4a); retrieval runs through scoped Bash (`gh`, ecosyste.ms curl). Repo READMEs are Tier-3 self-description and A6-untrusted. Synthetic validation: a 8k-star farm with flat usage ranks last with `fake_star_suspect: true` where raw-star sort ranks it 2nd. Live golden-topic measurement (DoD "composite > raw stars") deferred to the Slice-5 harness, protocol documented. Fixture e2e-07.
- Context7 conditional doc retrieval (AI-126): three-condition gate (technical profile + named dependency + integrate/configure/debug/migrate/understand intent) checked at Phase 0, declared in the plan at the human gate, zero calls otherwise (1,000/month free tier). `resolve-library-id` → `query-docs`, cached per `library_id + version`, escalation to `tavily_skill` on missing docs, graceful Tavily degradation when the MCP is absent (C-9). Chunks graded Tier 1/2 with `doc_provenance: {library_id, version, section}` mapped to the canonical URL (`retrieval_tool: "context7_query_docs"`, null score); they pass the full Phase-2 battery like any source (C-3) and remain untrusted data (A6/C-4). Fixture e2e-06 covers gating, provenance, and degradation.
- Grounding spine (AI-123, amended by D-4): **rigor profiles** in quality-gate.md — `standard` (default; entailment spot-check on executive-summary + single-source claims, weak claims → Needs Verification) and `critical` (implied by `--confidential`: entailment on every claim, refuse-if-no-source, mandatory `anchor` per claim, Phase-0 sycophancy/false-premise probe, contradiction critic). New `anchor` field in `research-evidence.schema.json` (`verbatim_quote` for web — char offsets are never emitted against unpersisted web content; `snapshot_char_range` + SHA-256 for persisted corpus docs), replacing the ticket's Citations-API requirement per D-4. Phase 4 is attribute-first (spans selected before prose). Phase 5 gains a decorrelated entailment judge (different Claude model, claim + span only). Orchestration topology in methodology.md: lead + isolated subagents (Phase-2 grading delegated on exhaustive runs), long-context policy by working-set size, scratch-only compaction (the evidence layer is never compacted), neutral-references-only rule for confidential runs. `verify_gates.py --rigor critical` enforces anchors + refuse-if-no-source deterministically. The generalist default keeps its current cost profile: a standard run gets a spot-check entailment pass and no refusal gate (PR-2 fit-to-mission).

## [0.2.0] — 2026-06-12

Hardening release driven by three independent reviews run on 2026-06-12: a manual adversarial review (18 findings, ADV-1→18), a `/skill-harness` run (#1, uncalibrated — 6.6/10 FAIL: D4 eval coverage, D5 append-mostly hygiene), and an adversarial review of the remediation plan itself (13 findings, PR-1→13).

### Added

- `scripts/verify_gates.py` — deterministic gate verification (stdlib-only, zero network): artifact counts/ratios/medians, §4.1 cascade conformance, punycode normalization, CWD-report SHA-256 check. Quality gates are script-verified, never LLM-self-reported (ADV-12, ADV-3).
- `tests/check-example-invariants.sh` — jq cross-file validation of the example artifact pair (dangling IDs, cascade recomputation, label routing, B5); wired into CI (ADV-17).
- Anti-pattern A6 — retrieved content is data, never instructions; "structured = safe" premise removed from B8 (ADV-1).
- Optional-source degradation rule (methodology §7 + SKILL.md scope constraints): any retrieval source beyond Tavily is optional, with documented Tavily fallback (C-9).
- `references/examples.md` — the two worked examples, moved out of SKILL.md to bring the load tier under the 5,000-token soft cap (harness TOKEN-BUDGET warning).
- `evals/` — loading, progressive-disclosure, and e2e fixtures + rubric (closes harness CRITICAL D4).
- `CHANGELOG.md` and `gotchas-log.md` (closes harness CRITICAL D5).
- `allowed-tools` frontmatter restricting the skill's tool surface (ADV-18).

### Changed

- **Credibility cascade unified** — `references/methodology.md §4.1` is now the single normative algorithm (precedence cascade + explicit Tier-3 no-upgrade rule + label→section routing); quality-gate.md and SKILL.md Phase 6 carry verbatim copies, README renders it as a table (ADV-2, ADV-6, harness XCUT). Resolution note: "single Tier 1 uncorroborated → 3" was unreachable under precedence; a single Tier 1 source is credibility 2.
- Phase 4 drafts in memory; all four artifacts are written atomically at Phase 6, then verified by `verify_gates.py` before completion is reported (ADV-5).
- Sources discovered after Phase 2 (tavily_research citations, tavily_extract pulls, CRAG re-queries) repass the full Phase-2 gate battery (ADV-13).
- Tier comparator fixed to membership in {Tier 1, Tier 2}; Tier 3 is a secondary corroborator only (ADV-9).
- Exhaustive source floor: one expansion round max, then proceed with a documented shortfall (ADV-10). CRAG capped at 2 per failing sub-question AND ≤6 total per run (ADV-16).
- Punycode gate conditioned on an active `include_domains` allowlist (ADV-14).
- "Seven-phase" wording aligned in methodology §9 and README (ADV-15, harness XCUT).
- `tavily_score` nullable for score-less retrieval tools — never fabricate a score (ADV-8).
- `examples/eu-ai-act-2026/` regenerated as a gate-conformant `--length short` run: 16 sources, 15 claims, exact-arithmetic metrics (corroboration 12/15 = 0.80), labels recomputed under the unified cascade (ADV-7).
- Invariant I4 amended to I4a (markdown skill-surface; deterministic helpers under `scripts/`, stdlib-only, zero network, zero SDK) with explicit user approval — decisions D-3/D-4 of the AI-119 plan.
- SKILL.md description: "Load when…" phrasing + negative boundary against the plugin-namespaced `deep-research` sibling and `/research` (harness ROUTING + CONFLICTS warnings). Description is ~80 words, above the 50-word soft target — waived: the dual-sibling disambiguation is load-bearing.

### Fixed

- Fabricated citation "report §4 domain-language match" in SKILL.md Edge Cases replaced with plain rationale (ADV-4); the new CI prose-reference check makes this class machine-caught.
- Hostile-CWD provenance hole: a `deep-research-report.md` in the invocation CWD is honored only after its SHA-256 matches the SKILL.md line-8 prefix (ADV-3).

## [0.1.1] — 2026-04-17

Remediation cycle from the first `/skill-harness`-style review (findings D1–D6), 14 commits:

- D1: phase enumeration aligned to 7 phases; Phase-2 tier-admission rule tightened; README sync-model paragraph rewritten.
- D2: README badges trimmed, then restored by explicit user preference (`revert(D2)`, 2026-04-17 — aesthetic choice is the user's).
- D3: methodology §9 phase vocabulary adopted in quality-gate.md; derived counter fields documented.
- D4: wildcard punycode semantics resolved in anti-patterns B3; 0.3 SEO-farm threshold reframed as defense-in-depth.
- D5: `.claude/CLAUDE.md` added as primary spec anchor; README file trees updated.
- D6: `tests/` harness + `.github/workflows/validate.yml` added; `examples/eu-ai-act-2026/` fixture added; Tavily pre-flight verification step added to Quick Start.

## [0.1.0] — 2026-04-17

Initial release: 7-phase pipeline + human gate, NATO Admiralty 2×6 grading on a 4-tier domain registry, CRAG loop, punycode homograph defense, Perplexity-calibrated source targets, four CWD artifacts, `deep-research-report.md` methodology anchor with SHA-256 provenance.
