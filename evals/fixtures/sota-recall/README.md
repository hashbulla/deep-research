# SOTA-recall regression fixtures

> Two real research briefs whose phase-1 runs missed four ground-truth items — frozen here as the regression eval for the solution-space hardening. A hardened pipeline that does not surface all four items on these briefs has failed, whatever the elegance of its design.

## Provenance

Both briefs are neutralized reconstructions of real July 2026 research runs (YouTube and Instagram source-connector toolchains). Each run produced access-gate verdicts that held — sitting on a solution-space map with holes. The four missed items were recovered only under adversarial challenge, in one short re-probe. Root causes and the hardening they motivated: `references/solution-space.md`.

## Contents

| File | Role |
|---|---|
| `yt-brief.md` | YouTube research question (fixture case `yt`) |
| `ig-brief.md` | Instagram research question (fixture case `ig`) |
| `ground-truth.json` | The four items, each mapped to the sweep mechanism expected to surface it |
| `stack-corpus/` | Synthetic own-stack corpus (public-info only) for the deterministic stack-sweep test |
| `stack-paths.fixture.json` | `stack-paths.json` config pointing at the synthetic corpus |

## The four items and their mechanisms

Each item deliberately tests a DIFFERENT sweep mechanism — a hardening that finds one does not prove the others:

| Item | Case | Expected category | Mechanism under test |
|---|---|---|---|
| `youtube-data-mcp-server` | yt | `mcp-registries` | Named MCP-registry sweep (live) |
| Unipile | ig | `own-stack` | Stack grep BEFORE web (deterministic) |
| HikerAPI | ig | `commercial-vendors` | Vendor enumeration by risk class (live) |
| session-delegation class | ig | `commercial-vendors` | Risk-class taxonomy (deterministic: the class must exist in the sweep plan) |

## Replay protocol

1. **Deterministic part (CI-safe, hermetic):** run `scripts/stack_inventory.py` with `stack-paths.fixture.json` against `stack-corpus/` for the `ig` case — the Unipile fixture note must surface, the decoy must not. Exercised by `tests/check-solution-space.sh`.
2. **Live part (operator machine, manual):** feed each brief to the hardened Phase 0 + Phase 1b ONLY (plan + solution-space sweep — never a full product re-research). Check `research-solution-space.json` and the draft benchmark rows against `ground-truth.json` `accept_when` criteria. Record evidence in the tracking ticket.

## Perishability

SOTA ground truth decays. Every item carries `validated` (date the item was last confirmed to exist and behave as described). When replaying more than ~6 months after `frozen`, re-validate items before treating a miss as a pipeline failure — a renamed repo or a dead vendor is a fixture bug, not a recall bug.
