# Tooling categories — closed taxonomy

> The versioned, closed set of tool categories for the `suggest-tooling` skill. Every
> candidate must be classified into one or more of these categories before ranking. The
> category-to-hat mapping drives the relevance score.

## Categories

Exactly 11 categories. Do not add, remove, or rename keys without a coordinated update
to this file, `DEFAULT_CATEGORY_HAT` in `suggest-tooling/scripts/marketplace_rank.py`,
and `suggest-tooling/tooling-hats.json.example` — all three must stay in sync (the T9
test enforces script-vs-example parity at CI time).

| Category key | Description |
|---|---|
| `eval` | Evaluation frameworks, benchmarks, and judge pipelines for LLM outputs |
| `rag` | Retrieval-augmented generation: indexing, chunking, embedding, retrieval |
| `mcp-server` | Model Context Protocol servers exposing tools or resources to Claude Code |
| `prompt-eng` | Prompt engineering utilities, template managers, and context-engineering tools |
| `agent-orchestration` | Multi-agent frameworks, orchestrators, and task-routing systems |
| `scraping` | Web scraping, data extraction, and anti-bot fetcher libraries |
| `observability` | Monitoring, tracing, logging, and alerting for production systems |
| `k8s-security` | Kubernetes security scanning, policy enforcement, and hardening tools |
| `secrets-mgmt` | Secret vaults, rotation, injection, and leak-prevention tooling |
| `ci-cd` | Continuous integration and deployment pipelines, GitOps, and release automation |
| `fr-b2b-ops` | French B2B sales operations: CRM, outreach, lead enrichment, and pipeline tools |

## Category-to-hat mapping

Each category maps to exactly one hat. Hat weights are defined in
`suggest-tooling/tooling-hats.json.example` (user-scope override at
`~/.claude/deep-research/tooling-hats.json`).

| Category key | Hat |
|---|---|
| `eval` | `ai-engineer` |
| `rag` | `ai-engineer` |
| `mcp-server` | `ai-engineer` |
| `prompt-eng` | `ai-engineer` |
| `agent-orchestration` | `ai-engineer` |
| `scraping` | `ai-engineer` |
| `observability` | `platform` |
| `k8s-security` | `devsecops` |
| `secrets-mgmt` | `devsecops` |
| `ci-cd` | `devsecops` |
| `fr-b2b-ops` | `fr-b2b` |

## Extension protocol

Adding a category requires editing three files in the same commit:

1. This file — add the key and description to the table above, and the key-to-hat row
   to the mapping table.
2. `suggest-tooling/scripts/marketplace_rank.py` — add the key to `DEFAULT_CATEGORY_HAT`
   with its hat assignment.
3. `suggest-tooling/tooling-hats.json.example` — add the key to `category_hat`.

The T9 block in `tests/check-marketplace-rank.sh` asserts that the script's
`DEFAULT_CATEGORY_HAT` key set equals the example's `category_hat` key set. A mismatch
fails CI.
