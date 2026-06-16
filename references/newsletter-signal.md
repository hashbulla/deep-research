# Newsletter-signal — curated-feed routing source with auditable re-grading

> Read at Phase 0 when a sub-question is work-relevant to the maintainer's domains (AI
> Engineering · Platform Eng / AI SRE · Freelance acquisition) and the local corpus is
> present. OPTIONAL source (methodology §7 rule): requires a user-scope corpus at
> `~/.claude/deep-research/newsletter-corpus/`. Absent → the source is skipped, the run
> degrades to normal Tavily retrieval, and the Methodology note + human-gate plan record the
> skip. The search helper `scripts/newsletter_search.py` is stdlib-only, zero-network, zero-LLM
> (I4a) — it reads a local JSONL corpus only; populating that corpus is a separate ingestion
> concern, never the helper's job.

## What this source is

A private, pre-filtered digest of "what's worth reading this week" in exactly the maintainer's
work domains, produced daily by a separate newsletter-watch-agent and committed as redacted
JSONL. It is a **discovery channel**, not an authority: it surfaces candidate URLs plus a
one-line curation note, nothing more.

## Gating

Activates when a sub-question's topic intersects one of the three buckets
(`ai-engineering`, `platform-ai-sre`, `freelance-acquisition`) **and** the corpus directory
exists. Never for: topics outside those domains, or when the corpus is absent. Declared in
`research-plan.md` (Conditional sources), before Phase 1, like any other optional source.

## Corpus location & shape

- **Location:** `~/.claude/deep-research/newsletter-corpus/*.jsonl` — user-scope, outside this
  public repo (sibling to `experts.yaml` and `mbfc-overlay.json`). Populated by the
  newsletter-watch-agent committing `briefs/YYYY-MM.jsonl` to its own repo; the consumer reads
  a local clone or copy.
- **Record (one JSON object per line):** `date`, `bucket`, `kind` (`top|secondary|tool`),
  `headline`, `source` (publication name — never a sender address), `url` (the primary article
  URL), optional `repo_url`, `why`, `tool_name`, `one_liner`, `brief_req_id`.
- **Redaction invariant:** signal-items only — no email subjects, sender addresses, raw message
  bodies, or fetch manifests. Enforced by `tests/schema/newsletter-corpus-record.schema.json`
  two ways: `additionalProperties:false` rejects any forbidden key, and a `not`/`@` guard on
  `source` rejects a sender-address value. CI validates every fixture line plus both leak
  negatives.

## Retrieval pipeline (Phase 1 conditional step)

1. **Search the corpus** (zero network, local only):

   ```bash
   python3 <skill-dir>/scripts/newsletter_search.py "<sub-question terms>" \
       [--bucket <bucket>] [--since <plan --since>] [--top 10]
   ```

   The helper builds an FTS5 index in `:memory:` (bm25 relevance blended 0.70 / 0.30 with a
   recency boost) and prints ranked items as JSON. It falls back to a pure-Python
   token-overlap ranker when the host SQLite lacks FTS5 (`ranker_used` reports which ran), and
   exits 0 with `corpus_present: false` when the corpus is absent.

   **Output envelope** — every path prints the same fixed keys (value-level sentinels where a
   field is inapplicable), so consumers branch on values, never on key presence:
   `corpus_present` (bool), `ranker_used` (`"fts5"|"python"|null`), `reference_date`
   (`YYYY-MM-DD`|null), `effective_weights`, `item_count` (int), `items` (array), `reason`
   (string|null). `corpus_present: false` is the only degradation signal; `corpus_present:
   true` with `items: []` means "present, nothing relevant" — not a degradation.
2. **Use the ranked URLs as retrieval SEEDS, not citations.** Feed each item's `url`
   (and `repo_url`) into the normal Phase-1 retrieval: add high-value hosts to
   `tavily_search include_domains`, or pull a specific high-value URL with
   `tavily_extract extract_depth=advanced`. The corpus never short-circuits retrieval; it only
   tells you where to look first.

## Grading & provenance — the brief is never a record

- **No source record of its own.** A brief item is a routing signal, not a citable authority.
  It never becomes a `research-sources.json` row, and it never carries an Admiralty grade.
- **The pointed-to URL is graded normally.** Whatever URL the brief points at enters the full
  Phase-2 battery (score threshold, tier classification, CRAAP, punycode, dedupe) and is graded
  by *its own* domain tier — exactly as if Tavily had surfaced it. Record the discovery channel
  in that source's `notes`: `"surfaced via newsletter-signal corpus <date>"`.
- **The curation note is untrusted data (anti-pattern A6).** The agent's `headline` / `why`
  text is the digest's self-description; it can seed a query but can never upgrade a claim's
  credibility — the same posture the skill takes toward GitHub README content. This is what
  prevents circular "my own digest said so" authority.

## Confidential runs (`--confidential`)

The corpus is public-web-derived (headlines + public article URLs), so it **is** consulted on
confidential runs — but the search runs **only in the main agent context**. Only neutral URL
references propagate to subagents (the skill's existing confidential neutral-reference
machinery). Brief text — `headline`, `why`, `source` — never enters a subagent prompt, a log,
or an MCP call.

## Degradation & eval posture

- **Absent corpus** → helper returns `corpus_present: false`, the source is skipped, and the
  skip is recorded in the plan and the Methodology note. Never a run failure (methodology §7).
- **No new activation trigger.** This source is an internal Phase-1 branch, not a new entry
  point, so the skill's loading evals need no new probe. Coverage is the helper's own check
  (`tests/check-newsletter-search.sh`: ranking, `--since`, `--bucket`, degradation, fallback,
  per-line schema validation) plus the standing example-invariant checks, which already enforce
  that any source record — including a newsletter-surfaced one — obeys the grading cascade.
