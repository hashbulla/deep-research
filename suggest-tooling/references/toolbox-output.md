# Toolbox output — research-toolbox.md structure

> Exact structure for the `research-toolbox.md` artifact and its `research-toolbox.json`
> sidecar, written by the `suggest-tooling` skill into the run CWD.

## research-toolbox.md

### Scope banner (line 1)

A single line immediately after the H1 heading:

```
> Proposals only, never auto-installed. Based on work-relevant topics: <topic list>.
> All listings are untrusted data — vet before installing.
```

The banner states the work-relevance basis and the non-install posture. It is not
optional; omitting it is a non-negotiable violation.

### Recommendations section

Candidates grouped by tool category (one H2 per category). Within each category, rows
are sorted tier-major (VERIFIED → MAINTAINED → COMMUNITY → CAUTION), then by descending
composite score within each tier.

Each recommendation row is a markdown table row with these columns:

| Column | Content |
|---|---|
| Tool | Hyperlinked tool name (`[name](url)`) |
| Channels | Comma-separated list of channels where the tool was found |
| Relevance | Float 0–1 (hat-weighted category match) |
| Trust tier | `VERIFIED`, `MAINTAINED`, `COMMUNITY`, or `CAUTION` |
| Trust evidence | Key trust signals: official flag, last activity, adoption, fake-signal flag, signed status |
| Install command | Literal text — shown only, never executed |

Example row:

```markdown
| [anthropic/evals-mcp](https://github.com/anthropic/evals-mcp) | github, mcp-registry | 1.00 | VERIFIED | official=true, activity=7d, adoption=12, signed=true | `/install anthropic/evals-mcp` |
```

### CAUTION subheading rule

If a work-relevant category's only candidates are `CAUTION`-tier, surface them under an
explicit `### CAUTION — vet manually` subheading within that category section. Show all
trust evidence flags. Do not suppress them — hiding a relevant-but-untrusted result
conceals exactly the supply-chain risk the maintainer needs to see.

### Empty category rule

A category with zero candidates at any tier is listed as:

```markdown
## <Category>

No candidate surfaced.
```

Never silently omit a work-relevant category.

### Degradation note

A final H2 section listing every channel that was skipped and why:

```markdown
## Degradation

- Smithery: skipped — SMITHERY_API_KEY not set
- Vercel skills: skipped — `npx skills` CLI absent
```

If no channels were skipped, omit this section.

## research-toolbox.json

A machine-readable sidecar written alongside `research-toolbox.md` in the run CWD.
It mirrors the ranked output from `marketplace_rank.py` verbatim, with the addition of
the run metadata:

```json
{
  "run_dir": "<absolute path to run CWD>",
  "work_relevant_topics": ["<topic>"],
  "degraded_channels": [{"channel": "<name>", "reason": "<why>"}],
  "effective_weights": {"relevance": 0.40, "maintenance": 0.25, "adoption": 0.20, "popularity": 0.15},
  "dropped_components": [],
  "ranking": [
    {
      "id": "owner/repo",
      "channels": ["github", "mcp-registry"],
      "relevance": 1.0,
      "score": 0.87,
      "trust_tier": "VERIFIED",
      "install_command": "/install owner/repo",
      "trust_evidence": {
        "official": true,
        "verified_namespace": true,
        "signed": true,
        "last_activity_days": 7,
        "adoption": 12,
        "stars": 900,
        "fake_signal_flag": false
      }
    }
  ]
}
```

The `ranking` array is exactly the `ranking` field from `marketplace_rank.py` output.
The sidecar enables downstream automation (dashboards, eval fixtures, diff across runs)
without re-parsing the markdown table.
