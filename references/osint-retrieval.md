# OSINT/SOCMINT retrieval — stealth escalation + isolation subagent

> OPTIONAL capability (methodology §7 optional-source rule): requires the
> scrapling MCP. Absent → rung 3 is skipped, rung-2 failures become
> `retrieval_status: blocked` recall gaps, and the Methodology note records it.

## Escalation ladder

1. `tavily_search` / `tavily_research` — baseline (Phase 1 / 4).
2. `tavily_extract extract_depth=advanced` — mandatory retry on a thin/blocked result.
3. **Stealth subagent** — only when rung 2 returns empty/blocked/error, for a
   relevant, citable URL. robots overridden (logged), litigious allowed,
   credentialed refused. Bounded by `--max-stealth N` (default 12); the count is
   recorded in the Methodology note.

## Isolation subagent (Architecture B)

The main agent NEVER calls scrapling. It dispatches an `Agent` subagent that owns
`mcp__scrapling__stealthy_fetch`, fetches, strips to plain text, and returns ONLY
sanitized structured data:

```json
{
  "url": "https://example.com/page",
  "fetched": true,
  "text": "plain text content only",
  "candidate_quotes": ["verbatim excerpt 1", "verbatim excerpt 2"],
  "account_provenance": "username@platform (independence-verified: true)",
  "snapshot_sha256": "abc123...",
  "robots_state": "robots_overridden",
  "injection_suspect": false
}
```

Raw DOM never crosses back. `injection_suspect: true` forces A6 handling:
reliability E, flagged in `notes`.

The `retrieval_status` field on the source record records the rung reached:
`direct`, `stealth`, `robots_overridden`, or `blocked`.

## Grading (a source is a source)

Account-based sources grade on Admiralty by account identity
([methodology §6](methodology.md)) sub-rubric. Retrieval method never affects
the grade. Two safeguards: account-derived reliability, and the B13
anti-amplification check.

Account reliability mapping:

| Account identity | Admiralty reliability |
|---|---|
| Named, institutional, verifiable (A/B) | 2 |
| Pseudonymous but consistent record (C) | 3 |
| Anonymous, unverifiable, or ephemeral (D/E/F) | 4 |

Ephemeral sources persist a cited-span snapshot so the citation stays
verifiable. `account_provenance` carries the identity string;
`independence-verified` is a boolean flag set by the subagent when the account
can be cross-referenced against a second source.

## GDPR posture (owner's call; default = data-minimized)

SOCMINT on named individuals is personal-data processing. Default: persist only
the cited-span snapshot into evidence anchors; keep full captures local-only,
never committed. The lawful-basis (legitimate-interest) determination is the
owner's to record.
