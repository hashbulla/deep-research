# Solution-space sweep — enumerate the market before verdicting the gate

> Read at Phase 0 on EVERY run, before `research-plan.md` is written. Gate research answers *may we, and at what price*; a solution-space map answers *what already exists*. A correct verdict sitting on a holey map is still a wrong answer — each item in [../evals/fixtures/sota-recall/README.md](../evals/fixtures/sota-recall/README.md) was missed by a run whose own verification passed. The sweep emits `research-solution-space.json` (artifact #5), whose contract is [../tests/schema/research-solution-space.schema.json](../tests/schema/research-solution-space.schema.json).

## Gating

The two geometries are different shapes of work and must not substitute for each other. **Gate research** is deep and verdict-oriented: it follows one candidate chain to the bottom, grades access legality, cost, and account risk, and returns CONFIRMED/DOUBTFUL. **Solution-space mapping** is broad and enumeration-oriented: it sweeps a closed set of categories for *every* packaged path to the outcome, shallow but complete, and returns a menu. Depth on one branch never certifies breadth across the tree.

The sweep is **universal**, not a conditional source: `research-solution-space.json` is written on every run, and the applicability declaration plus the planned per-category queries are written into `research-plan.md` before Phase 1. The sweep executes at **Phase 1b** — the stack grep runs first, before any web retrieval call, and its output feeds the query vocabulary of every subsequent call.

Applicability is an **audited declaration, never an assumption**. On a question with no solution space (a factual, historical, or regulatory question that names no capability to acquire), set `question_geometry.solution_space_applicable: false` with a reason, and record all six categories as `not-applicable` with that reason. The completeness critic still runs — on an inapplicable run its mandate is to challenge the declaration itself. `not-applicable` is reserved for this whole-question case: on an applicable question, a category you choose not to sweep is `waived` with a real reason, never `not-applicable`.

## The six categories

Closed set. Every run records exactly six category objects, one per key, in this order.

| Key | Enumerates | Instrument |
|---|---|---|
| `platform-official-api` | The real capability surface of the platform(s) named in the question — endpoints, scopes, export mechanisms, quotas — read from vendor docs, not assumed from reputation | Tavily on vendor domains; Context7 when a named SDK passes the Phase-0 gate ([tool-routing.md](tool-routing.md)) |
| `own-stack` | What the operator already owns, pays for, or has documented — connectors, subscriptions, playbooks, memory notes | `scripts/stack_inventory.py` grep over the paths in `~/.claude/deep-research/stack-paths.json` (template: [../stack-paths.json.example](../stack-paths.json.example)); its JSON output includes `skipped_files` (oversize/unreadable, with reason) — a non-empty list is triaged, never ignored |
| `open-source` | Repositories and packages implementing the capability | [github-research.md](github-research.md) — **topic-facet sweep first (≥3 distinct combinations, star-sorted, gated by Rule 7b)**, then star-band sharding, composite ranking, fake-star gate. Reuse it; do not restate its mechanics here |
| `mcp-registries` | MCP servers exposing the capability as agent tools | Named registry list below; the registries actually queried are recorded in `registries` |
| `commercial-vendors` | Priced products, enumerated **by risk class** — never by first-hit | Tavily per risk class; pricing pages extracted and dated |
| `substitution-channels` | Alternative channels reaching the same outcome by another route | Tavily on the channel vocabulary below |

**Named registries** (`mcp-registries`): official MCP Registry, Smithery, mcp.so, Glama, LobeHub, mcpservers.org. A swept `mcp-registries` category MUST list in `registries` which of the six were actually queried — an unqueried registry is a hole, and "I searched for MCP servers" is not a registry sweep.

**Risk classes** (`commercial-vendors`): `official-api-wrapper`, `managed-public-scraping`, `session-delegation`, `credentialed-self-hosted`. Every class is enumerated with at least one named representative *even when a class is gated NO-GO*. A gate is a reason to enumerate the class **better** — a risk-graded complete menu is what lets the operator price the gate — never a reason to stop enumerating. Commercial findings MUST carry `risk_class`; classes also differ by cost by an order of magnitude, so enumerate per class and compare per-unit pricing rather than stopping at the first priced option.

## Query vocabulary — capability classes, never problem words

The query vocabulary encodes the hypothesis. Search the words of your own presumed chain and you retrieve your own presumed chain; unknown-unknowns live under the market's vocabulary, not the problem's. Write every query as a **capability class the market sells**, and phrase the problem's own words out.

| Category | Capability-class vocabulary (use) | Problem vocabulary (never) |
|---|---|---|
| `platform-official-api` | "official API reference", "developer platform scopes", "data portability export", "OAuth scopes reference", "API deprecation policy" | "how to get my &lt;platform&gt; data", "&lt;platform&gt; API tutorial" |
| `own-stack` | grep the capability class: "unified messaging", "session delegation", "webhook", "OAuth connector", "inbox", "transcript", "export" | grep the platform name alone ("instagram"), or the problem ("scraper") |
| `open-source` | FIRST: `gh search repos --topic &lt;class-a&gt; --topic &lt;class-b&gt; --sort stars`, `api.github.com/search/repositories?q=topic:&lt;class&gt;&amp;sort=stars` — ≥3 distinct topic combinations, gated by Rule 7b; then "&lt;capability&gt; client library", "&lt;protocol&gt; SDK", "self-hosted &lt;capability&gt; bridge", "CLI for &lt;capability&gt;". **On a Claude/agentic question also sweep the DELIVERY FORM (Rule 7c):** `topic:claude-code+topic:&lt;capability&gt;`, `topic:agent-skills`, `filename:SKILL.md` code search, and `anthropics/skills` | "&lt;platform&gt; scraper github", `site:github.com` via a web engine (prose retrieval wearing a GitHub costume — fails Rule 7b); **tool vocabulary alone on an agentic question — it cannot see a delivery form (fails Rule 7c)** |
| `mcp-registries` | "&lt;capability&gt; MCP server", "OAuth MCP server &lt;platform&gt;", "MCP &lt;domain&gt; tools" — one query **per registry**, plus the capability verb ("enumerate", "list", "read") | "MCP for &lt;my exact task&gt;" |
| `commercial-vendors` | per risk class: "unified messaging API", "social inbox API", "managed data API pricing per 1k", "session delegation automation", "residential proxy scraping API", "iPaaS connector &lt;platform&gt;" | "&lt;platform&gt; scraper", "&lt;platform&gt; API alternative" |
| `substitution-channels` | "data portability export", "GDPR data request format", "RSS feed", "oEmbed endpoint", "email digest", "bridge to &lt;protocol&gt;", "&lt;capability&gt; via &lt;adjacent surface&gt;" | "workaround for &lt;blocked path&gt;" |

Two disciplines make this operational. **Name the modality, not the goal**: a modality absent from the prompt does not exist to the retriever, so enumerate the modalities a capability could arrive through (messaging, export, feed, webhook, delegated session) before writing queries. **Derive vocabulary from the stack sweep**: capability terms found in the operator's own notes (e.g. a playbook naming "hosted-auth session delegation") become web-query terms for the remaining five categories.

## Sweep order and breadth

1. **`own-stack` first, before any web call.** It is a local grep — effectively free, always run at full breadth regardless of `--length`, and never waived for cost. Its grep terms are recorded in `categories[].queries` exactly like any other category's queries; a `swept` own-stack category with an empty `queries` array fails the gate. Absent `~/.claude/deep-research/stack-paths.json` → status `degraded`, with a reason naming the absent config and what was lost (for example: "stack-paths.json absent — no own-stack inventory performed; paid connectors not checked"), visible in the manifest and in the report, never silent.
2. **Then the five web categories,** seeded with the vocabulary the stack sweep surfaced.

| `--length` | Web queries across the five web categories |
|---|---|
| `short` | 4–6 |
| `standard` | 6–12 |
| `exhaustive` | 12–20 |

Breadth is spent across categories, not concentrated: a run that spends all twelve queries on `commercial-vendors` has swept one category and starved five. Multi-platform questions emit **one** manifest; `question_geometry.platforms` lists the platforms and `findings[].platform` tags each row. Estimated overhead of the whole sweep: +15–25 % of a standard run.

## Status semantics

| Status | Meaning | Required beyond `key`/`status`/`reason`/`date` |
|---|---|---|
| `swept` | Queries ran, solutions found | non-empty `queries` (grep terms count as queries) **and** non-empty `findings`; `registries` on `mcp-registries`; `risk_class` on every commercial finding |
| `empty` | Queries ran, zero solutions exist | non-empty `queries` **and** `control` with `found: true` |
| `waived` | Deliberately not swept on an applicable question | a real reason — what makes this category incapable of changing the answer |
| `not-applicable` | The question has no solution space at all | a reason; valid only when `solution_space_applicable` is `false`, and then on all six |
| `degraded` | The instrument was unavailable or partial | a reason naming the instrument and what was lost |

**`empty` requires a control query.** A sweep returning nothing without proof the instrument works is indistinguishable from a broken instrument. Construct the control by picking an item you already know that category lists — a registry entry you have seen, a vendor you have priced — and query for it with the same tool and filters. Record `control: {query, expected_hit, found}`. The failure branch has teeth: `found: false` means the instrument is broken, so the status is **not** `empty` — it is `degraded`, with the failed control as the reason.

## The completeness critic

A decorrelated critic runs on **every** run, including inapplicable ones. It is an `Agent` subagent on a **different Claude model than the synthesis** — the same decorrelation mechanism as the Phase-5 entailment judge ([model-tiers.md](model-tiers.md) §"How selection actually works").

- **Inputs:** the research question, the manifest, and the category taxonomy from this file. **Never the report prose** — reading the synthesis anchors the critic on the chain it is meant to challenge.
- **Mandate:** name categories, modalities, risk classes, and registries that were never swept; countersign every waiver; challenge the `not-applicable` declaration when `solution_space_applicable` is `false`.
- **Waiver countersignature (D8):** a hollow waiver — one that restates the status instead of giving a reason the category cannot change the answer — becomes a finding. Resolve it by sweeping, or by re-waiving with a better reason. The count of waived categories appears at the top of the results Artifact.
- **Resolutions:** every finding resolves to `swept` (max **one** re-sweep iteration per run), `waived` (with a real reason), or `rejected` (the challenge did not hold, with the note saying why). All recorded in the manifest `critic` block.
- **On `--confidential`:** the standing subagent invariant (SKILL.md §Scope Constraints: confidential text never enters a subagent prompt, a log, or an MCP call) applies unchanged — the egress test below is that invariant *instantiated* for the critic, not a second rule. The critic receives only material that already lawfully egressed to Tavily — the question, the queries, the category statuses — which is by construction not confidential text. **`own-stack` findings are withheld**: they are the one category whose findings never touched the web, and shipping them to a subagent would be new egress. The critic is told the category's status, not its contents.
- **Degradation is asymmetric.** The critic is the recall instrument, not presentation: if the `Agent` tool is unavailable, record `ran: false` with a populated `skip_reason`, and expect the deterministic gate to FAIL — the run then follows the D9 path below rather than passing quietly.

## Declared incompleteness is a downstream obligation

A **declared** incompleteness is not a **treated** incompleteness. A caveat in the Methodology note is read once by its author and never again; downstream it silently becomes fact — "the inventory is non-exhaustive" turns into "nothing exists" the moment a design phase consumes it.

Hard rule: any universal negative the Phase-5 entailment judge refuses, and any inventory declared non-exhaustive, MUST create a `declared_incompleteness` entry `{kind, text, obligation}` — `kind` is `refused-universal` or `non-exhaustive-inventory`. The `obligation` states what a downstream reader must do before treating the gap as settled (re-sweep which categories, with which queries). **Every obligation is quoted at the TOP of `research-report.md`**, above the executive summary — never relegated to the Methodology note.

## The benchmark table

The sweep renders one table in `research-report.md`, one row per solution, placement fixed by [report-structure.md](report-structure.md):

| Solution | Class | Cost | Risk class | Use-case coverage | Verdict |
|---|---|---|---|---|---|

`Class` is one of `custom-build` / `built-in` / `open-source` / `commercial`, matching `findings[].class`. `Risk class` matches `findings[].risk_class`. **Every row is sourced and dated** — each carries its `research-sources.json` citation and the date the cost and capability were observed; pricing perishes faster than anything else in a research report. `custom-build` appears as a row like any other, so the reader sees what building costs against what buying costs. A category swept `empty` contributes no row; its absence is explained by the manifest, not by silence.

## Results Artifact

Results are presented in an Artifact — a private claude.ai page rendered with the Artifact tool at the end of the run (D4), carrying: the report, the benchmark table, the count of waived categories, the `declared_incompleteness` obligations, and the gate verdicts.

- **Excluded on `--confidential` runs.** Publishing is egress. Record the exclusion in the Methodology note; the operator may lift it for a given run.
- **Tool absent (headless surface):** record the graceful degradation in the Methodology note and finish. A missing Artifact is never a run failure — the five artifact files are the contract.

## Deterministic gate

At Phase 6, next to `check-artifacts`, run the solution-space gate and **quote both verdicts** in the final chat message:

```bash
python3 <skill-dir>/scripts/verify_gates.py check-solution-space --manifest research-solution-space.json
```

| Rule | Checked |
|---|---|
| `waived`, `not-applicable`, `degraded` carry a non-empty reason | yes |
| `swept` carries non-empty `queries` and non-empty `findings` | yes |
| `empty` carries non-empty `queries` and `control.found: true` | yes |
| `solution_space_applicable: false` ⇒ all six categories `not-applicable` | yes |
| `solution_space_applicable: true` ⇒ no category `not-applicable` | yes |
| `critic.ran` is `true` | yes |
| any `waived` category ⇒ `critic.waivers_reviewed` is `true` | yes |
| `registries` present on a swept `mcp-registries`; `risk_class` on commercial findings | yes — `check-solution-space` enforces both (non-empty `registries` on a swept/empty `mcp-registries`; closed `risk_class` taxonomy on commercial findings) |

The schema is permissive where the gate is strict: it accepts an empty category `reason` and a `control.found: false`. The gate is the binding instrument; write to the gate.

**Persistent FAIL (D9).** After the bounded iterations above (one critic re-sweep, one waiver re-waive), a still-failing gate does not abort the run: deliver all five artifacts and the Artifact, with the FAIL verdict as the **first line** of `research-report.md` and of the Artifact when one is rendered (a `--confidential` run skips the Artifact). A report under a FAIL verdict may not claim SOTA, "complete", or "no alternative exists".

## Manifest example

One category shown of the six the array always carries; the five siblings are elided for length.

```json
{
  "schema_version": 1,
  "generated": "2026-08-04",
  "question": "Which packaged toolchains ingest Instagram content into an agentic CLI?",
  "question_geometry": {
    "solution_space_applicable": true,
    "reason": "the question asks which existing solutions cover a capability",
    "platforms": ["instagram"]
  },
  "categories": [
    {
      "key": "commercial-vendors",
      "status": "swept",
      "reason": "four risk classes enumerated; the gated class kept in the menu, risk-graded",
      "date": "2026-08-04",
      "queries": [
        "managed instagram data API pricing per 1k requests",
        "session delegation social automation vendor"
      ],
      "findings": [
        {
          "name": "Phantombuster",
          "class": "commercial",
          "platform": "instagram",
          "risk_class": "session-delegation",
          "source_ids": ["S034"],
          "note": "takes the operator's session cookie as input; gated NO-GO, listed so the gate is priced"
        }
      ]
    }
  ],
  "declared_incompleteness": [
    {
      "kind": "refused-universal",
      "text": "no MCP server enumerates private playlists",
      "obligation": "downstream design may not consume this as fact; re-sweep the six named registries before costing a custom enumerator"
    }
  ],
  "critic": {
    "ran": true,
    "model": "sonnet",
    "waivers_reviewed": true,
    "findings": [
      {
        "finding": "substitution-channels never considered the platform's data-export path",
        "resolution": "swept",
        "note": "re-sweep added the portability export; the single iteration is consumed"
      }
    ]
  }
}
```

## Root causes closed

The five observed failures behind this file, and the mechanism that closes each. Fixtures: [../evals/fixtures/sota-recall/README.md](../evals/fixtures/sota-recall/README.md).

| Observed root cause | Mechanism | Recorded in |
|---|---|---|
| Two geometries confused — a deep verdict chain stood in for a market map | Enumeration-first sweep, universal, separate from gate research | `question_geometry`, category statuses |
| Query vocabulary encodes the hypothesis | Per-category capability-class vocabulary; problem words phrased out | `categories[].queries` |
| No instrument measures recall — rigorous verification makes a blind spot authoritative | Decorrelated completeness critic + control query on every `empty` | `critic`, `categories[].control` |
| A declared incompleteness is not a treated one | Obligations quoted at the top of the report | `declared_incompleteness` |
| Blindness to one's own stack — an unnamed modality does not exist | `own-stack` grep first, before any web call | `own-stack` category |
| A gate on a class stopped enumeration of the class | Vendors enumerated by risk class; a NO-GO completes the menu | `findings[].risk_class` |
