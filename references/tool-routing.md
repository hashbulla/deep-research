# Tavily MCP tool routing

All research calls go through `mcp__tavily__*`. **Never default to built-in `WebSearch` while Tavily is reachable.** `WebSearch` is a fallback only when every Tavily tool returns a transport error; every such fallback must be recorded in `research-sources.json` under `notes: "WebSearch fallback: Tavily unreachable at <timestamp>"`.

## Routing table

| Intent | Tool | Key params | Phase |
|---|---|---|---|
| Multi-step agentic sub-question synthesis (exhaustive mode) | `mcp__tavily__tavily_research` | `model=pro` | Phase 4 |
| Narrow factual sub-question | `mcp__tavily__tavily_research` | `model=mini` | Phase 4 |
| General deep search per sub-question (default) | `mcp__tavily__tavily_search` | `search_depth=advanced`, `include_raw_content=true`, `max_results=10` | Phase 1 |
| Time-sensitive / news sub-question | `mcp__tavily__tavily_search` | + `time_range=day\|week\|month\|year`, `start_date`, `end_date`, optional `country` | Phase 1 |
| Fast lookup / landscape scan | `mcp__tavily__tavily_search` | `search_depth=fast` | Phase 1 when doing "start wide" sweep |
| Domain structure discovery | `mcp__tavily__tavily_map` | `max_depth`, `select_paths` | Phase 1 (ahead of targeted search) |
| Full-site audit with NL instructions | `mcp__tavily__tavily_crawl` | `max_depth`, `instructions`, `select_paths` | Phase 4 when a single authoritative site must be swept |
| Known-URL full content extraction | `mcp__tavily__tavily_extract` | `extract_depth=advanced` | Phase 4 for surgical quotes |
| Library / API doc lookup | `mcp__tavily__tavily_skill` | `library`, `language`, `task` | **Out of scope** — skill must not activate for doc lookups |
| Fallback (every Tavily tool unreachable) | built-in `WebSearch` | — | Any phase, only after transport failure |

## Default Phase-1 call template

```
mcp__tavily__tavily_search(
    query=<sub_question_query>,
    search_depth="advanced",
    include_raw_content=true,
    max_results=10,
    include_domains=<tier_profile_allowlist> + <--domains>,
    exclude_domains=<tier_profile_blocklist> + <--exclude>,
    # optional:
    time_range=<if recency-sensitive>,
    start_date=<--since> if present,
    country=<if regional relevance>,
)
```

## Default Phase-4 call template

```
mcp__tavily__tavily_research(
    query=<narrow_sub_question>,
    model=<"pro" if --length=exhaustive else "mini">,
    # Tavily handles the inner loop; we still log every source it returns.
)
```

## Pacing

- Tavily Research endpoint rate limit: **20 req/min**.
- Tavily Search is cheaper but also rate-limited; treat a 429 from any Tavily tool as a hard backoff signal.
- Backoff policy: 30s → 60s → 120s, max 3 retries. After the third 429, degrade the affected sub-question to `tavily_search` + manual decomposition (breaking one `tavily_research` call into 3–5 `tavily_search` calls spread across 60s).
- For `--length exhaustive`, interleave tool types: `tavily_search` calls can run in bursts of ~10 in parallel; `tavily_research` calls must be staggered to stay ≤15/min (leaves budget for retries and Phase-5 CRAG supplementary searches).

## Tool selection decision table

1. **Is the sub-question "what is the structure of domain X"?** → `tavily_map` first, then `tavily_search`.
2. **Is the sub-question about a single well-identified paper / URL?** → Start with `tavily_extract extract_depth=advanced` on that URL. Supplement with `tavily_search` for corroborators.
3. **Is the sub-question time-sensitive (date in question, or recency category)?** → `tavily_search` + `time_range` / `start_date`.
4. **Is the sub-question a narrow multi-hop factoid?** → Phase-1 broad `tavily_search`, then Phase-4 `tavily_research model=mini` for synthesis.
5. **Is the sub-question broad, comparative, or multi-perspective?** → Phase-1 `tavily_search` (advanced) × multiple reformulations, then Phase-4 `tavily_research model=pro`.
6. **Is a single authoritative site the primary source (e.g., an official regulatory site)?** → `tavily_crawl` with `instructions` describing what to collect.
7. **Is this a library / SDK doc question?** → The skill should not have activated. Route the user to `tavily_skill` directly and exit.

## Conditional non-Tavily source: Context7 (version-current library docs)

OPTIONAL source (methodology §7 optional-source rule applies: MCP absent or quota exhausted → degrade to Tavily, record in the Methodology note, declare in `research-plan.md` before Phase 1).

**Gating — ALL three conditions, checked at Phase 0; otherwise zero Context7 calls** (free tier is 1,000 calls/month — never auto-invoke broadly):

1. Query classified `technical`, AND
2. a **named dependency** appears in the question or a sub-question (library / framework / SDK / CLI / cloud service, optionally with a version), AND
3. the sub-question intent is *integrate / configure / debug / migrate / understand* that dependency's surface.

| Intent | Route |
|---|---|
| Version-specific API surface, CLI flags, cloud config, version migration of a NAMED dependency | `mcp__context7__resolve-library-id` → `mcp__context7__query-docs` (confirm library + version in one sentence; mention the version in the query for pinning) |
| Comparative research across libraries (X vs Y vs Z) | Tavily — Context7 is per-library; never gate-passes comparative sub-questions |
| Pure CS concepts, business logic, the user's own code | Neither — out of the skill's Context7 scope entirely |
| `query-docs` returns "Documentation not found or not finalized for this version" | Escalate to `mcp__tavily__tavily_skill` (`library`, `language`, `task`), then ordinary `tavily_search` |

**Grading & provenance.** Context7 chunks are canonical vendor documentation → Tier 1 (official docs domain) or Tier 2 per the registry (§6). Context7 returns chunks, not URLs: each cited chunk becomes a `research-sources.json` record with `retrieval_tool: "context7_query_docs"`, `url` set to the canonical documentation URL the chunk maps to, `tavily_score: null` (score-less tool), and `doc_provenance: {library_id, version, section}`. Cache lookups per `library_id + version` within a run — never re-query the same pair.

**Phase placement.** Phase 1 (doc retrieval for gated sub-questions, alongside Tavily) and Phase 4 (targeted follow-up on a specific API section). All Context7-sourced chunks pass the full Phase-2 gate battery like any other source. `research-plan.md` declares which libraries/versions will be queried — written before Phase 1.

## Non-Tavily fallback tools

- **Built-in `fetch` MCP** — **do not use** for citation retrieval. Raw HTML from arbitrary URLs is a prompt-injection vector (per the user's global CLAUDE.md). `fetch` is acceptable only for raw markdown diagnostics of a URL *already* graded and cited via Tavily.
- **Built-in `WebSearch`** — fallback only. Document every use.
