<p align="center">
  <strong>Deep Research</strong>
</p>

<p align="center">
  <em>Intelligence-grade multi-source research as a Claude Code skill, benchmarked against Perplexity Deep Research.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Claude_Code-Skill-7C3AED?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiPjxwYXRoIGQ9Ik0xMiAyTDIgN2wxMCA1IDEwLTV6Ii8+PHBhdGggZD0iTTIgMTdsMTAgNSAxMC01Ii8+PHBhdGggZD0iTTIgMTJsMTAgNSAxMC01Ii8+PC9zdmc+" alt="Claude Code Skill">
  <img src="https://img.shields.io/badge/Phases-7_+_Human_Gate-E04E2A?style=for-the-badge" alt="7 Phases">
  <img src="https://img.shields.io/badge/Grading-Admiralty_A--F_×_1--6-0891B2?style=for-the-badge" alt="Admiralty">
  <img src="https://img.shields.io/badge/Target-100%2B_Sources-059669?style=for-the-badge" alt="100+ Sources">
  <img src="https://img.shields.io/badge/Retrieval-Tavily_MCP-1F2328?style=for-the-badge" alt="Tavily MCP">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" alt="MIT License">
  <img src="https://img.shields.io/badge/Runtime-2--15_min-blue?style=flat-square" alt="Runtime">
  <img src="https://img.shields.io/badge/Languages-Any-orange?style=flat-square" alt="Any Language">
</p>

---

Point it at a research question. It decomposes the question into orthogonal sub-questions, retrieves across a tiered domain registry with Tavily, grades every source on the NATO Admiralty 2×6 matrix, and hands you a report where every claim traces to a URL and an explicit confidence label. Exhaustive runs reach **100+ sources**, calibrated to Perplexity Deep Research output.

> **Why does this exist?** LLM research agents confidently synthesize from SEO farms unless you force source discipline. Anthropic's own internal research system found that *"early agents consistently chose SEO-optimized content farms over academic PDFs, even when authoritative sources were retrievable."* The fix is not better prompting alone. It is a **source-grading harness that runs before the synthesis step** — tier registry, score threshold, Admiralty reliability, CRAAP authority check, LLM-as-judge rerank, CRAG grounding loop. This skill bakes all of that into a 7-phase pipeline with **one human gate** before any retrieval call fires.

---

## What You Get

Four artifacts in your invocation directory, written atomically at the end of the run.

```
research-plan.md         # approved by you at the human gate
research-report.md       # final synthesis, inline citations, confidence tags
research-sources.json    # every cited source, Admiralty-graded
research-evidence.json   # claim → source mapping, credibility 1–6
```

### `research-report.md` excerpt

```markdown
# Impact of the EU AI Act on open-source model providers in 2026

> Research date: 2026-04-17 · Length: standard
> Source count: 42/71 · Tier 1/2 share: 86% · Median date: 2025-09-14

## Executive summary

- GPAI obligations under Articles 53–55 entered application on 2 August 2025,
  with systemic-risk provisions applying above the 10²⁵ FLOPs threshold.[^1][^2]
- The open-source exemption (Article 2(5g)) excludes free and open-source
  GPAI models from several transparency obligations unless they meet the
  systemic-risk threshold.[^1][^3] [CONFIRMED]

## 1. GPAI provisions in force in 2026

Under Article 53 of Regulation (EU) 2024/1689 [...].[^1][^4] The European AI
Office published its Code of Practice on 2025-07-10 [...].[^5] [CONFIRMED]

## Contradictions & open debates

The scope of "sufficiently detailed summary" of training data remains disputed.
The Commission's July 2025 template[^5] is interpreted by Meta[^6] as [...],
while Mozilla[^7] argues [...]. [POSSIBLY TRUE — contested]

## Needs Verification

- Claim that compliance costs exceed €1M for small open-source providers —
  rests on a single trade-press source[^12] without regulatory corroboration.

## Sources

[^1]: Regulation (EU) 2024/1689 — eur-lex.europa.eu — Tier 1, Admiralty A1
[^2]: European AI Office GPAI guidance — digital-strategy.ec.europa.eu — Tier 1, A1
[...]
```

### `research-evidence.json` schema

```json
{
  "claim_id": "C001",
  "claim_text": "GPAI obligations under Articles 53–55 entered application on 2 August 2025.",
  "supporting_source_ids": ["S001", "S002"],
  "contradicting_source_ids": [],
  "admiralty_credibility": 1,
  "label": "CONFIRMED",
  "corroboration_count": 2,
  "independent_tier12_count": 2,
  "primary_source_present": true
}
```

Every claim in the report has a record. No URL is fabricated; no claim is silent about its provenance.

---

## Quick Start

### Install

```bash
gh repo clone hashbulla/deep-research ~/.claude/skills/deep-research
```

Claude Code discovers the skill automatically. No restart needed.

### Run

```bash
# Standard run, language inferred from the question
/deep-research impact of EU AI Act on open-source model providers in 2026

# Exhaustive run in French, with recency and custom domains
/deep-research --length exhaustive --lang fr \
  --since 2025 --domains anthropic.com,mistral.ai \
  comparaison LangGraph / CrewAI / AutoGen / Claude Agent SDK

# Narrow factual with recency gate
/deep-research --since 2025 prompt caching cost-performance tradeoffs
```

### Prerequisites

| Requirement | Why | Check |
|:------------|:----|:------|
| ![Claude Code](https://img.shields.io/badge/Claude_Code-required-7C3AED?style=flat-square) | Runtime for the skill | `claude --version` |
| ![Opus](https://img.shields.io/badge/Opus/Sonnet_4.6%2B-recommended-E04E2A?style=flat-square) | Synthesis quality and Admiralty discipline benefit from top-tier reasoning | `/model opus` |
| ![Tavily MCP](https://img.shields.io/badge/Tavily_MCP-required-1F2328?style=flat-square) | Every retrieval call. `WebSearch` is fallback only. | Visible in `/mcp` |
| ![gh CLI](https://img.shields.io/badge/gh_CLI-optional-6B7280?style=flat-square) | Only for installing from this repo | `gh auth status` |

> **Verify Tavily is registered before invoking:**
>
> ```bash
> claude mcp list | grep tavily
> ```
>
> If the grep returns no match, register the Tavily remote MCP server at user scope (see [Troubleshooting](#troubleshooting)). The skill halts at Phase 0 with an explicit error if `mcp__tavily__*` tools are not visible.

### Invocation flags

| Flag | Values | Default | Effect |
|------|--------|---------|--------|
| `--length` | `short` \| `standard` \| `exhaustive` | `standard` | Calibrates sub-question count, recall breadth, source target (15–25 / 35–60 / **100+**) |
| `--lang` | ISO 639-1 | inferred | Output language of `research-report.md` |
| `--since` | `YYYY` or `YYYY-MM-DD` | inferred | Lower bound on source publication date |
| `--domains` | comma list | tier profile | Additional allowlist appended to the tier profile |
| `--exclude` | comma list | tier blocklist | Additional blocklist |
| `--profile` | `academic` \| `technical` \| `current-affairs` \| `mixed` | inferred | Selects `include_domains` baseline from the tier registry |
| `--min-corroboration` | int ≥ 1 | `2` | Min independent Tier 1/2 sources required to mark a claim CONFIRMED |

---

## Pipeline

```mermaid
flowchart TD
    Start(["/deep-research &lt;question&gt;"]) --> P0

    subgraph P0["Phase 0 — Query Architect"]
        B1[Parse question & flags] --> B2[Classify: academic/technical/current/mixed]
        B2 --> B3[Decompose into sub-questions<br/>factual · contextual · contradictory · recency]
        B3 --> B4[Assemble tier profile<br/>+ include_domains preview]
        B4 --> B5[Write research-plan.md]
    end

    P0 --> G1

    G1{{"HUMAN GATE\n\nreview the plan\napprove / edit / cancel\nno Tavily call before approval"}}
    G1 -- "approve" --> P1

    subgraph P1["Phase 1 — Broad Retrieval"]
        direction LR
        R1["tavily_search<br/>search_depth=advanced"] --> R2["tavily_map<br/>for domain discovery"]
        R2 --> R3["Paced under 20 req/min"]
    end

    P1 --> P2

    subgraph P2["Phase 2 — Source Grading"]
        direction LR
        S1["score &gt; 0.7"] --> S2["Tier 1–4 classification"]
        S2 --> S3["CRAAP Currency + Authority"]
        S3 --> S4["Admiralty A–F"]
        S4 --> S5["Dedupe canonical URL<br/>punycode check"]
    end

    P2 --> P3

    subgraph P3["Phase 3 — Precision Rerank"]
        direction LR
        J1["LLM-as-judge pointwise<br/>≤10 docs per sub-question"] --> J2["Primary vs secondary"]
        J2 --> J3["Top 5–7 selected"]
    end

    P3 --> P4

    subgraph P4["Phase 4 — Deep Extract & Synthesis"]
        direction LR
        E1["tavily_research<br/>mini / pro"] --> E2["tavily_extract<br/>extract_depth=advanced"]
        E2 --> E3["Write research-report.md<br/>surgical quotes only"]
    end

    P4 --> P5

    subgraph P5["Phase 5 — CRAG Grounding"]
        direction LR
        C1["groundedness ≥ 0.95?<br/>corroboration ≥ 0.80?"] --> C2{gates pass}
        C2 -- "no, &lt;2 iters" --> Req["rewrite query →<br/>tavily_search supplement"]
        Req --> C1
        C2 -- "yes, or 2 iters done" --> C3["move failing claims<br/>to Needs Verification"]
    end

    P5 --> P6

    subgraph P6["Phase 6 — Confidence Annotation"]
        direction LR
        Z1["Admiralty credibility 1–6<br/>per claim"] --> Z2["CONFIRMED / PROBABLY TRUE /<br/>POSSIBLY TRUE → main body"]
        Z2 --> Z3["DOUBTFUL / IMPROBABLE /<br/>UNVERIFIED → Needs Verification"]
    end

    P6 --> Done(["4 artifacts written atomically"])

    style G1 fill:#FEF3C7,stroke:#D97706,color:#92400E
    style P1 fill:#DBEAFE,stroke:#3B82F6
    style P2 fill:#FEF9C3,stroke:#CA8A04
    style P3 fill:#FEF9C3,stroke:#CA8A04
    style P4 fill:#DCFCE7,stroke:#059669
    style P5 fill:#FEE2E2,stroke:#EF4444
    style P6 fill:#F3F4F6,stroke:#6B7280
    style Start fill:#7C3AED,stroke:#7C3AED,color:#fff
    style Done fill:#059669,stroke:#059669,color:#fff
```

### The Human Gate

Three minutes of your attention, one decision. You review the plan — classification, sub-question decomposition, domain allowlist preview, estimated Tavily calls, stop conditions — and approve or edit. **No retrieval call fires before approval.** This is non-negotiable; it is the single most effective intervention against wasted runtime and off-target research.

| Gate | Purpose | Time |
|:-----|:--------|:-----|
| ![Gate](https://img.shields.io/badge/Phase_0-Plan_Approval-D97706?style=flat-square) | Catches bad classification, wrong tier profile, and missed sub-question categories before any Tavily credit is spent | ~2–3 min |

---

## Source Grading

Three overlapping disciplines, applied deterministically in Phase 2 and probabilistically in Phase 3.

### 1. The tier registry

Every domain classified before any content enters the synthesis prompt. Based on Anthropic's internal finding that unconstrained agents drift toward SEO content.

| Tier | Examples | Admiralty reliability | Usage |
|:----:|:---------|:---------------------:|:------|
| **1** | `arxiv.org`, `pubmed.ncbi.nlm.nih.gov`, `nature.com`, `*.gov`, `*.europa.eu`, `who.int` | **A** | Primary sources; preferred in `include_domains` |
| **2** | `anthropic.com`, `openai.com`, `reuters.com`, `ft.com`, `docs.python.org`, `gartner.com` | **B** | Default retrieval baseline (Tier 1+2 union) |
| **3** | `techcrunch.com`, `wired.com`, `arstechnica.com`, `substack.com` (institution-affiliated) | **C** | Acceptable only with corroboration from Tier 1/2 |
| **4** | `reddit.com`, `x.com`, `linkedin.com`, `medium.com` | **D–F** | Never primary. Social-signal pointers only, in a labeled `Signals` subsection |

Full list in [`references/methodology.md §6`](references/methodology.md).

### 2. NATO Admiralty 2×6 matrix

Two orthogonal axes: **reliability** of the source, **credibility** of the information after corroboration. Every cited source carries a reliability letter; every claim in `research-evidence.json` carries a credibility digit.

```mermaid
flowchart LR
    Tier["Domain tier<br/>(1–4)"] --> Rel["Reliability<br/>A / B / C / D / E / F"]
    Rel --> Pair["Source record<br/>e.g. A1, B2, C3"]
    Corr["Independent<br/>corroborating sources"] --> Cred["Credibility<br/>1 / 2 / 3 / 4 / 5 / 6"]
    Contra["Contradicting<br/>sources"] --> Cred
    Cred --> Pair
    Pair --> Label["Claim label<br/>CONFIRMED / PROBABLY TRUE /<br/>POSSIBLY TRUE / …"]

    style Tier fill:#DBEAFE,stroke:#3B82F6
    style Rel fill:#DBEAFE,stroke:#3B82F6
    style Corr fill:#FEF3C7,stroke:#D97706
    style Cred fill:#FEF3C7,stroke:#D97706
    style Contra fill:#FEE2E2,stroke:#EF4444
    style Pair fill:#DCFCE7,stroke:#059669
    style Label fill:#059669,stroke:#059669,color:#fff
```

Credibility rules are deterministic — no LLM fluency-weighted guessing:

| Credibility | Condition | Label |
|:-----------:|:----------|:------|
| 1 | ≥2 independent Tier 1/2 sources agree, no contradiction | **CONFIRMED** |
| 2 | 1 Tier 1 source, or ≥2 Tier 2 sources agree | **PROBABLY TRUE** |
| 3 | Single Tier 1/2 source, or Tier 2+3 agree | **POSSIBLY TRUE** |
| 4 | Contradicted by ≥1 equally authoritative source | **DOUBTFUL** |
| 5 | Contradicted by ≥2 Tier 1/2 sources | **IMPROBABLE** |
| 6 | Single Tier 3/4 source, no corroboration | **UNVERIFIED** |

Labels 4/5/6 cannot appear in the main report body — they route to the **Needs Verification** section with an explicit reason.

### 3. Quality gates

Applied post-synthesis. Failing a gate triggers a CRAG re-query loop (up to 2 iterations per sub-question) before any claim ships.

| Gate | Threshold | Failure action |
|------|:---------:|:---------------|
| Groundedness | ≥ 0.95 | CRAG re-query for unsupported claims |
| Source quality | ≥ 0.80 Tier 1/2 | Expand allowlist, re-retrieve |
| Coverage | ≥ 0.90 sub-questions | Add follow-up sub-question |
| Freshness | Median within `--since` window | Add recency sub-question |
| Corroboration rate | ≥ 0.80 | Re-query; else → Needs Verification |

Full thresholds in [`references/quality-gate.md`](references/quality-gate.md).

---

## Architecture

Six-phase orchestrator, single `SKILL.md` entry point, methodology externalized into reference files loaded on demand.

```mermaid
graph LR
    O["SKILL.md<br><i>Orchestrator (7 phases)</i>"]

    O -. Phase 0 reads .-> M["references/methodology.md<br><i>Operational spec (report distillation)</i>"]
    O -. Phase 0 reads .-> T["references/tool-routing.md<br><i>Tavily binding table</i>"]
    O -. Phase 0 reads .-> P["references/research-plan-template.md<br><i>Phase 0 scaffold</i>"]
    O -. Phase 4 reads .-> S["references/report-structure.md<br><i>Output + JSON schemas</i>"]
    O -. Phase 5 reads .-> Q["references/quality-gate.md<br><i>Deterministic thresholds</i>"]
    O -. any phase .-> A["references/anti-patterns.md<br><i>Forbidden behaviors</i>"]

    O -- calls --> TVS(["mcp__tavily__tavily_search"])
    O -- calls --> TVR(["mcp__tavily__tavily_research"])
    O -- calls --> TVE(["mcp__tavily__tavily_extract"])
    O -- calls --> TVM(["mcp__tavily__tavily_map"])

    O -- writes --> plan[("research-plan.md")]
    O -- writes --> report[("research-report.md")]
    O -- writes --> sources[("research-sources.json")]
    O -- writes --> evidence[("research-evidence.json")]
```

### File structure

```
~/.claude/skills/deep-research/
├── .claude/CLAUDE.md                      # Maintainer spec anchor — invariants, gotchas, conventions
├── SKILL.md                               # Orchestrator — 7 phases, human gate, provenance block
├── deep-research-report.md                # Methodology source of truth (cited below)
└── references/
    ├── methodology.md                     # Full distillation — tier registry, Admiralty, CRAAP, CRAG
    ├── tool-routing.md                    # Tavily MCP tool selection per intent
    ├── report-structure.md                # research-report.md structure + JSON schemas
    ├── quality-gate.md                    # Deterministic thresholds, CRAG triggers
    ├── anti-patterns.md                   # Non-negotiables (no fabricated URLs, no WebSearch, etc.)
    └── research-plan-template.md          # Phase 0 scaffold
```

### Design decisions

| Decision | Choice | Rationale |
|:---------|:-------|:----------|
| Primary retrieval | `tavily_search search_depth=advanced` | Per-phase control; Tavily already reranks semantic chunks |
| Synthesis for narrow sub-questions | `tavily_research model=mini\|pro` | Delegates the inner Perplexity-style loop where useful |
| Stage-2 rerank | LLM-as-judge (≤10 docs) | Cohere Rerank / cross-encoders not available as MCP; judge approximates cross-encoder accuracy |
| Pre-context filtering | Inline Claude reasoning on Tavily results | Anthropic's Dynamic Filtering is API-side only; inline filtering achieves equivalent discipline |
| Source grading | NATO Admiralty 2×6 | Intelligence-grade provenance, usable by humans, deterministic |
| Contradiction handling | Dedicated report section | Report §1 stage 4 — never silent, never auto-resolve between equally authoritative sources |

---

## Troubleshooting

<details>
<summary><strong>Tavily MCP not registered</strong></summary>

The skill halts at Phase 0 if `mcp__tavily__*` tools are not visible. Register the Tavily remote MCP server at user scope:

```bash
claude mcp add --scope user tavily --transport http https://mcp.tavily.com/mcp/
```

Then re-invoke.
</details>

<details>
<summary><strong>Tavily rate limit (429)</strong></summary>

Research endpoint is capped at 20 req/min. The skill backs off at 30s → 60s → 120s. On persistent 429, affected sub-questions degrade automatically to `tavily_search` + manual decomposition. Documented in the Methodology note of the final report.
</details>

<details>
<summary><strong>Exhaustive run came back with &lt; 100 sources</strong></summary>

The skill expands the allowlist to the Tier 1+2 union and adds 2–4 contextual/recency sub-questions automatically before proceeding to Phase 4. If it still falls short, the Methodology note documents why (e.g., narrow topic, paywall-dominant domain). The 100+ target is a quality calibration, not a hard contract.
</details>

<details>
<summary><strong>A claim I expected to see ended up in Needs Verification</strong></summary>

The corroboration threshold is `--min-corroboration 2` by default. A single Tier 1 source with no second independent corroborator yields credibility 3, which is still in the main body. Credibility 4–6 (contradicted, single Tier 3/4, etc.) routes to Needs Verification. Raise `--min-corroboration 3` for stricter runs, or examine `research-evidence.json` for the exact support graph.
</details>

<details>
<summary><strong>I want to override the tier profile</strong></summary>

Use `--profile academic|technical|current-affairs|mixed` or pass `--domains` directly. User-specified domains are unioned with the tier profile; they are never silently dropped. Any `--domains` entry below Tier 2 is flagged in `research-plan.md` for your confirmation at the human gate.
</details>

<details>
<summary><strong>Output language mismatch</strong></summary>

`--lang` wins over the question's language. The skill preserves original-language proper nouns (legislation names, institution names, paper titles) inside the translated report to keep citation traceability.
</details>

---

## Extending

| Goal | How |
|:-----|:----|
| **Tune the tier registry** | Edit [`references/methodology.md §6`](references/methodology.md). Add domains to Tier 1/2; rebuild the include_domains preview at the top of the plan template. |
| **Adjust quality gates** | Edit [`references/quality-gate.md`](references/quality-gate.md). Thresholds are deterministic; raising groundedness to 0.98 simply triggers more CRAG iterations. |
| **Add a sub-question category** | Edit `SKILL.md` Phase 0 step 3 and mirror in [`references/research-plan-template.md`](references/research-plan-template.md). |
| **Change default length calibration** | Edit the "Length calibration" table in [`references/methodology.md`](references/methodology.md). |
| **Swap Tavily for another MCP** | Edit [`references/tool-routing.md`](references/tool-routing.md) and the Phase 1 / Phase 4 call templates in `SKILL.md`. Keep the grading phases intact — they are MCP-agnostic. |

---

## Roadmap

| Status | Feature |
|:------:|:--------|
| ![Done](https://img.shields.io/badge/-Done-059669?style=flat-square) | 7-phase pipeline with human gate |
| ![Done](https://img.shields.io/badge/-Done-059669?style=flat-square) | NATO Admiralty 2×6 grading with deterministic credibility assignment |
| ![Done](https://img.shields.io/badge/-Done-059669?style=flat-square) | CRAG grounding loop (2 iterations max, graceful Needs-Verification fallback) |
| ![Done](https://img.shields.io/badge/-Done-059669?style=flat-square) | Unicode homograph defense (punycode normalization of every domain) |
| ![Done](https://img.shields.io/badge/-Done-059669?style=flat-square) | 100+ source exhaustive calibration |
| ![Planned](https://img.shields.io/badge/-Planned-D97706?style=flat-square) | Exa `findSimilar` MCP for academic citation chaining |
| ![Planned](https://img.shields.io/badge/-Planned-D97706?style=flat-square) | Valyu academic index integration (arXiv / PubMed / bioRxiv full-text) |
| ![Planned](https://img.shields.io/badge/-Planned-D97706?style=flat-square) | NewsGuard / MBFC ratings overlay on the tier registry |
| ![Future](https://img.shields.io/badge/-Future-6B7280?style=flat-square) | External-model judge (Gemini / GPT-4) to break LLM-as-judge circularity |
| ![Future](https://img.shields.io/badge/-Future-6B7280?style=flat-square) | Citation graph export (BibTeX / RIS) for academic handoff |
| ![Future](https://img.shields.io/badge/-Future-6B7280?style=flat-square) | Benchmark harness vs Perplexity Deep Research on a fixed test set |

---

## Research Foundation

The full methodology is in [`deep-research-report.md`](deep-research-report.md) — a standalone intelligence brief on state-of-the-art web search techniques for AI agents. The `references/methodology.md` file is a near-verbatim distillation of that report, with every skill rule back-referenced to its source section (`[R§n]`).

The report synthesizes these sources, each directly wired into a specific part of the skill:

| Source | Used for | Skill location |
|:-------|:---------|:---------------|
| [Perplexity Deep Research](https://www.perplexity.ai/hub/blog/introducing-perplexity-deep-research) | 5-stage retrieve-reason-refine loop, tiered source preference | SKILL.md Phase 0–6 shape |
| [Anthropic · Multi-agent research system](https://www.anthropic.com/engineering/built-multi-agent-research-system) | Orchestrator-worker pattern, "start wide then narrow", SEO-farm failure mode | Phase 1 parallel retrieval, prompt structure |
| [Anthropic · Web search tool (domain controls)](https://docs.claude.com/en/docs/build-with-claude/tool-use/web-search-tool) | `allowed_domains` / `blocked_domains`, Unicode homograph defense | Phase 2 domain normalization |
| [Anthropic · Building effective agents](https://www.anthropic.com/research/building-effective-agents) | Extended / interleaved thinking, source quality as first-class metric | Phase 0 decomposition, Phase 3 rerank |
| [Anthropic · Agent evaluation guide (2026)](https://www.anthropic.com/engineering/claude-evals) | Groundedness + Coverage + Source Quality triad | Phase 5 CRAG gates |
| [Tavily API documentation](https://docs.tavily.com/) | `search_depth=advanced`, `include_domains`, `score` filter, Research endpoint | Phase 1, Phase 4 tool routing |
| [Corrective RAG (CRAG)](https://arxiv.org/abs/2401.15884) | Post-synthesis claim grading and re-query loop | Phase 5 |
| [LevelRAG / PRISM query decomposition](https://arxiv.org/abs/2502.18139) | CoT decomposition patterns for multi-hop queries | Phase 0 |
| [NATO Admiralty source grading](https://en.wikipedia.org/wiki/Admiralty_code) | A–F × 1–6 matrix for intelligence-grade provenance | Phase 2, Phase 6 |
| [CRAAP Test](https://library.csuchico.edu/craap-test) | Currency · Relevance · Authority · Accuracy · Purpose automation | Phase 2 filter gates |
| [OSINT five-step validation](https://www.osintframework.com/) | Independent corroboration, primary-source chain, confidence-trap defense | Phase 5, anti-patterns |

A curated domain tier registry (≈ 60 Tier 1 domains + ≈ 40 Tier 2) is embedded in [`references/methodology.md §6`](references/methodology.md). Full bibliography and methodology rationale in [`deep-research-report.md`](deep-research-report.md).

---

## Repository layout

```
deep-research/
├── .claude/CLAUDE.md                      # maintainer spec anchor
├── README.md                              # this file
├── LICENSE                                # MIT
├── SKILL.md                               # skill entry point
├── deep-research-report.md                # methodology source of truth
├── references/
│   ├── methodology.md
│   ├── tool-routing.md
│   ├── report-structure.md
│   ├── quality-gate.md
│   ├── anti-patterns.md
│   └── research-plan-template.md
├── examples/eu-ai-act-2026/               # end-to-end fixture (4 artifacts)
├── tests/                                 # cross-reference / provenance / schema checks
│   ├── check-cross-references.sh
│   ├── check-provenance.sh
│   ├── check-schema.sh
│   ├── schema/{research-sources,research-evidence}.schema.json
│   └── fixtures/ → examples/eu-ai-act-2026/*.json
└── .github/workflows/validate.yml         # CI — runs the three checks on push
```

### Sync model

The canonical copy is this repository. If you symlink instead of clone (e.g., `ln -s "$PWD" ~/.claude/skills/deep-research` from a working directory that holds the repo), edits propagate to Claude Code immediately. The default `gh repo clone hashbulla/deep-research ~/.claude/skills/deep-research` install creates a regular clone — commit upstream from that directory to publish changes.

---

<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" alt="MIT">
</p>
