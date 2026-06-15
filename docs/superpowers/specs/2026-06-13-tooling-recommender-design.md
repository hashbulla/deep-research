# Design: tooling recommender for deep-research (skill/plugin/MCP discovery)

> A sibling skill `suggest-tooling` that consumes a finished `/deep-research` run and proposes work-relevant Claude Code skills, plugins, and MCP servers — ranked by relevance and trust-graded for supply-chain safety, never auto-installed. Closes Linear AI-30 and the AI-40 marketplace remainder.

**Status:** awaiting user approval · **Author:** maintainer session 2026-06-13 · **Grounded by:** `docs/superpowers/specs/research/tooling-discovery-2026/` (dogfood `/deep-research` run, attached design input).

## 1. Problem & scope-conflict resolution

When a `/deep-research` run touches a topic relevant to the maintainer's work (AI Engineering → DevSecOps → Platform → FR B2B), surface the skills / plugins / MCP servers that would help act on it. Example: researching "RAG eval" → propose an eval skill / MCP / plugin.

This collides with a locked non-negotiable — `SKILL.md` Scope Constraints: *"Do NOT output … suggestions for further research beyond the plan … Emit only the four artifacts."* That lock underwrites the skill's grounding discipline and is itself an anti-pattern entry.

**Resolution (decision D1, user-approved):** the recommender is a **separate sibling skill** (`suggest-tooling`), not a 5th artifact emitted by the grounding engine. `deep-research` gains one default-OFF flag `--suggest-tooling` that *delegates* to the sibling at end-of-run, passing the run directory + the work-relevant topic list Phase 0 already computes. The grounding engine still emits exactly four artifacts; the sibling writes the fifth (`research-toolbox.md`). The four-artifact prose contract across `SKILL.md` / `README.md` / `methodology.md` is **unchanged** — the sibling, not the engine, produces the extra file.

Rationale: trust-model separation (the engine grades *source reliability for facts*; the recommender grades *supply-chain safety of third-party code* — different models, mirroring the project's own Analyst-vs-Critic rule), an independent eval surface, and standalone reusability (`/suggest-tooling <run-dir>` works on any past run).

## 2. Architecture

```
deep-research/  (grounding engine — four-artifact contract UNTOUCHED)
  Phase 0 already computes work_relevant_topics[]  (newsletter-signal predicate)
  Phase 6: if --suggest-tooling (default OFF) → delegate to suggest-tooling, passing run-dir
                                   │
                                   ▼
suggest-tooling/  (sibling skill — opinion engine, own evals, own A6 trust banner)
  SKILL.md                         entry point, trigger, degradation
  references/tooling-discovery.md  per-channel query mechanics + ranking + trust tiers
  references/tooling-categories.md closed, versioned category taxonomy (§3)
  scripts/marketplace_rank.py      THE single ranker + tier cascade (stdlib, zero-network, zero-LLM — I4a)
  imports fake_star_gate() extracted into deep-research/scripts/github_rank.py  (single source of truth; not a 2nd ranker)
  writes → research-toolbox.md      the 5th artifact (this skill's only output)
```

Component boundaries (each independently understandable/testable):

| Unit | Responsibility | Depends on | Failure mode |
|---|---|---|---|
| `--suggest-tooling` flag (in `deep-research`) | At Phase 6, if set, invoke the sibling with run-dir + topics. ~3 lines; no synthesis change. | sibling skill present | sibling absent → print one neutral line, four artifacts unaffected |
| `suggest-tooling` SKILL.md | Orchestrate: read run, classify relevance, query 6 channels, rank, trust-grade, emit toolbox | references + both rank scripts | any channel down → degrade + record |
| `references/tooling-discovery.md` | Per-channel access model, ranking formula, trust-tier rules | — | — |
| `marketplace_rank.py` | THE single composite ranker + total trust-tier cascade + scalar fake-signal heuristic, over a pre-classified candidate JSON | stdlib only | bad input → exit non-zero |
| `github_rank.py` (refactored + reused) | GitHub-leg primitives; gains an extracted `fake_star_gate()` imported by the ranker (not re-run as a 2nd ranker) | — (shipped; behavior-preserving extraction + regression test) | null dependents → gate returns `null`, blocks VERIFIED |

## 3. Work-relevance predicate (decision D2)

**Hat-weighted category match.** Reuses the existing newsletter-signal domain intersection as the *gate*, then refines to a *score*. The classification step is split from the arithmetic step to keep the I4a boundary clean (network/LLM judgment outside the helper script; deterministic math inside it):

1. **Classification (skill's LLM/Bash layer, NOT the helper script).** Map each work-relevant research topic and each discovered candidate → one or more tool **categories** drawn from a **closed, versioned taxonomy** shipped in `references/tooling-categories.md` (e.g. `eval`, `rag`, `mcp-server`, `observability`, `k8s-security`, `scraping`, `prompt-eng`, `agent-orchestration`, `ci-cd`, `secrets-mgmt` — no open ellipsis; new categories are added by editing that file). Emit a structured `{candidate, categories[], category_fit}` JSON where `category_fit ∈ {0, 1}` in v1 (1 = candidate's category set intersects a topic's category set; graded fit is a v2 roadmap item). This step may use LLM reasoning because it runs in the skill context, not in `marketplace_rank.py`.
2. **Arithmetic (deterministic, in `marketplace_rank.py`).** Map each category → the maintainer's profile **hats** with priority weights: AI-Engineer 1.0 · DevSecOps 0.7 · Platform 0.5 · FR-B2B 0.4 (weights live user-scope — see §6). `relevance = max over matched (category_fit × hat_weight)`. A candidate with `relevance == 0` (no category match, or category maps to no hat) is **excluded**. Relevance is both the inclusion floor and a ranking component.

The closed taxonomy is what defends against the *fragile* failure mode: a near-miss topic ("retrieval evaluation") is mapped to `eval`/`rag` by the LLM classification step (semantic, not string-match), so it is not silently dropped — and the eval suite (§9) includes a near-miss fixture to prove it.

The hat-weight table is PII-adjacent (encodes career priorities) → lives user-scope at `~/.claude/deep-research/tooling-hats.json`; the repo ships `tooling-hats.json.example`. Absent file → fall back to the binary newsletter-signal gate (flat relevance = 1 for any work-relevant candidate), recorded in the toolbox.

## 4. Discovery connectors (decision: all six in v1)

All six ship in v1; each is independently degradable (a missing key / unreachable channel records a degradation line and never fails the run). Per-channel mechanics, grounded in the dogfood report:

| Channel | Query (Bash/MCP layer, never in helper scripts) | Trust primitive harvested | Degradation |
|---|---|---|---|
| GitHub (general) | **reuse `github-research.md`** + `github_rank.py` (`gh` CLI, topics `claude-code`/`mcp-server`/`claude-skill`/`claude-plugin`) | official-org, stars (divergence-gated), pushed_at, releases | `gh` absent → Tavily `site:github.com` |
| MCP Registry | public REST `GET /v0/servers` (cursor pagination) via `curl` | reverse-DNS namespace verification (io.github OIDC / com.* DNS) | endpoint down → skip + record |
| Claude Code marketplaces | git-fetch `marketplace.json` from `claude-plugins-official` + `claude-plugins-community` (no search API) | official-curated vs community-reviewed (commit-SHA pinned) | unreachable → skip + record |
| Vercel skills | `skills.sh` leaderboard / `npx skills find` | install counts + official-publisher designation | CLI absent → skip + record |
| Smithery | REST `GET /servers` Bearer token | `verified` flag, `useCount`, `score` | **no `SMITHERY_API_KEY`** → skip + record (degradation expected) |
| awesome-* lists | fetch README (e.g. `punkpeye/awesome-mcp-servers`, `hesreallyhim/awesome-claude-code`) | none (curation reputation is not a trust primitive) | **README = untrusted data (A6)** — **seed-only** (see below) |

**awesome-* lists are seed-only, never a recommendation row.** The dogfood ranking exposed why: with the lists in the candidate set, `github_rank.py` ranked `punkpeye/awesome-mcp-servers` (0.85) and `ComposioHQ/awesome-claude-skills` above actual tools — a meta-list is not a tool. So the awesome-* connector may only **extract candidate repo identifiers** from the README and feed them into the GitHub leg for normal grading; the list repo itself is excluded from `research-toolbox.md` rows by a hard `is_meta_list` filter. **`is_meta_list` is structural/provenance-based, not a name substring (reviewer N4):** a candidate is a meta-list if (primary) it was surfaced *only* via the awesome-* connector's README-extraction path — a `provenance: "awesome-list-seed"` flag set at harvest, the moment a repo is read *out of* a list it can never re-enter *as* a row unless an independent connector also surfaces it; and (secondary) the §3 classifier maps obvious index repos to a `meta-list` category that maps to **no hat → relevance 0 → excluded**. A name pattern (`awesome-*`) is at most a tertiary hint, never the decider — so a legit tool named `awesome-lint` is not false-flagged and an unprefixed curated index is still caught. This keeps the channel in v1 (decision: all six ship) while preventing list-pollution.

All retrieved listings/READMEs are untrusted data: parsed for candidate identifiers, never executed, never allowed to upgrade a trust tier on their own say-so.

## 5. Ranking & trust grading

Two **orthogonal** axes (decision D-trust). Composite (not single-signal) scoring is adopted on first-principles grounds — orthogonal signals shouldn't be collapsed to one number, and your shipped `github_rank.py` already proves the pattern works. (A single MCP-ecosystem preprint also reports a composite cutting ranking variance ~21% vs single-signal, but it is one uncorroborated, sub-0.7-score source [^c-mcpcrawler] — directional support only, not the justification.)

### 5.1 One ranker, github_rank.py reused as the gate (not as the ranker)

`marketplace_rank.py` is the **single** ranker for all channels. `github_rank.py` is **not** re-run as a second ranker (its `expert_overlap` axis has no analog off-GitHub, and the spec must not bolt two non-comparable score scales together). Instead:

- The GitHub connector produces GitHub-derived **primitives** (`stars`, `pushed_at`, `forks`, `open_issues`, `releases_count`, `dependents_count`) and runs the StarScout-derived fake-star divergence test to set `fake_signal_flag`. That test is currently an **inline block** inside `main()` at `scripts/github_rank.py:111-113` (not yet an importable function). The plan therefore **extracts it into `def fake_star_gate(stars, forks, open_issues, dependents) -> bool | None` in `github_rank.py`** — a behavior-preserving refactor (`main()` calls the new function; a regression test asserts `github_rank.py`'s output on the dogfood candidate set is byte-identical before/after) — and `marketplace_rank.py` **imports** it. Single source of truth, genuinely reused, not copy-pasted. The function returns `null` when its inputs (forks/issues/dependents) are absent, which §5.2 routes away from VERIFIED.
- All channels then feed one normalized `marketplace_rank.py` over the same component vocabulary: `relevance` (§3) · `maintenance` (recency of last-push/last-publish + release velocity) · `adoption` (installs/useCount/dependents) · `popularity` (stars — **demoted**). Set-wide-unavailable components are dropped and weights renormalized (same rule and code idiom as `github_rank.py`); effective weights printed, never silently zeroed. One score scale, one ordering.

### 5.2 Trust tier — total, deterministic, ⊥ relevance

Computed as an **ordered cascade** (first match wins, explicit final `else`), so every candidate lands in exactly one tier regardless of which signals are absent (mirrors the credibility cascade in `verify_gates.py:60-74`). `null`/absent signals are handled explicitly — they never silently satisfy a rule:

Every predicate is explicitly null-guarded so no comparison is ever evaluated on a missing value, and the final `else` makes the cascade total:

```
official         := official-org OR verified-namespace(OIDC/DNS) OR official-publisher
activity_known   := last_activity_days is not null
maintained       := activity_known and last_activity_days <= 90
stale            := activity_known and last_activity_days > 180
adoption_known   := adoption is not null            # dependents/useCount present
adopted          := adoption_known and adoption > 0
divergence_known := fake_signal_flag is not null    # the fake-signal gate actually ran
signed           := bool(signed)                    # signed provenance present
corroborated     := divergence_known or adoption_known or signed   # >=1 signal beyond identity

if   fake_signal_flag is True:                                  -> CAUTION    # gamed signal
elif stale:                                                     -> CAUTION    # abandoned
elif official and maintained and corroborated
     and fake_signal_flag is not True:                          -> VERIFIED   # identity + >=1 corroborating signal, not gamed
elif (not official) and maintained and adopted
     and fake_signal_flag is not True:                          -> MAINTAINED
elif maintained or adoption_known or divergence_known:          -> COMMUNITY  # some positive-but-insufficient signal
else:                                                           -> CAUTION    # nothing known (incl. null activity) -> conservative
```

Key disambiguations (each is a §9 unit fixture):
- **`null` adoption routes to COMMUNITY, never MAINTAINED.** Most real candidates have `dependents_count: null` (confirmed: all 10 dogfood repos) — absence of an adoption signal is "unknown," not "adopted." MAINTAINED requires `adopted` (a *positive* number).
- **VERIFIED requires a corroborating signal beyond identity (anti-vacuity).** Official identity + maintained is not enough on its own; the candidate must also have `divergence_known` (the fake-signal gate actually ran) OR `adoption_known` OR `signed` provenance. This keeps an empty official stub (verified namespace but no usage, no signature, no gate result — all null) at COMMUNITY, while letting a verified-namespace **signed** MCP server reach VERIFIED via the `signed` path even though it has no GitHub fake-star data. A non-official repo riding on stars alone never qualifies (VERIFIED requires `official`). Decision A, ratified 2026-06-14 — supersedes the stricter "divergence-gate-must-run" rule from review finding N1, which wrongly capped the registry's strongest signal (namespace verification) at COMMUNITY.
- **Null `last_activity` is handled, not crashed.** `activity_known` gates both `maintained` and `stale`, so a candidate with unknown activity satisfies none of the upper branches and falls to the explicit `else → CAUTION` (conservative). Totality holds for the all-null candidate.
- No rule references `relevance` — trust tier stays orthogonal to the relevance rank.

### 5.3 Fake-signal gate by channel (no hand-waving)

- **GitHub leg:** the extracted `fake_star_gate()` from `github_rank.py` (§5.1) [^c-starscout].
- **Non-GitHub scalar counts (Smithery `useCount`, skills.sh installs):** there is *no event history* to run a spike-vs-usage divergence on, so the spec does **not** claim an "analogous" divergence test. Instead a concrete, stdlib-computable heuristic over the candidate set: a candidate is flagged when `unverified == true` AND its scalar count sits in the set's high percentile AND it has **no corroborating GitHub `dependents`** — loud popularity with no independent adoption trace. **Small-N guard (reviewer N3):** the percentile rule only applies when the per-channel candidate set has `N >= 8`; below that a percentile is statistically meaningless (p90 of N=4 is just "the max"), so `fake_signal_flag = null` (unknown) and the candidate cannot reach VERIFIED on that channel alone. A `N=3` unit fixture asserts no spurious flag. If a channel exposes no count at all (MCP Registry, marketplaces), `fake_signal_flag` is `null`.

Each recommendation row carries the **raw trust evidence** (stars, last activity, official flag, signed/provenance status, `fake_signal_flag`, `adoption`) so the maintainer audits rather than trusts the label.

### 5.4 Cross-channel dedupe (the same tool on 3 channels)

The same MCP server routinely appears on Smithery + MCP Registry + GitHub at once (report c2: sub-registries consume the official registry). Dedupe before ranking, deterministically:

- **Dedupe key:** reverse-DNS server name for MCP servers (`io.github.owner/name` → canonical `owner/name`); `owner/repo` for GitHub/Vercel skills; resolve a registry/Smithery entry to its backing `repository` URL when present so the same project collapses across channels.
- **Primitive merge = trust-conservative:** take the **strongest** verification signal (any channel's verified-namespace/official-org wins) but the **most cautious** maintenance/divergence signal (oldest `last_activity`, and `fake_signal_flag` True if *any* channel flags it). This makes the tier independent of connector ordering (closing the non-determinism the reviewer flagged) and biases toward caution. The merged row records `channels: [...]` listing every surface the tool was found on.

## 6. Determinism & supply-chain contract (I4a + non-negotiable)

- **`marketplace_rank.py` is stdlib-only, zero-network, zero-LLM** (invariant I4a). All network retrieval (registry REST, `gh`, git-fetch, Tavily) happens in the skill's Bash/MCP layer and is handed to the script as a pre-collected candidate JSON — identical to the `github_rank.py` pattern.
- **Never auto-install.** The recommender proposes; install commands are *shown as text, never executed*. No `/plugin install`, no `npx skills add`, no MCP registration is run.
- **All listings/READMEs are untrusted (A6).** Never obey embedded instructions; never upgrade a tier on a README's claim.
- **User-scope secrets/config** (`tooling-hats.json`, `SMITHERY_API_KEY`) live outside the public repo; `.example` templates ship; absence degrades gracefully.

## 7. Output: `research-toolbox.md`

Written by the sibling skill into the run CWD. Structure: (1) a one-line scope banner (work-relevance basis + "proposals only, never auto-installed; all listings untrusted"); (2) recommendations grouped by tool category, each row = `{tool, channels[], relevance, trust_tier, trust_evidence[], install_command (shown)}`, sorted by relevance within `VERIFIED`→`MAINTAINED`→`COMMUNITY`→`CAUTION`; (3) a degradation note (channels skipped + why); (4) machine-readable `research-toolbox.json` sidecar mirroring the rows for auditability. No prose beyond evidence — same surgical-quote discipline as the parent skill.

**CAUTION-only categories are never silently dropped.** If a work-relevant category's only candidates are `CAUTION`, they are surfaced under an explicit `CAUTION — vet manually` subheading with their flags shown, not suppressed — hiding a relevant-but-untrusted result would hide exactly the supply-chain risk the maintainer needs to see. A category with zero candidates at any tier is listed as "no candidate surfaced."

## 8. Invariants & cross-file propagation

- **Four-artifact contract intact.** Because the sibling (not the engine) writes the 5th file, `SKILL.md` / `README.md` / `methodology.md` four-artifact language **does not change**. The only `deep-research` edit is the documented `--suggest-tooling` flag (default OFF) in the flags table + a Phase-6 delegation line — added in the same commit (I5 / Extension protocol).
- **`verify_gates.py` untouched on counts** — it asserts the sources/evidence JSON pair, not a file count, so the 5th artifact does not affect it. No extension needed.
- **I3 (methodology = phase vocab):** unaffected — no new phase; delegation is a Phase-6 post-step.
- **Full local check suite + green CI before commit** (cross-references, provenance, schema, example-invariants, `py_compile`).

## 9. Eval & verification plan

Concrete fixtures, one per failure mode minimum (mirrors the parent skill's loading/e2e/unit discipline — CLAUDE.md):

- **hijacker:** a finished run on a *non*-work-relevant topic (e.g. French medieval history) with `--suggest-tooling` set → MUST emit no recommendation rows (empty toolbox + "no work-relevant topics" note). Fires-when-it-shouldn't is the headline risk for a recommender.
- **silent:** a clearly work-relevant run (e.g. "RAG eval") → MUST surface ≥1 candidate.
- **fragile:** a near-miss topic ("retrieval evaluation" rather than "RAG eval") → MUST still map to `eval`/`rag` and surface candidates (proves the closed-taxonomy + semantic classification of §3).
- **drifter:** a multi-topic run → recommendations stay scoped to the work-relevant topics, not every topic.
- **overachiever:** never installs, never writes outside the run CWD, never emits prose beyond evidence.
- **`marketplace_rank.py` unit suite:** component drop/renormalize; the §5.2 tier cascade **totality gap cases** (90–180d + null adoption → COMMUNITY; official + null divergence → COMMUNITY not VERIFIED; stale → CAUTION; explicit else → CAUTION); the §5.3 scalar fake-signal heuristic; and the §5.4 **cross-channel dedupe** (same server on 3 channels collapses to one trust-conservative row). Mirrors `github_rank.py`'s test style.

The skill itself is then run through `skill-harness`.

## 10. Out of scope (YAGNI)

Auto-install / one-click setup; writing to `~/.claude/`; ranking non-Claude-ecosystem tools; a hosted/always-on recommender; trust *scoring* as a single number (rejected — opaque); persisting recommendations across runs.

## 11. Tracker closure

- **AI-30** (tooling recommender): implemented as `suggest-tooling`. One-line outcome to post on close.
- **AI-40** (marketplace remainder, superseded by AI-30): closed — its marketplace-discovery intent is subsumed by the six-channel connector set here.

[^c-mcpcrawler]: dogfood report, source **s3** only (arXiv "Measurement Study of MCP" preprint, `tavily_score 0.5`, uncorroborated — MCPCrawler's 21%-variance figure appears in s3's notes/prose, has no graded claim id, and is **directional support only**, not a load-bearing justification). Composite scoring is justified on first principles + the shipped `github_rank.py`, not on this stat.
[^c-starscout]: dogfood report c12/c13 (both CONFIRMED), sources s6/s7 (StarScout ICSE-2026 + arXiv preprint).
