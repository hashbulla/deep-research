# Flags — full semantics

> Moved out of `SKILL.md` on 2026-08-04 (harness run #3, D3 load-tier remediation). `SKILL.md` §Inputs keeps every flag name, its values and its default — nothing is invisible from the body. **Read this file at Phase 0 when a flag is set** and its effect is not obvious from the one-line summary.
>
> Flag *names* are an interim default (the methodology report does not prescribe them) — see [provenance.md](provenance.md). Their *effects* are load-bearing.

| Flag | Values | Default |
|---|---|---|
| `--length` | `short` \| `standard` \| `exhaustive` | `standard` |
| `--lang` | ISO 639-1 (`fr`, `en`, …) | inferred from the question |
| `--since` | `YYYY` or `YYYY-MM-DD` | inferred from the question's freshness needs |
| `--domains` | comma-separated list | the tier profile from [methodology.md](methodology.md) §6 |
| `--exclude` | comma-separated list | the tier profile's blocklist |
| `--profile` | `academic` \| `technical` \| `current-affairs` \| `mixed` | inferred |
| `--min-corroboration` | integer ≥ 1 | `2` |
| `--model` | `opus` \| `fable` | `opus` |
| `--confidential` | boolean | off |
| `--rigor` | `standard` \| `critical` | `standard` (`critical` implied by `--confidential`) |
| `--suggest-tooling` | boolean | off |
| `--max-stealth` | integer ≥ 0 | `12` |

## Effects

- **`--length`** — calibrates sub-question count, retrieval breadth and the target source count. The per-length targets (sub-questions · broad-recall candidates · final cited · rough runtime) live in [methodology.md](methodology.md) §"Length calibration": short 3–5 · 20–30 · 15–25 · 1–2 min; standard 6–10 · 50–80 · 35–60 · 3–5 min; exhaustive 12–20 · 150–250 · **100+** · 8–15 min. It also scales the Phase-1b web sweep: 4–6 / 6–12 / 12–20 Tavily calls across the five web categories.
- **`--lang`** — the output language of `research-report.md`. On a mismatch with the question's language, the flag wins: translate internally but keep original-language key terms in search queries.
- **`--since`** — a lower bound on source publication date, passed to Tavily as `time_range` / `start_date`. `scripts/newsletter_search.py` accepts the same `YYYY` / `YYYY-MM` / `YYYY-MM-DD` forms.
- **`--domains` / `--exclude`** — additional allowlist / blocklist, **unioned** with the tier profile, never replacing it. A user-added domain below Tier 2 is a Phase-0 step-3 safety trigger: confirm inclusion and record the decision in `research-plan.md`.
- **`--profile`** — selects the domain tier profile (the `include_domains` baseline) instead of the classification inferred at Phase 0 step 4.
- **`--min-corroboration`** — the number of independent Tier 1/2 sources a claim needs to reach CONFIRMED. Also drives the Phase-3 follow-up-search trigger and the Phase-5 corroboration-rate gate.
- **`--model`** — synthesis tier. Claude-Code-native: the session model plus subagent `model` overrides, never SDK calls. Policy and mechanics in [model-tiers.md](model-tiers.md).
- **`--confidential`** — confidential-path run: subagents receive and return neutral references only, rigor escalates to `critical`, the retention posture is recorded in the plan, the newsletter corpus is consulted in the main context only, and the Phase-6 Artifact render is skipped (publishing is egress; the operator may lift that per run). See [model-tiers.md](model-tiers.md).
- **`--rigor`** — verification depth: entailment-judge scope, refuse-if-no-source, mandatory `anchor` per claim, and the Phase-0 sycophancy / false-premise probe. Profiles in [quality-gate.md](quality-gate.md) §"Rigor profiles".
- **`--suggest-tooling`** — after Phase 6 completes, delegate the finished run to the `suggest-tooling` sibling skill, which writes `research-toolbox.md` (the 6th file). Default OFF; runs are byte-identical without it. **This engine still emits exactly the five artifacts** — the sibling, not the engine, writes the extra file.
- **`--max-stealth`** — per-run ceiling on scrapling stealth dispatches (OSINT/SOCMINT rung 3). `0` disables stealth retrieval entirely. The actual count is recorded in the Methodology note and enforced by `verify_gates.py check-artifacts --max-stealth N`. Only relevant when the scrapling MCP is present. See [osint-retrieval.md](osint-retrieval.md).
