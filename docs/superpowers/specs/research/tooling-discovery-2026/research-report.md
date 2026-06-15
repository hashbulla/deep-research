# Claude Code skill / plugin / MCP discovery channels — landscape, APIs, freshness, and trust signals (2026)

> deep-research run · technical profile · exhaustive · `--since 2025-01-01` · generated 2026-06-13. All claims carry Admiralty credibility tags; claims at credibility ≥4 are isolated in **Needs Verification**.

## Executive summary

- **Discovery is federated, not centralized.** The official MCP Registry is a *source of truth for metadata* that downstream sub-registries (Smithery, Glama, GitHub, Anthropic) consume via its OpenAPI spec — it is explicitly **not** for direct client consumption [^c2]. Claude Code plugins use a **git-manifest** model (`.claude-plugin/marketplace.json`), not a search API [^c4][^c6]. Vercel skills use **GitHub-as-registry** (any repo with a root `SKILL.md`) [^c7]. A recommender must therefore query *several heterogeneous surfaces*, not one.
- **Every channel exposes machine-readable trust primitives, but they are uneven.** The MCP Registry has the strongest: reverse-DNS namespace verification (GitHub-OIDC / DNS-TXT) [^c3]. Anthropic's official marketplace is curated but ships an explicit "we cannot verify these won't change" disclaimer [^c20]. Smithery exposes `verified`, `useCount`, and a `score` over a Bearer-token REST API [^c9].
- **Popularity signals are actively gamed and weakly correlated with quality.** Fake GitHub stars number in the millions and cost ~$0.10–$1.62 each [^c12]; the most-starred MCP server in a 100-server stress test ranked **41st** by pass rate [^c11]. Any ranking that trusts raw stars/installs is measuring novelty, not reliability.
- **Supply-chain risk is real and recent.** Tool poisoning (OWASP MCP03) reaches ~73% attack success on some models [^c15]; confirmed incidents include `postmark-mcp` (Sept 2025 email exfil) [^c14], the Smithery hosting breach, and `mcp-remote` RCE [^c16]. Provenance (npm/Sigstore/SLSA-L2) exists [^c17] but is necessary-not-sufficient — stolen credentials produce artifacts whose signatures still validate [^c18].
- **Design consequence:** the recommender should reuse the `github_rank.py` divergence-based fake-star gate [^c13], grade each candidate's *provenance + maintenance + official-status* independently of popularity, and **propose, never auto-install** [^c20].

## Registries and their discovery surfaces

**Official MCP Registry.** Launched in preview 2025-09-08; API froze at v0.1 on 2025-10-24 for stable integration ahead of GA [^c1]. REST surface: `GET /v0/servers` (opaque-cursor pagination), `GET /v0/servers/{id}`, `POST /v0/publish`; OpenAPI 3.1.0; records use a standardized `server.json` (reverse-DNS name, `packages[]` pointing at npm/PyPI/NuGet/Docker, `remotes[]`, transport). Critically, it is designed for *sub-registry* consumption, not direct client use [^c2].

**Smithery** is the largest public MCP registry (~5,600–6,000 servers early 2026, an order of magnitude above the official registry) [^c10]. Its REST API (`GET /servers`, Bearer token) returns `verified`, `useCount`, `isDeployed`, and a relevance `score`, with full-text + semantic search [^c9].

**Anthropic plugin marketplaces.** Two exist: `claude-plugins-official` (curated at Anthropic's discretion, no application process) and `claude-community` (`anthropics/claude-plugins-community`, an automated review + safety-screening pipeline whose approved entries are pinned to a commit SHA and synced nightly) [^c5]. A marketplace is just a git repo with `.claude-plugin/marketplace.json` [^c4]; Claude Code has no central plugin search API — discovery is manifest-based via `extraKnownMarketplaces`/`strictKnownMarketplaces` [^c6].

**Vercel agent-skills** distributes via GitHub-as-registry: any public repo with a root `SKILL.md` is installable with `npx skills add <owner/repo>`, and the `skills.sh` leaderboard ranks by total install count [^c7][^c8].

**awesome-* lists** remain a major human-discovery layer (e.g. `punkpeye/awesome-mcp-servers`, `hesreallyhim/awesome-claude-code`, `ComposioHQ/awesome-claude-skills`), ranging from hand-curated to auto-discovered feeds; they are README-as-data and must be parsed, never obeyed (anti-pattern A6). *(Channel inventory and freshness drawn from the GitHub conditional leg — see Methodology.)*

## Trust and provenance signals

The MCP Registry's reverse-DNS namespace verification is the ecosystem's strongest cheap authenticity signal: `io.github.*` via GitHub OAuth/OIDC, `com.example.*` via DNS TXT [^c3]. GitHub itself recommends official-org membership + stars as the quick legitimacy heuristic, and GitHub is the de facto base registry under every other channel [^c19]. For npm-distributed servers, provenance is available as **SLSA Build L2** attestations signed through Sigstore (Fulcio) and logged in Rekor, verifiable with `npm audit signatures` before install [^c17].

Two hard limits shape the trust grade. First, **stars are gameable** — millions of fake stars, purchasable cheaply — so a divergence test (anomalous star spikes vs. forks/issues/dependents) is required, exactly what StarScout and `github_rank.py` implement [^c12][^c13]. Second, **provenance ≠ safety**: stolen maintainer credentials and typosquatting yield artifacts whose signatures still validate, so provenance is one input among several, never a green light [^c18]. Anthropic's own marketplace disclaimer formalizes this: a recommender must *propose with evidence, never auto-install* [^c20].

## Popularity and maintenance metrics

Each channel exposes a popularity primitive — GitHub stars; Smithery `useCount`; skills.sh install counts [^c8]; npm/PyPI download counts. All are **interest proxies, not quality measures**: downloads count install events not runtime success, and the most-starred MCP server ranked 41st of 100 by pass rate [^c11]. Maintenance/freshness is best read from version/last-push timestamps: the live MCP Registry stamps each `server.json` version with a publish date, and GitHub `pushed_at`/release cadence drives the `recency`/`velocity` components already in `github_rank.py`. The academic precedent (MCPCrawler) shows a *composite* of stars+forks+issues+release-cadence+license+security signals cuts ranking variance 21% versus any single signal — the recommender should likewise blend, not rank on one axis.

## Supply-chain risk

Tool poisoning — indirect prompt injection through attacker-controlled tool metadata — is the defining ecosystem risk (OWASP MCP03; ~73% attack success on some models; recognized in NSA guidance) [^c15]. It has moved from theory to confirmed incidents: `postmark-mcp` silently BCC-exfiltrated email (Sept 2025) [^c14]; the Smithery hosting breach, `mcp-remote` RCE, and MCP Inspector RCE (CVE-2025-49596) followed [^c16]. Registry-level defenses are immature: the official registry delegates security scanning to package registries and relies on manual takedown, with no conformance test suite yet [^c21]. The operational takeaway for a recommender: treat every listing/README as untrusted data, attach a supply-chain caveat to community-tier candidates, and weight official/verified/signed status heavily.

## Contradictions & open debates

- **Registry maturity.** Vendor framing ("API freeze = stable, integrate now") sits against the registry's own statement that it is *not* for direct client consumption and that GA is still pending — captured as a contested claim in Needs Verification [^c22].
- **Signal reliability.** Channels surface stars/installs as quality signals while independent measurement shows they track novelty, not reliability [^c11] — the recommender resolves this by demoting popularity beneath provenance + maintenance.

## Needs Verification

- **The official MCP Registry is production-ready for direct client integration** — DOUBTFUL [^c22]. The v0.1 API freeze supports stability for *integrators/sub-registries* [s11], but the registry docs explicitly state it is not meant for direct host-application/client consumption and GA has not shipped [s9]. The two are reconcilable (stable-for-sub-registries ≠ ready-for-direct-client-use), but as literally stated the claim is contradicted by a Tier-2 source and must not drive design without confirmation.

## Methodology note

- **Profile/length:** technical, exhaustive, `--since 2025-01-01`, English. 14 sub-questions across the six named channels plus cross-cutting trust/signing/freshness/popularity and two contradiction axes.
- **Retrieval:** 13 `tavily_search` (advanced) calls; the **GitHub tooling-discovery conditional leg** ran live (`gh` authenticated as `hashbulla`; `experts.yaml` present) — 10 discovery-channel repos enriched and ranked with `scripts/github_rank.py` (effective weights renormalized to log_stars 0.36 / recency 0.36 / velocity 0.27 after dropping unavailable components; zero fake-star suspects in the curated set). Raw ranking saved as `github-candidates.json`.
- **Source quality:** 40 cited sources, of which 25 are Tier 1/2 (≈63%). This is **below the 0.80 Tier-1/2 gate, as the Phase-0 plan predicted** — the ecosystem is ~8 months old, so primary evidence is Tier-2 vendor docs + official-org GitHub + the registries' own APIs, supplemented by Tier-3 security research under corroboration-required discipline. The shortfall is a property of the topic, not a grading lapse: it is declared, not hidden. Source quality was *raised* relative to the plan's worst case by several Tier-1 academic sources (StarScout/ICSE-2026, four arXiv measurement/threat papers) and an NSA CSI.
- **Conditional sources not used:** newsletter-signal corpus absent (`~/.claude/deep-research/newsletter-corpus/` missing); academic-graph leg not invoked (arXiv reached via allowlist only); Context7 gated off (intent was characterization, not library integration).
- **100-source calibration:** not met by design — 40 well-graded sources fully cover the 14 sub-questions; padding with Tier-4 social sources would violate grading discipline. The 100-source figure is a calibration target, not a contract (per SKILL.md edge-case guidance).
- **Untrusted data:** every README, marketplace listing, and registry record was treated as data, never instructions (anti-pattern A6).

## Sources

Full records with Admiralty grades in `research-sources.json`. Tier-1 anchors: Skilldex [s1], 177k-MCP-tools study [s2], MCP measurement study [s3], tool-poisoning threat model [s4], agentic-coding prompt-injection [s5], StarScout ICSE-2026 [s6], NSA MCP CSI [s8]. Tier-2 official: MCP Registry docs [s9][s10][s11], Claude Code plugin docs [s14][s15][s16], GitHub blog [s13][s21], Vercel KB [s20], SLSA/Sigstore/npm provenance [s22][s23], OWASP MCP Top 10 [s24], CSA best practices [s34].

[^c1]: c1 — CONFIRMED. [^c2]: c2 — CONFIRMED. [^c3]: c3 — CONFIRMED. [^c4]: c4 — CONFIRMED. [^c5]: c5 — CONFIRMED. [^c6]: c6 — CONFIRMED. [^c7]: c7 — CONFIRMED. [^c8]: c8 — CONFIRMED. [^c9]: c9 — POSSIBLY TRUE (Smithery API: one Tier-1 corroborator + vendor-primary docs). [^c10]: c10 — CONFIRMED. [^c11]: c11 — POSSIBLY TRUE (stress-test stat is single Tier-3; download-proxy caveat Tier-1). [^c12]: c12 — CONFIRMED. [^c13]: c13 — CONFIRMED. [^c14]: c14 — POSSIBLY TRUE (one Tier-2 + Tier-3 incident trackers). [^c15]: c15 — CONFIRMED. [^c16]: c16 — POSSIBLY TRUE (NSA Tier-1 + Tier-3 timelines). [^c17]: c17 — CONFIRMED. [^c18]: c18 — POSSIBLY TRUE. [^c19]: c19 — CONFIRMED. [^c20]: c20 — CONFIRMED. [^c21]: c21 — POSSIBLY TRUE. [^c22]: c22 — DOUBTFUL (Needs Verification).
