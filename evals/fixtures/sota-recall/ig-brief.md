# Fixture brief — Instagram ingestion toolchain (case `ig`)

> Frozen 2026-08-04. Neutralized reconstruction of a July 2026 phase-1 research brief. Replay against Phase 0 + Phase 1b ONLY (plan + solution-space sweep) — never a full product research run.

## Research question

Which packaged toolchains exist to wire Instagram content into an agentic CLI (Claude Code) and ingest, as full-text corpus notes (full caption + OCR of carousel slides + on-screen reel text):

- **Surface A** — the operator's own « Saved » collections (their data);
- **Surface B** — posts received or shared in the operator's DMs (their data);
- **Surface C** — content from followed third-party accounts (third-party content, separate gate).

Packaged solutions first — MCP servers, skills, extensions, SaaS APIs (managed scraping, unified-messaging, session-delegation vendors) — custom build last. The regulatory price of each path (platform ToS, GDPR) is part of the verdict.

## Flags

`--length exhaustive --profile technical --since 2024-09-01 --lang en`

## Known misses this fixture guards against

The original run had the right access-gate taxonomy but a holey market map (`ground-truth.json`, case `ig`): a **unified-messaging bridge already present and paid in the operator's own stack** covering Instagram DMs (own-stack sweep must surface it); a managed-scraping vendor ~3× cheaper than the one priced in the report (vendor enumeration must surface it); and the **session-delegation vendor class** never taxonomized (the risk-class enumeration must name it). The queries that missed them were phrased in problem vocabulary (« Instagram API/scraper/MCP ») instead of capability-class vocabulary (« unified messaging API », « social inbox », « session delegation »).
