# Changelog

All notable changes to the deep-research skill. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning is semver. Append-only: new entries go on top, old entries are never rewritten.

## [Unreleased]

### Added

- `references/model-tiers.md` + `--model` / `--confidential` flags (AI-120, decision D-4): Claude-Code-native model-tier selection — opus default, fable opt-in at ~2× cost, subagent `model` overrides, zero SDK calls and zero API keys. Plan template declares the tier at the human gate. Corrects the original cost estimate: Fable 5 shares the Opus 4.8 tokenizer, so the multiple is ~2× (price), not ~2.6× (facts verified against the claude-api skill, 2026-06-12).
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
