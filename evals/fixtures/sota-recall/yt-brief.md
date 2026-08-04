# Fixture brief — YouTube private-surface toolchain (case `yt`)

> Frozen 2026-08-04. Neutralized reconstruction of a July 2026 phase-1 research brief. Replay against Phase 0 + Phase 1b ONLY (plan + solution-space sweep) — never a full product research run.

## Research question

For the three private surfaces of a personal YouTube account — « Watch Later », liked videos + private/unlisted playlists, subscriptions + watch history — which access paths exist to (1) **enumerate** each surface into a list of video IDs and (2) **hydrate** each public video into a full-text note (title, chapters, transcript)? Browser-cookie paths are excluded by operator decision; OAuth and portability-export paths are acceptable. The operator explicitly wants **existing packaged toolchains surveyed before any custom build** — MCP servers, CLI tools, SaaS — with cost and account-risk per path.

## Flags

`--length standard --profile technical --lang en`

## Known miss this fixture guards against

The original run declared its MCP-server inventory non-exhaustive (3 servers sampled) and its own decorrelated judge REFUSED the universal claim « no MCP server does private-playlist enumeration » — yet the design phase consumed « nothing exists » as fact. The ground-truth item (`ground-truth.json`, case `yt`) is the OAuth-capable MCP server the registry sweep must surface.
