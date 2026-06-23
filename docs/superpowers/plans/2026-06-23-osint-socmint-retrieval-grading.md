# OSINT/SOCMINT Retrieval + Grading Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an optional stealth-retrieval escalation plus native Admiralty grading of social/protected sources to the deep-research skill, without breaking its autonomy, supply-chain, or grounding guarantees.

**Architecture:** A 3-rung retrieval ladder (Tavily search → `tavily_extract` advanced → isolated Scrapling subagent) feeds social/protected URLs into the existing pipeline. Those sources grade on the NATO Admiralty code by account identity (no separate lane). New deterministic gates in `verify_gates.py` enforce the account-reliability→tier mapping, a per-run stealth cap, `retrieval_status` validity, and an anti-amplification independence check. All retrieval is via MCP tool calls; the `scripts/` helpers stay stdlib-only / zero-network.

**Tech Stack:** Python 3.11 stdlib (`scripts/verify_gates.py`), JSON Schema draft-07 (`tests/schema/`), bash test harness (`tests/*.sh`), markdown skill surface (`SKILL.md`, `references/`), `mcp__scrapling__stealthy_fetch` (runtime only, optional), `Agent` subagent dispatch.

**Source spec:** `docs/superpowers/specs/2026-06-23-osint-socmint-retrieval-grading-design.md` (AI-183).

## Global Constraints

- **Scripts are stdlib-only, zero-network, zero-LLM** — invariant I4a (`.claude/CLAUDE.md`). `verify_gates.py` must never open a socket. Verified by `python3 -m py_compile` + review.
- **Skill surface (`SKILL.md`, `references/`) is markdown-only** — no embedded executable code.
- **No emoji** in `SKILL.md`, `references/*`, or artifacts. README badges are the only exception.
- **`references/methodology.md` §9 is the single source of phase vocabulary** — never rename/reorder phases (I3).
- **Tier-registry / rubric changes land in `references/methodology.md` §6 first**, then propagate to README + SKILL.md in the **same commit** (I5).
- **No report re-hash needed** — the account-reliability rubric is skill policy with no `[R§n]` back-ref, so `deep-research-report.md` is untouched and the `Hash at generation time:` line in SKILL.md stays valid (I1). Confirm in Task 11.
- **Deterministic rules over hedging** — thresholds are numbers (`--max-stealth 12`, amplification window 72h).
- **Absolute paths in scripts/tool-routing; relative paths in markdown cross-references.**
- **GDPR default = data-minimized** — persist only cited-span snapshots; full captures local-only, never committed.

## File Structure

| Path | Action | Responsibility |
|---|---|---|
| `tests/schema/research-sources.schema.json` | Modify | Add `retrieval_status`, `account_provenance`, `scrapling_stealth` enum |
| `scripts/verify_gates.py` | Modify | 4 new deterministic gates + `scrapling_stealth` score-less registration |
| `tests/fixtures/osint/*.json` | Create | Good SOCMINT pair + amplification-violation + cap-violation fixtures |
| `tests/check-osint-gates.sh` | Create | Drives `verify_gates.py` over the fixtures, asserts PASS/FAIL |
| `references/methodology.md` | Modify | §6 account-reliability sub-rubric + tier map + B13 + robots doctrine |
| `references/anti-patterns.md` | Modify | B5 reframe note + new B13 |
| `references/report-structure.md` | Modify | Field docs for `retrieval_status` + `account_provenance` |
| `references/osint-retrieval.md` | Create | Escalation ladder + isolation-subagent contract + GDPR knob |
| `SKILL.md` | Modify | `allowed-tools` delta, ladder workflow, subagent dispatch, `--max-stealth`, Phase-0 probe |
| `README.md` | Modify | Tier-table note + capability mention |
| `CHANGELOG.md` | Modify | Release entry |
| `gotchas-log.md` | Modify | Stealth-cap + GDPR maintenance traps |
| `.claude/CLAUDE.md` | Modify | Architecture-map rows for the new files |
| `.github/workflows/validate.yml` | Modify | Run `check-osint-gates.sh` |

---

### Task 1: Schema — new fields and enum value

**Files:**
- Modify: `tests/schema/research-sources.schema.json`
- Test: `tests/check-schema.sh` (existing ajv driver) + a temp fixture

**Interfaces:**
- Produces: schema accepting `retrieval_tool: "scrapling_stealth"`, an optional `retrieval_status` enum, and an optional `account_provenance` object. Consumed by Tasks 2–6 and the emitter.

- [ ] **Step 1: Write the failing test** — create `tests/fixtures/osint/socmint-source.json` (a one-element array) that the *current* schema rejects (it uses the new fields):

```json
[
  {
    "id": "S001",
    "url": "https://www.linkedin.com/posts/eu-ai-office_gpai-update-activity-123",
    "url_canonical": "linkedin.com/posts/eu-ai-office_gpai-update-activity-123",
    "url_punycode": "linkedin.com/posts/eu-ai-office_gpai-update-activity-123",
    "title": "EU AI Office post on GPAI timeline",
    "publisher": "LinkedIn",
    "author": "EU AI Office",
    "published_date": "2026-03-01",
    "accessed_date": "2026-06-23",
    "domain_tier": 2,
    "admiralty_reliability": "B",
    "tavily_score": null,
    "retrieval_tool": "scrapling_stealth",
    "retrieval_status": "robots_overridden",
    "account_provenance": {
      "platform": "linkedin",
      "handle": "eu-ai-office",
      "verified": true,
      "account_reliability_basis": "verified institutional account",
      "post_timestamp": "2026-03-01T09:12:00Z"
    },
    "retrieval_query": "EU AI Office GPAI timeline",
    "sub_questions": ["sq1"],
    "primary_source": false,
    "notes": "Surfaced via newsletter-signal corpus 2026-03-01; stealth-retrieved (LinkedIn bot-walled)."
  }
]
```

- [ ] **Step 2: Run schema validation to verify it fails**

Run: `npx --yes ajv-cli@5 validate -s tests/schema/research-sources.schema.json -d tests/fixtures/osint/socmint-source.json`
Expected: FAIL — `additionalProperties` rejects `retrieval_status` / `account_provenance`, and the `retrieval_tool` enum rejects `scrapling_stealth`.

- [ ] **Step 3: Add `scrapling_stealth` to the `retrieval_tool` enum**

In `tests/schema/research-sources.schema.json`, append `"scrapling_stealth"` to the `retrieval_tool.enum` array (after `"WebSearch"`).

- [ ] **Step 4: Add the `retrieval_status` property** (sibling of `retrieval_tool` in `properties`):

```json
"retrieval_status": {
  "type": "string",
  "enum": ["direct", "stealth", "robots_overridden", "blocked"],
  "description": "How the content was obtained relative to access obstacles. Audit metadata only — never affects the grade."
},
```

- [ ] **Step 5: Add the `account_provenance` property** (sibling, optional — not added to `required`):

```json
"account_provenance": {
  "type": "object",
  "additionalProperties": false,
  "description": "Account identity for account-based sources (social platforms). Drives account-derived reliability per methodology §6.",
  "required": ["platform", "handle", "verified"],
  "properties": {
    "platform": { "type": "string" },
    "handle": { "type": ["string", "null"] },
    "verified": { "type": "boolean" },
    "account_reliability_basis": { "type": "string" },
    "post_timestamp": { "type": ["string", "null"] }
  }
},
```

- [ ] **Step 6: Run validation to verify it passes**

Run: `npx --yes ajv-cli@5 validate -s tests/schema/research-sources.schema.json -d tests/fixtures/osint/socmint-source.json`
Expected: PASS (`valid`).

- [ ] **Step 7: Commit**

```bash
git add tests/schema/research-sources.schema.json tests/fixtures/osint/socmint-source.json
git commit -m "feat(schema): add retrieval_status, account_provenance, scrapling_stealth (AI-183)"
```

---

### Task 2: `verify_gates.py` — register `scrapling_stealth` + account-tier mapping check

**Files:**
- Modify: `scripts/verify_gates.py` (`SCORELESS_TOOLS` near line 49; new constant; the source loop near lines 109–136)
- Test: `tests/fixtures/osint/` + manual run

**Interfaces:**
- Produces: a `REL_TO_TIER` constant and a per-source check that any record carrying `account_provenance` has `domain_tier == REL_TO_TIER[admiralty_reliability]`. Consumed by Task 6's harness.

- [ ] **Step 1: Write the failing fixture** — create `tests/fixtures/osint/bad-tier-map.json` by copying `socmint-source.json` and changing `"domain_tier": 2` to `"domain_tier": 1` (reliability B must map to tier 2, not 1). Add a minimal matching evidence file `tests/fixtures/osint/bad-tier-map-evidence.json`:

```json
[
  {
    "claim_id": "C001",
    "claim_text": "The AI Office reiterated the GPAI timeline.",
    "section": "1. GPAI timeline",
    "supporting_source_ids": ["S001"],
    "contradicting_source_ids": [],
    "admiralty_credibility": 3,
    "label": "POSSIBLY TRUE",
    "corroboration_count": 1,
    "independent_tier12_count": 1,
    "primary_source_present": false,
    "notes": ""
  }
]
```

- [ ] **Step 2: Run to verify the violation is NOT yet caught**

Run: `python3 scripts/verify_gates.py check-artifacts --sources tests/fixtures/osint/bad-tier-map.json --evidence tests/fixtures/osint/bad-tier-map-evidence.json --length short`
Expected (pre-implementation): the tier-map error is absent from `violations` (the gate doesn't exist yet). Note: `source_count_floor` will FAIL because the fixture has 1 source — that is unrelated; we assert specifically on the *absence* of a `tier map` violation string.

- [ ] **Step 3: Register the score-less tool.** Add `"scrapling_stealth"` to the `SCORELESS_TOOLS` set (line 49–57) so a null `tavily_score` on a stealth record does not trip the existing "null tavily_score on score-bearing tool" check (line 132).

- [ ] **Step 4: Add the mapping constant** after `SCORELESS_TOOLS`:

```python
# Account-derived reliability → domain_tier (methodology §6, Safeguard 1).
# Applies ONLY to account-based sources (those carrying account_provenance);
# domain-graded sources keep their registry tier.
REL_TO_TIER = {"A": 2, "B": 2, "C": 3, "D": 4, "E": 4, "F": 4}
```

- [ ] **Step 5: Add the check** inside the `for src in sources:` loop (after the null-score block, ~line 136):

```python
        if src.get("account_provenance"):
            rel = src.get("admiralty_reliability")
            expected_tier = REL_TO_TIER.get(rel)
            if expected_tier is not None and src.get("domain_tier") != expected_tier:
                violations.append(
                    f"{sid}: account source reliability {rel!r} must map to "
                    f"domain_tier {expected_tier}, found {src.get('domain_tier')}"
                )
```

- [ ] **Step 6: Run to verify the violation now fires**

Run: `python3 scripts/verify_gates.py check-artifacts --sources tests/fixtures/osint/bad-tier-map.json --evidence tests/fixtures/osint/bad-tier-map-evidence.json --length short`
Expected: `violations` now contains `"S001: account source reliability 'B' must map to domain_tier 2, found 1"`.

- [ ] **Step 7: Verify the good fixture is clean of tier-map violations** — build `tests/fixtures/osint/socmint-evidence.json` (the well-formed counterpart):

```json
[
  {
    "claim_id": "C001",
    "claim_text": "The AI Office reiterated the GPAI timeline.",
    "section": "Needs Verification",
    "supporting_source_ids": ["S001"],
    "contradicting_source_ids": [],
    "admiralty_credibility": 3,
    "label": "POSSIBLY TRUE",
    "corroboration_count": 1,
    "independent_tier12_count": 1,
    "primary_source_present": false,
    "notes": ""
  }
]
```

Wait — credibility 3 must NOT be in "Needs Verification" (only ≥4 lives there, `verify_gates.py:188`). Set `"section": "1. GPAI timeline"` instead. Run the good pair:

Run: `python3 scripts/verify_gates.py check-artifacts --sources tests/fixtures/osint/socmint-source.json --evidence tests/fixtures/osint/socmint-evidence.json --length short`
Expected: no `tier map` violation string (source_count_floor still FAILs on count — expected for a 1-source fixture; Task 6 uses `--length short` with padded fixtures where needed).

- [ ] **Step 8: Compile + commit**

```bash
python3 -m py_compile scripts/verify_gates.py
git add scripts/verify_gates.py tests/fixtures/osint/
git commit -m "feat(gates): enforce account-reliability->domain_tier mapping (AI-183)"
```

---

### Task 3: `verify_gates.py` — per-run stealth cap

**Files:**
- Modify: `scripts/verify_gates.py` (new `--max-stealth` arg ~line 322; count + check in `check_artifacts`)
- Test: `tests/fixtures/osint/cap-violation.json`

**Interfaces:**
- Consumes: `args.max_stealth` (int, default 12).
- Produces: a violation when `count(retrieval_tool == "scrapling_stealth") > max_stealth`.

- [ ] **Step 1: Write the failing fixture** — `tests/fixtures/osint/cap-violation.json`: an array of 3 records each with `"retrieval_tool": "scrapling_stealth"`, valid `account_provenance`, distinct ids `S001`–`S003`, reliability `B`/tier `2`. (Copy `socmint-source.json` three times, bump ids/handles.)

- [ ] **Step 2: Add the CLI arg** to the `check-artifacts` subparser (near line 322):

```python
    p_art.add_argument("--max-stealth", type=int, default=12,
                       help="per-run ceiling on scrapling_stealth retrievals")
```

- [ ] **Step 3: Run to confirm no cap violation yet**

Run: `python3 scripts/verify_gates.py check-artifacts --sources tests/fixtures/osint/cap-violation.json --evidence tests/fixtures/osint/socmint-evidence.json --length short --max-stealth 2`
Expected: no `stealth cap` violation (gate absent).

- [ ] **Step 4: Add the cap check** in `check_artifacts`, after the source loop (before the gates dict, ~line 209):

```python
    stealth_n = sum(1 for s in sources if s.get("retrieval_tool") == "scrapling_stealth")
    if stealth_n > args.max_stealth:
        violations.append(
            f"stealth cap exceeded: {stealth_n} scrapling_stealth retrievals > "
            f"--max-stealth {args.max_stealth}"
        )
```

- [ ] **Step 5: Run to verify the violation fires**

Run: `python3 scripts/verify_gates.py check-artifacts --sources tests/fixtures/osint/cap-violation.json --evidence tests/fixtures/osint/socmint-evidence.json --length short --max-stealth 2`
Expected: `violations` contains `"stealth cap exceeded: 3 scrapling_stealth retrievals > --max-stealth 2"`.

- [ ] **Step 6: Compile + commit**

```bash
python3 -m py_compile scripts/verify_gates.py
git add scripts/verify_gates.py tests/fixtures/osint/cap-violation.json
git commit -m "feat(gates): enforce per-run stealth-fetch cap (AI-183)"
```

---

### Task 4: `verify_gates.py` — `retrieval_status` validity for stealth records

**Files:**
- Modify: `scripts/verify_gates.py` (source loop)
- Test: `tests/fixtures/osint/bad-status.json`

**Interfaces:**
- Produces: a violation when a `scrapling_stealth` record's `retrieval_status` is absent or not in `{stealth, robots_overridden}`.

- [ ] **Step 1: Write the failing fixture** — `tests/fixtures/osint/bad-status.json`: copy `socmint-source.json`, set `"retrieval_status": "direct"` (invalid for a stealth retrieval).

- [ ] **Step 2: Run to confirm not yet caught**

Run: `python3 scripts/verify_gates.py check-artifacts --sources tests/fixtures/osint/bad-status.json --evidence tests/fixtures/osint/socmint-evidence.json --length short`
Expected: no `retrieval_status` violation.

- [ ] **Step 3: Add the check** in the source loop (after the account-tier block from Task 2):

```python
        if src.get("retrieval_tool") == "scrapling_stealth":
            status = src.get("retrieval_status")
            if status not in {"stealth", "robots_overridden"}:
                violations.append(
                    f"{sid}: scrapling_stealth record needs retrieval_status in "
                    f"{{stealth, robots_overridden}}, found {status!r}"
                )
```

- [ ] **Step 4: Run to verify the violation fires**

Run: `python3 scripts/verify_gates.py check-artifacts --sources tests/fixtures/osint/bad-status.json --evidence tests/fixtures/osint/socmint-evidence.json --length short`
Expected: `violations` contains `"S001: scrapling_stealth record needs retrieval_status in {stealth, robots_overridden}, found 'direct'"`.

- [ ] **Step 5: Compile + commit**

```bash
python3 -m py_compile scripts/verify_gates.py
git add scripts/verify_gates.py tests/fixtures/osint/bad-status.json
git commit -m "feat(gates): validate retrieval_status on stealth records (AI-183)"
```

---

### Task 5: `verify_gates.py` — anti-amplification independence check (B13)

**Files:**
- Modify: `scripts/verify_gates.py` (new `parse_dt` helper; new arg `--amplification-window`; build `srcmap`; per-claim check)
- Test: `tests/fixtures/osint/amplification-*.json`

**Interfaces:**
- Consumes: `args.amplification_window` (hours, default 72), each source's `account_provenance.post_timestamp` and `handle`.
- Produces: a violation when a claim has ≥2 social supporters with distinct handles whose `post_timestamp`s fall within the window, unless the claim's `notes` contains the literal marker `independence-verified`.

- [ ] **Step 1: Write the failing fixtures.** `tests/fixtures/osint/amplification-sources.json`: 2 stealth social sources `S001`/`S002`, reliability `C`/tier `3`, distinct handles `acct-a`/`acct-b`, `post_timestamp` 6 hours apart (`2026-03-01T09:00:00Z`, `2026-03-01T15:00:00Z`). `tests/fixtures/osint/amplification-evidence.json`:

```json
[
  {
    "claim_id": "C001",
    "claim_text": "A regulatory change is imminent (per two social posts).",
    "section": "1. Signals",
    "supporting_source_ids": ["S001", "S002"],
    "contradicting_source_ids": [],
    "admiralty_credibility": 3,
    "label": "POSSIBLY TRUE",
    "corroboration_count": 2,
    "independent_tier12_count": 0,
    "primary_source_present": false,
    "notes": ""
  }
]
```

- [ ] **Step 2: Run to confirm not yet caught**

Run: `python3 scripts/verify_gates.py check-artifacts --sources tests/fixtures/osint/amplification-sources.json --evidence tests/fixtures/osint/amplification-evidence.json --length short`
Expected: no `amplification` violation.

- [ ] **Step 3: Add the datetime helper** after `parse_iso` (~line 91):

```python
def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
```

Add `datetime` to the existing `from datetime import ...` line (line 36): `from datetime import date, datetime, timedelta`.

- [ ] **Step 4: Build a `srcmap`.** In `check_artifacts`, alongside the `tier` dict (line 109), add `srcmap: dict[str, dict] = {}` and inside the loop set `srcmap[sid] = src`.

- [ ] **Step 5: Add the CLI arg** (near `--max-stealth`):

```python
    p_art.add_argument("--amplification-window", type=int, default=72,
                       help="hours within which clustered social posts are amplification-suspect")
```

- [ ] **Step 6: Add the per-claim check** inside the `for claim in evidence:` loop, after the Tier-4 / cascade block (~line 189):

```python
        social_sup = [r for r in sup
                      if r in srcmap and srcmap[r].get("account_provenance")]
        if len(social_sup) >= 2:
            window = timedelta(hours=args.amplification_window)
            stamped = [(r, parse_dt(srcmap[r]["account_provenance"].get("post_timestamp")))
                       for r in social_sup]
            stamped = [(r, t) for r, t in stamped if t]
            handles = {srcmap[r]["account_provenance"].get("handle") for r in social_sup}
            clustered = any(
                abs(t1 - t2) <= window
                for i, (_, t1) in enumerate(stamped)
                for _, t2 in stamped[i + 1:]
            )
            note = (claim.get("notes") or "").lower()
            if clustered and len(handles) >= 2 and "independence-verified" not in note:
                violations.append(
                    f"{cid}: {len(social_sup)} social sources corroborate within "
                    f"{args.amplification_window}h without an 'independence-verified' "
                    f"note (B13 amplification masquerade)"
                )
```

- [ ] **Step 7: Run to verify the violation fires**

Run: `python3 scripts/verify_gates.py check-artifacts --sources tests/fixtures/osint/amplification-sources.json --evidence tests/fixtures/osint/amplification-evidence.json --length short`
Expected: `violations` contains the B13 amplification message.

- [ ] **Step 8: Add the passing counterpart.** Create `tests/fixtures/osint/amplification-cleared-evidence.json` identical to Step 1 but with `"notes": "independence-verified: distinct authors, no shared origin, posted independently during the EUR-Lex publication event."`. Run:

Run: `python3 scripts/verify_gates.py check-artifacts --sources tests/fixtures/osint/amplification-sources.json --evidence tests/fixtures/osint/amplification-cleared-evidence.json --length short`
Expected: no B13 violation (the marker clears it).

- [ ] **Step 9: Compile + commit**

```bash
python3 -m py_compile scripts/verify_gates.py
git add scripts/verify_gates.py tests/fixtures/osint/amplification-*.json
git commit -m "feat(gates): anti-amplification independence check B13 (AI-183)"
```

---

### Task 6: New test harness `check-osint-gates.sh` + CI wiring

**Files:**
- Create: `tests/check-osint-gates.sh`
- Modify: `.github/workflows/validate.yml`
- Test: the script itself

**Interfaces:**
- Consumes: all `tests/fixtures/osint/*.json` from Tasks 1–5.
- Produces: exit 0 only when every "bad" fixture FAILs with the expected violation substring and every "good" fixture is clean of OSINT violations.

- [ ] **Step 1: Write the harness** `tests/check-osint-gates.sh`:

```bash
#!/usr/bin/env bash
# Drives verify_gates.py over the OSINT/SOCMINT fixtures and asserts each
# gate fires (or stays silent) as designed. CI-only — never invoked by the
# skill at runtime.
set -euo pipefail
cd "$(dirname "$0")/.."
F=tests/fixtures/osint
G="python3 scripts/verify_gates.py check-artifacts --length short"
fail=0

assert_contains() { # <label> <output> <needle>
  if ! grep -qF "$3" <<<"$2"; then echo "MISS [$1]: expected '$3'"; fail=1; fi
}
assert_absent() {
  if grep -qF "$3" <<<"$2"; then echo "LEAK [$1]: unexpected '$3'"; fail=1; fi
}

out=$($G --sources $F/bad-tier-map.json --evidence $F/bad-tier-map-evidence.json || true)
assert_contains tier-map "$out" "must map to domain_tier 2, found 1"

out=$($G --sources $F/cap-violation.json --evidence $F/socmint-evidence.json --max-stealth 2 || true)
assert_contains cap "$out" "stealth cap exceeded: 3"

out=$($G --sources $F/bad-status.json --evidence $F/socmint-evidence.json || true)
assert_contains status "$out" "needs retrieval_status in {stealth, robots_overridden}"

out=$($G --sources $F/amplification-sources.json --evidence $F/amplification-evidence.json || true)
assert_contains amp "$out" "B13 amplification masquerade"

out=$($G --sources $F/amplification-sources.json --evidence $F/amplification-cleared-evidence.json || true)
assert_absent amp-cleared "$out" "B13 amplification masquerade"

if [ "$fail" -eq 0 ]; then echo "check-osint-gates: PASS"; else echo "check-osint-gates: FAIL"; exit 1; fi
```

- [ ] **Step 2: Make executable + run**

Run: `chmod +x tests/check-osint-gates.sh && bash tests/check-osint-gates.sh`
Expected: `check-osint-gates: PASS`.

- [ ] **Step 3: Wire into CI.** In `.github/workflows/validate.yml`, add a step after the existing check invocations:

```yaml
      - name: OSINT/SOCMINT gates
        run: bash tests/check-osint-gates.sh
```

- [ ] **Step 4: Commit**

```bash
git add tests/check-osint-gates.sh .github/workflows/validate.yml
git commit -m "test(osint): harness + CI wiring for OSINT/SOCMINT gates (AI-183)"
```

---

### Task 7: methodology §6 — account-reliability rubric + B13 + robots doctrine

**Files:**
- Modify: `references/methodology.md` (§6 tier registry section)
- Test: `tests/check-cross-references.sh`

**Interfaces:**
- Produces: the authoritative account-reliability sub-rubric (A/B→2, C→3, D/E/F→4) that Task 2's `REL_TO_TIER` mirrors, plus the B13 and robots-override doctrine. Policy-only — no `[R§n]` back-ref.

- [ ] **Step 1: Add the sub-rubric** at the end of §6 (verbatim — this is the single source of truth Task 2 derives from):

```markdown
### Account-derived reliability (OSINT/SOCMINT sources)

When a source is account-based (social platform; carries `account_provenance`),
the domain-tier registry cannot grade it — `twitter.com` as a *domain* says
nothing. Reliability A–F is derived from account identity, and each band maps
to a derived `domain_tier` so the existing tier-dependent rules keep working:

| Reliability | Account basis | Derived `domain_tier` |
|---|---|---|
| A / B | Verified institutional / official account | 2 |
| C | Established, real-identity named expert, unverified | 3 |
| D | Pseudonymous but consistent track record | 4 |
| E | Anonymous / burner / low-history, or injection-suspect | 4 |
| F | Impersonation- or deception-suspect | 4 |

Tier 1 stays reserved for canonical domains; a verified account caps at tier 2.
The mapping re-encodes B5: an anonymous social source (tier 4) is never
`primary_source`; a verified institutional account (tier 2) may be. Retrieval
method (stealth vs Tavily) never affects the grade — it is recorded only in
`retrieval_status`.
```

- [ ] **Step 2: Add the amplification + robots doctrine** (same section):

```markdown
**Anti-amplification (B13).** Before N social sources count as N independent
corroborations, confirm distinct authorship and no shared origin. Near-identical
posts clustered in time across accounts are coordinated amplification and count
as one source. `verify_gates.py` flags clustered social corroboration (≥2
distinct handles within the amplification window); the grader records the
independence determination with an `independence-verified` note or the gate fails.

**robots / stealth doctrine.** Stealth retrieval may override `robots.txt`
(logged as `retrieval_status: robots_overridden`) and may target litigious
platforms, but never credentialed content. It is bounded by `--max-stealth`
(default 12) per run to stay research-scale. SOCMINT on named individuals is
personal-data processing under GDPR; persistence defaults to cited-span
snapshots only (see `references/osint-retrieval.md`).
```

- [ ] **Step 2b: Verify cross-references tolerate policy-only content**

Run: `bash tests/check-cross-references.sh`
Expected: PASS. (The check validates that existing `[R§n]` refs resolve; it does not require new subsections to carry one. If it errors on the new section, the spec's Maintainer-integrity assumption is wrong — STOP and report.)

- [ ] **Step 3: Commit**

```bash
git add references/methodology.md
git commit -m "docs(methodology): account-reliability rubric + B13 + robots doctrine (AI-183)"
```

---

### Task 8: anti-patterns.md — reframe B5, add B13

**Files:**
- Modify: `references/anti-patterns.md`
- Test: `tests/check-cross-references.sh`

- [ ] **Step 1: Append a reframe note to B5** (after `anti-patterns.md:44`):

```markdown
**Reframe (AI-183):** "Tier 4 = never cited" now means *ungraded or
anonymous-low-reliability* social sources. An account graded reliability A–C via
the §6 account-reliability rubric (mapping to tier ≤ 3) is citable like any
other source; the deterministic Tier-4 support check (`verify_gates.py`) still
blocks tier-4 (anonymous/burner) social sources from `supporting_source_ids`.
```

- [ ] **Step 2: Add B13** after B12 (before section C):

```markdown
### B13. Amplification masquerade
Coordinated inauthentic social corroboration is not independent corroboration.
N near-identical posts across accounts clustered in time count as **one** source
(extends B10 to account-based sources). `verify_gates.py` flags clusters; the
grader must record an `independence-verified` determination or the claim's
corroboration is rejected. Cheap-to-fabricate social consensus never lifts a
claim's credibility on volume alone.
```

- [ ] **Step 3: Verify + commit**

Run: `bash tests/check-cross-references.sh`
Expected: PASS.

```bash
git add references/anti-patterns.md
git commit -m "docs(anti-patterns): reframe B5, add B13 amplification (AI-183)"
```

---

### Task 9: report-structure.md — document the new fields

**Files:**
- Modify: `references/report-structure.md` (§3 required/optional field list, ~lines 96–103)
- Test: `tests/check-cross-references.sh`

- [ ] **Step 1: Add field docs** after the `notes` bullet (`report-structure.md:103`):

```markdown
- `retrieval_status` — optional enum `direct | stealth | robots_overridden | blocked`. **Audit metadata only — never affects the grade.** `stealth` / `robots_overridden` records carry `retrieval_tool: "scrapling_stealth"` and `tavily_score: null`; `blocked` marks a recall gap (a relevant URL no rung could retrieve), documented in `notes` and the Methodology note.
- `account_provenance` — optional object for account-based sources: `{platform, handle, verified, account_reliability_basis, post_timestamp}`. Drives account-derived reliability (methodology §6). `domain_tier` for such records is the rubric-derived tier, not a registry tier.
```

- [ ] **Step 2: Verify + commit**

Run: `bash tests/check-cross-references.sh`
Expected: PASS.

```bash
git add references/report-structure.md
git commit -m "docs(report-structure): document retrieval_status + account_provenance (AI-183)"
```

---

### Task 10: references/osint-retrieval.md — the capability reference

**Files:**
- Create: `references/osint-retrieval.md`
- Test: `tests/check-cross-references.sh` (after SKILL.md links it in Task 11)

**Interfaces:**
- Produces: the runtime contract for the escalation ladder, the isolation-subagent payload, the GDPR knob, and optional-source degradation. Linked from SKILL.md (Task 11) and `.claude/CLAUDE.md` (Task 11).

- [ ] **Step 1: Write the file** (markdown-only; mirrors the spec's Architecture + GDPR sections — condensed):

```markdown
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
sanitized structured data: `{url, fetched, text, candidate_quotes,
account_provenance, snapshot_sha256, robots_state, injection_suspect}`. Raw DOM
never crosses back. `injection_suspect: true` forces A6 handling: reliability E,
flagged in `notes`.

## Grading (a source is a source)
Account-based sources grade on Admiralty by account identity (methodology §6
sub-rubric). Retrieval method never affects the grade. Two safeguards:
account-derived reliability, and the B13 anti-amplification check. Ephemeral
sources persist a cited-span snapshot so the citation stays verifiable.

## GDPR posture (owner's call; default = data-minimized)
SOCMINT on named individuals is personal-data processing. Default: persist only
the cited-span snapshot into evidence anchors; keep full captures local-only,
never committed. The lawful-basis (legitimate-interest) determination is the
owner's to record.
```

- [ ] **Step 2: Commit** (cross-ref check deferred to Task 11, which adds the inbound link)

```bash
git add references/osint-retrieval.md
git commit -m "docs(osint): retrieval ladder + isolation-subagent reference (AI-183)"
```

---

### Task 11: SKILL.md wiring + README/CHANGELOG/gotchas/CLAUDE.md propagation

**Files:**
- Modify: `SKILL.md` (frontmatter `allowed-tools` line 4; Phase 1/4 workflow; flags)
- Modify: `README.md`, `CHANGELOG.md`, `gotchas-log.md`, `.claude/CLAUDE.md`
- Test: full local check battery

**Interfaces:**
- Consumes: everything from Tasks 1–10. Produces the user-facing surface + the same-commit propagation required by I3/I5.

- [ ] **Step 1: Extend `allowed-tools`** (SKILL.md:4) — append the scrapling stealth tools to the existing list:

```
… mcp__context7__resolve-library-id, mcp__context7__query-docs, mcp__scrapling__stealthy_fetch, mcp__scrapling__open_session, mcp__scrapling__close_session
```

- [ ] **Step 2: Add the escalation + flag** to the Phase 1/4 workflow prose (the conditional-source area near the academic/newsletter steps). State: the 3-rung ladder, the isolation-subagent dispatch, the `--max-stealth N` flag (default 12), the Phase-0 availability probe (scrapling MCP present? else skip + record), and the `research-plan.md` declaration. Link `references/osint-retrieval.md` for the contract.

- [ ] **Step 3: Verify provenance is untouched** (no report edit → hash still valid):

Run: `bash tests/check-provenance.sh`
Expected: PASS (proves the no-re-hash assumption).

- [ ] **Step 4: Propagate** (same commit, I5): add a tier-table note in `README.md` (account-graded social sources are citable; stealth retrieval is optional + capped); a `CHANGELOG.md` entry (AI-183 capability summary); a `gotchas-log.md` row (stealth-cap default + GDPR persistence default + "scrapling MCP optional, degrades"); and `.claude/CLAUDE.md` architecture-map rows for `references/osint-retrieval.md`, `tests/check-osint-gates.sh`, and the new `verify_gates.py` gates.

- [ ] **Step 5: Run the full local battery**

```bash
bash tests/check-cross-references.sh
bash tests/check-provenance.sh
bash tests/check-schema.sh tests/fixtures/research-sources.json tests/fixtures/research-evidence.json
bash tests/check-example-invariants.sh
bash tests/check-osint-gates.sh
python3 -m py_compile scripts/verify_gates.py
```

Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add SKILL.md README.md CHANGELOG.md gotchas-log.md .claude/CLAUDE.md
git commit -m "feat(skill): wire OSINT/SOCMINT ladder + propagate docs (AI-183)"
```

---

### Task 12: Eval-posture confirmation + final battery

**Files:**
- Verify only: `evals/` (no new loading probe needed per spec Non-goals)

- [ ] **Step 1: Confirm no new activation probe is required.** The capability is an internal Phase-1/4 branch (no new trigger), so loading evals are unchanged — same reasoning as the newsletter source. Note this explicitly in the final commit message; do NOT add probes.

- [ ] **Step 2: Re-run the full battery** (Task 11 Step 5 commands) and confirm green.

- [ ] **Step 3: Final commit (if any pending) + push the branch**

```bash
git push -u origin feat/osint-socmint-retrieval
```

---

## Self-Review

**Spec coverage:** escalation ladder (T10/T11) · isolation subagent (T10) · a-source-is-a-source grading + account-tier mapping (T2/T7) · two safeguards: account reliability (T2/T7) + amplification B13 (T5/T8) · schema deltas retrieval_status/account_provenance/scrapling_stealth (T1) · stealth cap (T3) · pipeline placement + Phase-0 probe (T11) · allowed-tools + I4a (T11) · GDPR knob (T10) · B5 reframe (T8) · eval/verify (T6/T12) · maintainer-integrity no-re-hash (T7 Step 2b, T11 Step 3). All spec sections map to a task.

**Placeholder scan:** every code/test step shows real code or an exact command + expected output. The one self-correction (Task 2 Step 7, credibility-3-not-in-Needs-Verification) is intentional and corrected inline.

**Type consistency:** `REL_TO_TIER` (T2) mirrors the §6 table (T7) exactly. `scrapling_stealth` is the single spelling across schema (T1), `SCORELESS_TOOLS` (T2), cap (T3), status (T4). `independence-verified` marker identical in T5 (check), T7/T8 (doctrine). `--max-stealth`/`--amplification-window` arg names consistent T3/T5/T6.
