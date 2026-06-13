# Design — `newsletter-signal` conditional source for `/deep-research`

> Validated design for Linear AI-41 (Urgent). Teaches the `/deep-research` skill to consult
> the user's newsletter-watch-agent curated daily briefs as a conditional retrieval source.

## Problem

The user runs a `newsletter-watch-agent` that emits a daily curated brief across three
buckets (AI Engineering · Platform Eng + AI SRE · Freelance acquisition). Those briefs are a
high-signal, pre-filtered view of "what's worth reading this week" in exactly the user's
work domains — but they evaporate: they exist only as Telegram messages and an ephemeral,
gitignored JSON archive on a scale-to-zero Koyeb container. When the user runs a
work-relevant `/deep-research`, the pipeline cannot fold in what the curated feed already
surfaced.

## Goal

Slot a `newsletter-signal` source into the skill's existing **conditional-source
abstraction** — the exact shape used by GitHub (`references/github-research.md` +
`scripts/github_rank.py`), academic (`references/academic-research.md` +
`scripts/academic_graph.py`), and Context7. Each such source is gated at Phase 0 by query
classification, declared in the approved plan, documented in a `references/<x>.md`, optionally
backed by a stdlib-only/zero-network `scripts/<x>_*.py`, and degrades gracefully when its
dependency is absent.

## Decisions (resolved at the brainstorming gate)

1. **Storage — JSONL-of-record + in-memory FTS5.** The git-versioned JSONL corpus is the only
   durable store. `scripts/newsletter_search.py` rebuilds an FTS5 index in `:memory:` on each
   invocation (bm25 + recency boost), with a pure-Python keyword-overlap fallback when the
   host SQLite lacks FTS5. No persistent index file, no drift, no embedding infrastructure —
   appropriate at ~60 distilled items/day. Satisfies the I4a stdlib/zero-network contract.
2. **Ingestion — agent commits a redacted artifact.** The newsletter agent commits a redacted
   `briefs/YYYY-MM.jsonl` to its own repo each run, reusing its existing fine-grained PAT +
   GitHub Contents API path. The skill reads a user-scope clone at
   `~/.claude/deep-research/newsletter-corpus/` — sibling to the existing user-scope assets
   `experts.yaml` and `mbfc-overlay.json`. Durable, versioned, free. (Producer change is a
   separate commit in the agent repo.)
3. **Grading — routing signal, never a citable record.** The brief surfaces candidate URLs +
   the agent's note; every claim still grounds to the primary URL the brief points to, graded
   through the normal Phase-2 battery. The brief itself never becomes a `research-sources.json`
   record — provenance is recorded as `notes: "surfaced via newsletter-signal corpus <date>"`
   on the actually-graded source. This avoids circular "my own digest said so" authority and
   needs no new tier. The curation note is untrusted data (anti-pattern A6) and can never
   upgrade a claim — the same posture the skill takes toward GitHub READMEs.
4. **Confidential posture — consult, main-context only.** The corpus is public-web-derived
   (low risk), so it is consulted even on `--confidential` runs. But the search runs only in
   the main agent context; only neutral URL references propagate to subagents (the skill's
   existing confidential machinery). Brief text — headline, note, source — never enters a
   subagent prompt, a log, or an MCP call.

## Architecture — two repos, one contract

The JSONL schema is the seam. The work splits:

- **Consumer (this repo, AI-41 deliverable):** the contract schema, the search helper, the
  SKILL.md Phase-0/Phase-1 wiring, the same-commit doc propagation, and the tests. Buildable
  and testable now against a committed fixture corpus, independent of the producer.
- **Producer (`newsletter-watch-agent`, separate commit):** one new pipeline step that emits
  the redacted projection and commits it.

The consumer's graceful-degradation requirement means it ships and works before the producer
lands; the producer merely makes the corpus non-empty.

## The contract — `briefs/YYYY-MM.jsonl`

One JSON object per line, one per signal item. Fields: `date`, `bucket`
(`ai-engineering|platform-ai-sre|freelance-acquisition`), `kind` (`top|secondary|tool`),
`headline`, `source` (publication name — never a sender address), `url` (the primary article
URL claims ground to), `repo_url?`, `why?` (top items), `tool_name?`/`one_liner?` (tool
items), `brief_req_id?`.

**Redaction invariant (load-bearing):** signal-items only. No `subject`, no
`sender_address`/`sender_domain`, no raw `html`, no `q1_manifest`/`q2_manifest`. This is the
exact boundary the agent's own CLAUDE.md rule 14 draws. The agent's *archive* carries those
forbidden fields; the producer step must therefore project, not copy. Enforced by
`tests/schema/newsletter-corpus-record.schema.json` (`additionalProperties:false`) with CI
validating every fixture line.

## Invariants honored

- **I4a** — the helper is stdlib-only, zero-network, zero-LLM; brief *fetching* is the
  producer's concern, never the helper's.
- **I3** — methodology §9 phase vocabulary untouched; only a §6 note is added.
- **I1** — `deep-research-report.md` is not touched.
- **I5 / Extension protocol** — methodology edited first, then SKILL.md + README + skill
  CLAUDE.md propagated in the same commit.

## Out of scope (YAGNI)

Embeddings / vector RAG (overkill at this scale); a persistent on-disk index (drift surface);
on-demand `GET /archive` pull at research time (breaks the zero-network helper contract).
