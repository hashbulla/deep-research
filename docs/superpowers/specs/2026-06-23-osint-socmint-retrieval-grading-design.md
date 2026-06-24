---
title: OSINT/SOCMINT retrieval + grading for deep-research
date: 2026-06-23
status: approved-design
linear: AI-183
supersedes: "AI-183 prior recommendation (keep Tavily-only)"
related: [AI-41, AI-178, AI-182]
---

# OSINT/SOCMINT retrieval + grading for deep-research

> Add an optional capability that stealth-retrieves social/protected URLs Tavily cannot fetch and grades them natively on the NATO Admiralty code — without breaking the skill's autonomy, supply-chain, or grounding guarantees.

## Context

The `/deep-research` skill currently retrieves exclusively through Tavily and treats a fetch failure on protected content as a grading-time degradation (`anti-patterns.md` B9: abstract-only → credibility capped at 3) or a hard non-citation (B5: Tier 4 social → `supporting_source_ids` violation). The owner's position, settled over four rounds of adversarial review (recorded on AI-183), is that **retrieval difficulty must not masquerade as a quality verdict**, and that social/litigious sources are first-class intelligence — "where the real intel lives" (OSINT/SOCMINT practice, owner's professional domain, own tool, clear authorization).

This spec is the design that reconciles that position with the skill's existing guarantees. It is intentionally bounded (see Non-goals).

## Decisions locked (with provenance)

All four settled through `AskUserQuestion` rounds during brainstorming on 2026-06-23:

1. **Policy spine — aggressive incl. litigious.** Stealth retrieval is allowed against bot-walled targets including litigious platforms (LinkedIn/X/Facebook). `robots.txt` is overridden. **Credentialed content stays excluded** (the secret-hygiene / unauthorized-access line). A per-run stealth-fetch cap keeps the tool research-scale, not a mass-scraper.
2. **Grading — a source is a source.** No separate output lane. Social/protected sources grade on Admiralty by their real properties. The crude web heuristics (Tier-4 floor, B5 "never cite social") are replaced by account-identity reliability. Retrieval method is a non-grading audit flag.
3. **Two safeguards survive** (both on existing axes, not a new pipeline): account-derived reliability, and an anti-amplification independence check.
4. **Architecture — isolation subagent.** A dispatched `Agent` subagent owns the Scrapling tools and returns only sanitized structured data; raw DOM never reaches the main context.

## Goals

- Retrieve relevant social/protected URLs that Tavily cannot, via a gated stealth escalation.
- Grade those sources natively on Admiralty (A–F × 1–6) so they can be cited honestly, not laundered.
- Preserve every existing guarantee: autonomous flow (no mandatory human halt, `anti-patterns.md` A1), data-never-instructions (A6), grounding/corroboration integrity (A4, B10), supply-chain portability (I4a), and deterministic script-verified gates.

## Non-goals

- **No active in-platform discovery.** The escalation acts only on URLs that surface via existing channels: Tavily results, newsletter-corpus seeds (`references/newsletter-signal.md`), and user-provided URLs. Searching *inside* LinkedIn/X for entities or topics is a separate, larger spec.
- **No new entry point / trigger.** This is an internal Phase-1/4 branch, like the newsletter source — the skill's loading evals need no new activation probe.
- **No credentialed scraping, ever.** Out of scope and forbidden.

## Architecture

### Escalation ladder (retrieval)

Cheapest rung first; fires only for a URL that is relevant to a sub-question and citable under the grading model below.

| Rung | Tool | When |
|---|---|---|
| 1 | `tavily_search` / `tavily_research` | Phase 1 / 4 — unchanged baseline |
| 2 | `tavily_extract extract_depth=advanced` | **Mandatory retry** on a thin/blocked rung-1 result before any stealth — Tavily's own protected-content path |
| 3 | Stealth subagent (`mcp__scrapling__stealthy_fetch`) | Only when rung 2 returns empty / blocked / error |

Rung-3 policy:
- `robots.txt` **overridden**, logged as `retrieval_status: robots_overridden`.
- Litigious platforms **allowed**; credentialed targets **refused**.
- **Per-run cap** `--max-stealth N` (default **12**). On reaching the cap, remaining candidates are recorded as `retrieval_status: blocked` recall gaps and the cap hit is noted in the Methodology note. The cap is the structural guarantee that this stays research-scale.

### Isolation subagent

The main agent never calls Scrapling. It dispatches an `Agent` subagent (the tool is already in `allowed-tools`) that:

1. Owns the scrapling stealth tools for the duration of the fetch.
2. Fetches the target, renders, and **strips to plain text** (no DOM, no scripts, no markup).
3. Returns a fixed-shape JSON payload only:

```json
{
  "url": "https://…",
  "fetched": true,
  "text": "<sanitized plain text, length-bounded>",
  "candidate_quotes": ["<≤600-char spans relevant to the sub-question>"],
  "account_provenance": {
    "platform": "linkedin|x|facebook|web",
    "handle": "<account handle or null>",
    "verified": true,
    "display_name": "<or null>",
    "post_timestamp": "YYYY-MM-DDTHH:MM:SSZ"
  },
  "snapshot_sha256": "<hash of the persisted sanitized snapshot>",
  "robots_state": "allowed|overridden",
  "injection_suspect": false
}
```

Raw DOM/HTML is discarded inside the subagent and never crosses back. `injection_suspect: true` (imperative content addressed to an AI) forces the existing A6 handling on the resulting source record: reliability downgraded to **E**, flagged in `notes`.

> **Implementation note.** Verify how an `Agent` subagent dispatched from a skill inherits/limits tool access in Claude Code. Target: the scrapling tools are reachable inside the subagent but the main skill agent's surface grows minimally. Fallback: add the scrapling tools to the skill `allowed-tools` and confine their use to the subagent dispatch by discipline + review.

### Grading model — a source is a source

Social/protected sources enter `research-sources.json` and grade on Admiralty by their real properties. Two safeguards, both on existing axes:

**Safeguard 1 — account-derived reliability.** When `domain_tier` cannot meaningfully grade a source (account-based platforms), Admiralty reliability A–F is derived from account identity, per a new sub-rubric in `methodology.md` §6. Each reliability band also maps to a derived `domain_tier`, so the existing tier-dependent rules (`primary_source: true ⇒ domain_tier ≤ 2`; corroboration requirements for tier ≥ 3) keep working unchanged:

| Reliability | Account basis | Derived `domain_tier` |
|---|---|---|
| A / B | Verified institutional / official account (government agency, company official, established outlet) | 2 |
| C | Established, real-identity named expert, domain-relevant, unverified | 3 |
| D | Pseudonymous but consistent track record | 4 |
| E | Anonymous / burner / low history, **or** injection-suspect | 4 |
| F | Impersonation- or deception-suspect | 4 |

Tier 1 stays reserved for canonical domains (official journals, regulators) — even a verified account caps at tier 2. The mapping re-encodes B5's spirit: an anonymous social source (tier 4) can never be `primary_source`, while a verified institutional account (tier 2) can.

**Safeguard 2 — anti-amplification independence check** (extends B10). Before N social sources count as N independent corroborations toward credibility: cluster by content similarity + timing. Near-identical text posted across accounts in a tight window is **coordinated amplification → counts as one source**. Independence requires distinct authorship with no detectable shared origin or coordination signal. `verify_gates.py` flags suspicious clusters deterministically (normalized-text hash + timestamp proximity); the final independence call is a grader judgment recorded in `notes`.

**Invariants preserved:**
- Retrieval method **never** affects the grade. A stealth-fetched government PDF grades identically to a Tavily-fetched one. `retrieval_status` is audit metadata only.
- A single social source **never** alone-supports a CONFIRMED claim (A4 unchanged — CONFIRMED still requires the normative cascade).
- Ephemeral sources persist a snapshot (`snapshot_sha256`) so the citation stays verifiable after deletion (reuses the existing `anchor.snapshot_char_range` machinery, `report-structure.md` §4).

## Schema changes (`research-sources.json` + schema)

- `retrieval_tool` enum **+= `scrapling_stealth`**.
- New `retrieval_status` (enum): `direct | stealth | robots_overridden | blocked`. Audit only; never affects grade. `additionalProperties:false` requires adding it to the schema explicitly.
- New optional `account_provenance` object: `{platform, handle, verified, account_reliability_basis}` — present only for account-based sources.
- `domain_tier` for account-based sources is **derived** from account-reliability per the Safeguard-1 mapping (A/B→2, C→3, D/E/F→4); no schema change, but the emitter populates it from the rubric rather than the domain registry.
- Stealth records carry `tavily_score: null` (score-less tool) and document the admission path in `notes` (consistent with the existing null-score rule, `report-structure.md` §3).
- Snapshot persistence wiring for ephemeral sources (see GDPR posture for *where* the snapshot lives).

## Pipeline integration

- **Phase 1 (Broad Retrieval):** social/protected seeds (incl. newsletter-corpus seeds) feed in as candidate URLs.
- **Phase 2 (Source Grading):** the account-reliability sub-rubric assigns A–F for account-based sources.
- **Phase 4 (Deep Extract):** the escalation ladder runs; rung-3 dispatches the isolation subagent.
- **Phase 5 (Grounding Validation):** the anti-amplification independence check runs before corroboration counts are finalized.

`research-plan.md` declares, before Phase 1, that the stealth escalation is available and what the `--max-stealth` cap is — exactly as it declares other conditional sources.

## allowed-tools & supply-chain

- Frontmatter `allowed-tools` gains the scrapling stealth tool(s), scoped to the subagent path.
- **I4a is not violated.** This is an MCP tool call (same category as Tavily), not a `scripts/` helper. The `scripts/` supply-chain contract (stdlib-only, zero-network) is untouched; `verify_gates.py` stays offline.
- **Optional-source degradation.** If the scrapling MCP is absent (a consumer without it), rung 3 is skipped, rung-2 failures become `retrieval_status: blocked` recall gaps, and the Methodology note records the skip. Same graceful-degradation contract as Context7 / newsletter / academic. A Phase-0 availability probe (mirroring the corpus-present check) decides whether rung 3 is on.

## GDPR posture (owner's call; default = data-minimized)

The owner is EU-based; SOCMINT on named individuals is personal-data processing under GDPR requiring a lawful basis (legitimate-interest assessment) and data-minimization.

- **Default:** persist only the **cited-span** snapshot needed for verifiability into `research-evidence.json` anchors; keep any **full capture local-only**, never committed to the public repo.
- The lawful-basis determination and any retention limit are the owner's to record; this design exposes the persistence behavior as a knob, not a gate.

## Guardrail / anti-pattern changes

- **B5 reframed** — from "Tier 4 social is never cited" to "an *ungraded or anonymous-low-reliability* social source is never primary/sole support." Graded social sources are citable.
- **New B13 — amplification masquerade** — coordinated inauthentic social corroboration counts as one source (the Safeguard-2 rule).
- **New doctrine** — `robots.txt` override is logged (`retrieval_status`), capped (`--max-stealth`), and never credentialed.
- **A6 unchanged** — it already names "future retrieval extensions" as untrusted data; stealth content inherits it. The isolation subagent makes the guarantee architectural.

## Eval & verification

- New fixtures: a graded SOCMINT source (account-reliability path); an amplification-cluster negative (3 sock-puppet posts → corroboration counts as 1).
- `verify_gates.py` gains: amplification-cluster detection (normalized-text + timestamp proximity), `--max-stealth` cap conformance, `retrieval_status` accounting. All stay stdlib-only / zero-network.
- `tests/schema/research-sources.schema.json`, `check-schema.sh`, and `check-example-invariants.sh` updated for the new fields and the B5 reframing.

## Maintainer-integrity resolution

The account-reliability sub-rubric is **skill policy**, placed in `methodology.md` §6 **without** an `[R§n]` back-reference. Per I2, `tests/check-cross-references.sh` validates that every `[R§n]` that *exists* resolves — it does **not** require every subsection to carry one. So policy-only content needs no change to `deep-research-report.md` and **no re-hash (I1)**. Implementation step: confirm the cross-reference check tolerates the policy-only subsection (expected: yes).

## Implementation slices (for writing-plans)

1. Schema + fixtures: new fields, B5 reframing, example SOCMINT + amplification-negative fixtures, schema/invariant checks.
2. `verify_gates.py`: amplification clustering, cap conformance, `retrieval_status` accounting.
3. `methodology.md` §6: account-reliability sub-rubric + B13 + robots-override doctrine; `report-structure.md` field docs.
4. `SKILL.md`: `allowed-tools` delta, escalation-ladder workflow, isolation-subagent dispatch, `--max-stealth` flag, Phase-0 availability probe + plan declaration.
5. `references/` new section (or extend `tool-routing.md` / a new `osint-retrieval.md`) for the ladder + subagent contract + GDPR knob.
6. README + CHANGELOG + gotchas-log propagation (I5 single-source discipline).

## Open defaults to confirm at spec review

- `--max-stealth` default = **12** per run.
- GDPR persistence default = **cited-span snapshot only, full capture local-only**.
- Account-reliability rubric lives in `methodology.md` §6 as policy (no `[R§n]`, no re-hash).
