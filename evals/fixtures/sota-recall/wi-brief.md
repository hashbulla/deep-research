# Fixture brief — web interaction toolchain (case `wi`)

> Frozen 2026-08-05. Neutralized reconstruction of an August 2026 hand-run benchmark brief. Replay against Phase 0 + Phase 1b ONLY (plan + solution-space sweep) — never a full product research run.

## Research question

Which toolchains let an agentic CLI (Claude Code) drive the web at full capacity — authenticated portals, multi-step workflows (forms, upload, cart), Cloudflare/WAF-protected reads, and recursive link-following for deep research — while reading as a human user to adversarial fingerprinting and bot-management systems?

## Constraints carried by the brief

- Four capability classes must be benchmarked, not one: custom-build · already-owned-and-paid · open-source · commercial.
- The stack inventory runs before any web call.
- Verdicts are per target class; there is no single winner.

## Why this case exists

The original run declared `open-source` **swept** in its coverage manifest on the strength of prose search alone. No GitHub-native query ever ran. It missed eight repositories totalling roughly 200k stars — including the leading implementation of the very class the run had itself named as strongest for authenticated portals.

The sharpest form of the failure: the diagnosis was right and the inventory was wrong. Naming a class correctly buys nothing if it is then populated with the wrong instrument.

## Recall property under test

A hardened run must surface `Panniantong/Agent-Reach` and `jackwener/OpenCLI` through the `open-source` category, via a GitHub-native topic sweep — not through a vendor comparison blog, and not by name (the brief never names them).

Both are reachable from `topic:` facets derived from the capability classes. Neither is reachable from English prose describing the problem: Agent-Reach's README is Chinese-first, and OpenCLI's category ("turn any website into a CLI", browser-session reuse) is absent from the market-comparison corpus that prose search retrieves.
