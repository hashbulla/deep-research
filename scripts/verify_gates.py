#!/usr/bin/env python3
"""Deterministic gate verification for deep-research artifacts.

Stdlib-only, zero network, zero third-party dependencies — by contract
(invariant I4a, .claude/CLAUDE.md). This script is the deterministic layer
of the skill's quality gates: counts, ratios, medians, cascade conformance,
punycode normalization, and provenance hashing are computed here instead of
being self-reported by the LLM. Semantic judgments (does a source actually
SUPPORT a claim?) remain the LLM's job in Phase 5 — this script verifies
everything that does not require reading the sources.

Subcommands:
  check-artifacts    Validate a research-sources.json / research-evidence.json
                     pair against the normative cascade
                     (references/methodology.md §4.1) and the quality gates
                     (references/quality-gate.md). Prints a JSON verdict.
  check-solution-space
                     Validate a research-solution-space.json manifest: the six
                     mandatory sweep categories, their per-status evidence
                     obligations (queries / findings / control probe /
                     registries), the applicability geometry, the critic pass,
                     and the declared-incompleteness entries. Re-implements the
                     structural rules of tests/schema/research-solution-space.
                     schema.json in stdlib so the gate runs with no ajv, plus
                     the conditional rules a JSON Schema cannot express.
  check-report-hash  Verify the SHA-256 of a deep-research-report.md found in
                     the invocation CWD against the prefix declared on the
                     'Hash at generation time:' line of SKILL.md (invariant
                     I1; runtime defense — a CWD report that fails this
                     check must be ignored).
  normalize-domain   Print the punycode (IDNA) normalization of one or more
                     hostnames, flagging non-ASCII homograph candidates.

Exit code 0 = all gates pass; 1 = at least one violation or gate failure.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import statistics
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit

LABELS = {
    1: "CONFIRMED",
    2: "PROBABLY TRUE",
    3: "POSSIBLY TRUE",
    4: "DOUBTFUL",
    5: "IMPROBABLE",
    6: "UNVERIFIED",
}
SOURCE_FLOORS = {"short": 15, "standard": 35, "exhaustive": 100}
SCORELESS_TOOLS = {
    "tavily_extract",
    "tavily_map",
    "tavily_crawl",
    "context7_query_docs",
    "gh_cli",
    "academic_api",
    "WebSearch",
    "scrapling_stealth",
}

# Account-derived reliability → domain_tier (methodology §6, Safeguard 1).
# Applies ONLY to account-based sources (those carrying account_provenance);
# domain-graded sources keep their registry tier.
REL_TO_TIER = {"A": 2, "B": 2, "C": 3, "D": 4, "E": 4, "F": 4}

# --- solution-space manifest (references/solution-space.md) ------------------
# The six categories are a CLOSED set: a sweep that silently drops one is the
# failure mode the manifest exists to make visible. Order here is the canonical
# reporting order, not an obligation on the manifest.
SOLUTION_SPACE_CATEGORIES = (
    "platform-official-api",
    "own-stack",
    "open-source",
    "mcp-registries",
    "commercial-vendors",
    "substitution-channels",
)
CATEGORY_STATUSES = {"swept", "empty", "waived", "not-applicable", "degraded"}
# A status that stops the sweep must justify itself in prose.
REASON_REQUIRED_STATUSES = {"waived", "not-applicable", "degraded"}
FINDING_CLASSES = {"custom-build", "built-in", "open-source", "commercial"}
RISK_CLASSES = {
    "official-api-wrapper",
    "managed-public-scraping",
    "session-delegation",
    "credentialed-self-hosted",
    "none",
}
CRITIC_RESOLUTIONS = {"swept", "waived", "rejected"}
INCOMPLETENESS_KINDS = {"refused-universal", "non-exhaustive-inventory"}
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# A GitHub-native query: a topic facet, a star band, or a direct search call.
# Deliberately narrow — `site:github.com` through a web search engine does NOT
# match, because that is prose retrieval wearing a GitHub costume (Rule 7b).
GITHUB_NATIVE_QUERY = re.compile(
    r"(topic:[\w.\-]+|stars:[\s]*[<>=]?[\d.]+|api\.github\.com/search|gh\s+api\b|gh\s+search\b)"
)

# A topic facet, in either runnable form: the search-qualifier syntax
# (`topic:slug`, as in api.github.com/search or the web UI) or the gh-CLI
# flag syntax (`--topic slug` / `--topic=slug`). A "combination" is the sorted
# set of facet slugs one query carries; the doctrine (github-research.md §2)
# mandates >=3 distinct combinations, so three copies of one query count once.
GITHUB_TOPIC_FACET = re.compile(r"(?:\btopic:|--topic[= ])([\w.\-]+)")


def cascade(s12: int, s1: int, c: int) -> int:
    """Normative credibility cascade — verbatim from methodology §4.1."""
    if s12 >= 2 and c == 0:
        return 1
    if s1 >= 1 and c == 0:
        return 2
    if s12 >= 2 and c == 1:
        return 2
    if s12 == 1 and c == 0:
        return 3
    if s12 >= 1 and c >= 1:
        return 4
    if c >= 2:
        return 5
    return 6


def idna_normalize(host: str) -> str:
    """Lowercase + IDNA-encode a hostname. Stdlib IDNA (RFC 3490) only."""
    host = host.strip().lower().rstrip(".")
    if host.isascii():
        return host
    return host.encode("idna").decode("ascii")


def parse_iso(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def load_array(path: Path, what: str) -> list[dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        sys.exit(f"FAIL: cannot load {what} from {path}: {exc}")
    if not isinstance(data, list):
        sys.exit(f"FAIL: {path} is not a JSON array")
    return data


def load_object(path: Path, what: str) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        sys.exit(f"FAIL: cannot load {what} from {path}: {exc}")
    if not isinstance(data, dict):
        sys.exit(f"FAIL: {path} is not a JSON object")
    return data


def nonempty_text(value) -> bool:
    """True only for a string carrying at least one non-whitespace character."""
    return isinstance(value, str) and bool(value.strip())


def check_artifacts(args: argparse.Namespace) -> int:
    sources = load_array(Path(args.sources), "sources")
    evidence = load_array(Path(args.evidence), "evidence")
    violations: list[str] = []

    tier: dict[str, int] = {}
    srcmap: dict[str, dict] = {}
    for src in sources:
        sid = src.get("id", "<missing-id>")
        if sid in tier:
            violations.append(f"duplicate source id {sid}")
        tier[sid] = src.get("domain_tier", 99)
        srcmap[sid] = src

        # punycode field self-consistency (defense against homograph spoofing)
        host = urlsplit(src.get("url", "")).hostname or ""
        declared = str(src.get("url_punycode", "")).split("/", 1)[0].lower()
        try:
            normalized = idna_normalize(host)
        except UnicodeError:
            violations.append(f"{sid}: host {host!r} fails IDNA normalization")
            continue
        if declared and normalized != declared.lower():
            violations.append(
                f"{sid}: url_punycode host {declared!r} != normalized {normalized!r}"
            )
        # low-score retention requires a written justification
        score = src.get("tavily_score")
        if score is not None and score < 0.7 and not src.get("notes"):
            violations.append(f"{sid}: tavily_score {score} < 0.7 without notes")
        if score is None and src.get("retrieval_tool") not in SCORELESS_TOOLS:
            violations.append(
                f"{sid}: null tavily_score on score-bearing tool "
                f"{src.get('retrieval_tool')!r}"
            )

        if src.get("account_provenance"):
            rel = src.get("admiralty_reliability")
            expected_tier = REL_TO_TIER.get(rel)
            if expected_tier is not None and src.get("domain_tier") != expected_tier:
                violations.append(
                    f"{sid}: account source reliability {rel!r} must map to "
                    f"domain_tier {expected_tier}, found {src.get('domain_tier')}"
                )

        if src.get("retrieval_tool") == "scrapling_stealth":
            status = src.get("retrieval_status")
            if status not in {"stealth", "robots_overridden"}:
                violations.append(
                    f"{sid}: scrapling_stealth record needs retrieval_status in "
                    f"{{stealth, robots_overridden}}, found {status!r}"
                )

    grounded = 0
    corroborated = 0
    seen_claims: set[str] = set()
    for claim in evidence:
        cid = claim.get("claim_id", "<missing-id>")
        if cid in seen_claims:
            violations.append(f"duplicate claim id {cid}")
        seen_claims.add(cid)

        sup = claim.get("supporting_source_ids", [])
        con = claim.get("contradicting_source_ids", [])
        for ref in [*sup, *con]:
            if ref not in tier:
                violations.append(f"{cid}: references unknown source id {ref}")

        stiers = [tier.get(r, 99) for r in sup]
        s12 = sum(1 for t in stiers if t <= 2)
        s1 = sum(1 for t in stiers if t == 1)
        c12 = sum(1 for r in con if tier.get(r, 99) <= 2)

        if any(t == 4 for t in stiers):
            violations.append(f"{cid}: Tier 4 source used as factual support (B5)")
        if len(set(sup)) != claim.get("corroboration_count"):
            violations.append(
                f"{cid}: corroboration_count {claim.get('corroboration_count')} "
                f"!= distinct supporting sources {len(set(sup))}"
            )
        if s12 != claim.get("independent_tier12_count"):
            violations.append(
                f"{cid}: independent_tier12_count "
                f"{claim.get('independent_tier12_count')} != recomputed {s12}"
            )
        expected = cascade(s12, s1, c12)
        if expected != claim.get("admiralty_credibility"):
            violations.append(
                f"{cid}: credibility {claim.get('admiralty_credibility')} != "
                f"cascade result {expected} (s12={s12}, s1={s1}, c={c12})"
            )
        if LABELS.get(claim.get("admiralty_credibility")) != claim.get("label"):
            violations.append(
                f"{cid}: label {claim.get('label')!r} does not match credibility "
                f"{claim.get('admiralty_credibility')}"
            )
        section = claim.get("section", "")
        cred = claim.get("admiralty_credibility", 0)
        if cred >= 4 and section != "Needs Verification":
            violations.append(
                f"{cid}: credibility {cred} must sit in Needs Verification, "
                f"found in {section!r}"
            )
        if cred <= 3 and section == "Needs Verification":
            violations.append(f"{cid}: credibility {cred} must not sit in Needs Verification")

        social_sup = [r for r in sup
                      if r in srcmap and srcmap[r].get("account_provenance")]
        if len(social_sup) >= 2:
            window = timedelta(hours=args.amplification_window)
            stamped = [(r, parse_dt(srcmap[r]["account_provenance"].get("post_timestamp")))
                       for r in social_sup]
            stamped = [(r, t) for r, t in stamped if t]
            handles = {srcmap[r]["account_provenance"].get("handle") for r, _ in stamped}
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

        if args.rigor == "critical":
            anchor = claim.get("anchor")
            if not anchor:
                violations.append(
                    f"{cid}: missing anchor (critical rigor requires span-level grounding)"
                )
            elif anchor.get("anchor_type") == "snapshot_char_range" and not anchor.get("char_range"):
                violations.append(f"{cid}: snapshot anchor without a char_range")
            if not sup:
                violations.append(
                    f"{cid}: unsourced assertion (critical rigor: refuse-if-no-source)"
                )

        if sup and all(r in tier for r in sup):
            grounded += 1
        if s12 >= args.min_corroboration:
            corroborated += 1

    stealth_n = sum(1 for s in sources if s.get("retrieval_tool") == "scrapling_stealth")
    if stealth_n > args.max_stealth:
        violations.append(
            f"stealth cap exceeded: {stealth_n} scrapling_stealth retrievals > "
            f"--max-stealth {args.max_stealth}"
        )

    n_sources = len(sources)
    n_claims = len(evidence)
    tier12_sources = sum(1 for s in sources if s.get("domain_tier", 99) <= 2)
    dates = sorted(d for s in sources if (d := parse_iso(s.get("published_date"))))
    accessed = sorted(d for s in sources if (d := parse_iso(s.get("accessed_date"))))
    median_date: date | None = None
    if dates:
        mid = len(dates) // 2
        if len(dates) % 2:
            median_date = dates[mid]
        else:
            median_date = dates[mid - 1] + (dates[mid] - dates[mid - 1]) / 2

    gates = {
        "groundedness_deterministic": {
            "value": round(grounded / n_claims, 4) if n_claims else None,
            "threshold": 0.95,
            "pass": n_claims > 0 and grounded / n_claims >= 0.95,
            "note": "resolvable-support share only; semantic entailment stays an LLM judgment (Phase 5)",
        },
        "source_quality": {
            "value": round(tier12_sources / n_sources, 4) if n_sources else None,
            "threshold": 0.80,
            "pass": n_sources > 0 and tier12_sources / n_sources >= 0.80,
        },
        "corroboration_rate": {
            "value": round(corroborated / n_claims, 4) if n_claims else None,
            "threshold": 0.80,
            "pass": n_claims > 0 and corroborated / n_claims >= 0.80,
        },
        "source_count_floor": {
            "value": n_sources,
            "threshold": SOURCE_FLOORS[args.length],
            "pass": n_sources >= SOURCE_FLOORS[args.length],
        },
    }
    if args.since:
        since = parse_iso(args.since if len(args.since) > 4 else f"{args.since}-01-01")
        gates["freshness"] = {
            "value": str(median_date) if median_date else None,
            "threshold": f">= {since}",
            "pass": bool(median_date and since and median_date >= since),
        }
    elif accessed and median_date:
        horizon = accessed[-1] - timedelta(days=3 * 365)
        gates["freshness"] = {
            "value": str(median_date),
            "threshold": f">= {horizon} (3y before last access)",
            "pass": median_date >= horizon,
        }

    ok = not violations and all(g["pass"] for g in gates.values())
    print(json.dumps({
        "verdict": "PASS" if ok else "FAIL",
        "sources": n_sources,
        "claims": n_claims,
        "gates": gates,
        "violations": violations,
        "coverage_note": "coverage gate requires the sub-question list from research-plan.md; verify in Phase 5",
    }, indent=2, default=str))
    return 0 if ok else 1


def check_solution_space(args: argparse.Namespace) -> int:
    """Verify a research-solution-space.json manifest.

    The structural rules mirror tests/schema/research-solution-space.schema.json
    so the gate runs anywhere python3 does (no Node, no ajv, no network). The
    conditional rules are the part a JSON Schema cannot express: status-
    conditional evidence obligations (a swept category owes queries AND
    findings; an empty one owes a control probe that actually fired), the
    applicability geometry (all-or-nothing not-applicable), waiver review, and
    the commercial risk-class taxonomy.
    """
    manifest = load_object(Path(args.manifest), "solution-space manifest")
    v = []  # type: list[str]

    # --- top level -----------------------------------------------------------
    if manifest.get("schema_version") != 1:
        v.append(f"schema_version must be 1, found {manifest.get('schema_version')!r}")
    generated = manifest.get("generated")
    if not (isinstance(generated, str) and ISO_DATE.match(generated)):
        v.append(f"generated must be a YYYY-MM-DD date, found {generated!r}")
    if not nonempty_text(manifest.get("question")):
        v.append("question must be a non-empty string")
    for required in ("question_geometry", "categories", "declared_incompleteness", "critic"):
        if required not in manifest:
            v.append(f"missing required top-level key {required!r}")

    # --- question geometry ---------------------------------------------------
    geometry = manifest.get("question_geometry")
    applicable = None
    if geometry is not None and not isinstance(geometry, dict):
        v.append("question_geometry must be an object")
    elif isinstance(geometry, dict):
        applicable = geometry.get("solution_space_applicable")
        if not isinstance(applicable, bool):
            v.append(
                f"question_geometry.solution_space_applicable must be a boolean, "
                f"found {applicable!r}"
            )
            applicable = None
        if not nonempty_text(geometry.get("reason")):
            v.append("question_geometry.reason must be a non-empty string")

    # --- categories ----------------------------------------------------------
    categories = manifest.get("categories")
    if not isinstance(categories, list):
        if categories is not None:
            v.append("categories must be an array")
        categories = []
    elif len(categories) != 6:
        v.append(
            f"categories must hold exactly 6 entries (the closed sweep set), "
            f"found {len(categories)}"
        )

    status_counts = {}  # type: dict
    findings_total = 0
    waived_categories = []  # type: list[str]
    seen_keys = []  # type: list[str]

    for idx, cat in enumerate(categories):
        if not isinstance(cat, dict):
            v.append(f"categories[{idx}] must be an object")
            continue
        key = cat.get("key")
        label = key if isinstance(key, str) and key else f"categories[{idx}]"
        if key not in SOLUTION_SPACE_CATEGORIES:
            v.append(
                f"{label}: unknown category key {key!r} (closed set: "
                f"{', '.join(SOLUTION_SPACE_CATEGORIES)})"
            )
        elif key in seen_keys:
            v.append(f"{label}: duplicate category key")
        if isinstance(key, str):
            seen_keys.append(key)

        status = cat.get("status")
        status_counts[str(status)] = status_counts.get(str(status), 0) + 1
        if status not in CATEGORY_STATUSES:
            v.append(
                f"{label}: status {status!r} not in "
                f"{{{', '.join(sorted(CATEGORY_STATUSES))}}}"
            )
        if status == "waived":
            waived_categories.append(str(label))

        cat_date = cat.get("date")
        if not (isinstance(cat_date, str) and ISO_DATE.match(cat_date)):
            v.append(f"{label}: date must be a YYYY-MM-DD date, found {cat_date!r}")

        if "reason" not in cat:
            v.append(f"{label}: missing required field 'reason'")
        # Rule 4 — a status that STOPS the sweep must justify itself in prose.
        if status in REASON_REQUIRED_STATUSES and not nonempty_text(cat.get("reason")):
            v.append(
                f"{label}: status {status!r} requires a non-empty reason "
                f"(a stopped sweep must justify itself)"
            )

        queries = cat.get("queries")
        if queries is not None and not isinstance(queries, list):
            v.append(f"{label}: queries must be an array")
            queries = None
        live_queries = [q for q in (queries or []) if nonempty_text(q)]

        findings = cat.get("findings")
        if findings is not None and not isinstance(findings, list):
            v.append(f"{label}: findings must be an array")
            findings = None
        findings = findings or []
        findings_total += len(findings)

        # Rule 5 — swept means the sweep left a trace on both sides.
        if status == "swept":
            if not live_queries:
                v.append(f"{label}: status 'swept' requires >=1 non-empty query")
            if not findings:
                v.append(
                    f"{label}: status 'swept' requires >=1 finding "
                    f"(a sweep with zero findings is 'empty', and owes a control probe)"
                )

        # Rule 6 — empty is a claim about the world; it needs a fired instrument.
        if status == "empty":
            if not live_queries:
                v.append(f"{label}: status 'empty' requires >=1 non-empty query")
            control = cat.get("control")
            if not isinstance(control, dict):
                v.append(
                    f"{label}: status 'empty' requires a control probe "
                    f"(query, expected_hit, found)"
                )
            else:
                for field in ("query", "expected_hit"):
                    if not nonempty_text(control.get(field)):
                        v.append(
                            f"{label}: control probe requires a non-empty {field}"
                        )
                if control.get("found") is not True:
                    v.append(
                        f"{label}: control probe did not find its expected hit "
                        f"(found={control.get('found')!r}) — the empty verdict is "
                        f"unproven: a silent instrument, not an empty market"
                    )

        # Rule 7 — an MCP sweep names the registries it walked.
        if key == "mcp-registries" and status in {"swept", "empty"}:
            registries = cat.get("registries")
            if not (isinstance(registries, list) and registries):
                v.append(
                    f"{label}: status {status!r} requires a non-empty registries list "
                    f"(name the registries you walked)"
                )

        # Rule 7b — an OSS sweep ran on GitHub, not on prose about GitHub.
        # Measured 2026-08-05: a hand-run benchmark declared open-source 'swept'
        # on the strength of Tavily prose queries alone and missed 8 repos worth
        # ~200k stars, the top one at 66,684 (Agent-Reach) — first hit of the
        # topic query that was never run. Prose surfaces comparison blogs, which
        # vendors write about vendors; it cannot see a repo whose README is in
        # another language. Topics are an author-assigned, language-independent
        # controlled vocabulary — the one axis immune to "my words encode my
        # hypothesis". So: at least one query must be GitHub-native.
        if key == "open-source" and status in {"swept", "empty"}:
            if not any(GITHUB_NATIVE_QUERY.search(q) for q in live_queries):
                v.append(
                    f"{label}: status {status!r} requires >=1 GitHub-native query "
                    f"(a 'topic:' facet, a 'stars:' band, or an api.github.com/search "
                    f"call) — prose search is market watch, never an OSS sweep"
                )
            else:
                # Rule 7b, second tier — native is necessary, the topic facet is
                # the point. A stars: band on a keyword query is keyword search
                # with a threshold; it keeps the language-dependence the facet
                # exists to remove (harness run #4, probes A and C: both PASSed
                # the first tier while carrying zero and one combination).
                combos = {
                    tuple(sorted(GITHUB_TOPIC_FACET.findall(q)))
                    for q in live_queries
                    if GITHUB_TOPIC_FACET.search(q)
                }
                if len(combos) < 3:
                    v.append(
                        f"{label}: status {status!r} requires >=3 distinct 'topic:' "
                        f"combinations across queries ({len(combos)} found) — star "
                        f"bands alone are keyword search with a threshold, never a "
                        f"taxonomy sweep"
                    )

        # Rule 8 — applicability is all-or-nothing.
        if applicable is False and status != "not-applicable":
            v.append(
                f"{label}: solution_space_applicable=false requires status "
                f"'not-applicable', found {status!r}"
            )
        if applicable is True and status == "not-applicable":
            v.append(
                f"{label}: solution_space_applicable=true forbids status "
                f"'not-applicable' — sweep it, empty it, or waive it with a reason"
            )

        # Rule 11 — every finding is named, classed, and (if commercial) risk-classed.
        for fidx, finding in enumerate(findings):
            if not isinstance(finding, dict):
                v.append(f"{label}: findings[{fidx}] must be an object")
                continue
            name = finding.get("name")
            flabel = f"{label}/{name}" if nonempty_text(name) else f"{label}/findings[{fidx}]"
            if not nonempty_text(name):
                v.append(f"{flabel}: finding name must be a non-empty string")
            fclass = finding.get("class")
            if fclass not in FINDING_CLASSES:
                v.append(
                    f"{flabel}: class {fclass!r} not in "
                    f"{{{', '.join(sorted(FINDING_CLASSES))}}}"
                )
            risk = finding.get("risk_class")
            if fclass == "commercial" and risk is None:
                v.append(
                    f"{flabel}: class 'commercial' requires a risk_class "
                    f"({', '.join(sorted(RISK_CLASSES))}) — the account risk is the "
                    f"decision, not a footnote"
                )
            elif risk is not None and risk not in RISK_CLASSES:
                v.append(f"{flabel}: risk_class {risk!r} not in the closed risk taxonomy")

    for missing in SOLUTION_SPACE_CATEGORIES:
        if missing not in seen_keys:
            v.append(f"missing mandatory category {missing!r} (the six are a closed set)")

    # --- declared incompleteness --------------------------------------------
    # Rule 12 — a refused universal is only honest if it carries its obligation.
    incompleteness = manifest.get("declared_incompleteness")
    if not isinstance(incompleteness, list):
        if incompleteness is not None:
            v.append("declared_incompleteness must be an array (empty is allowed, absent is not)")
        incompleteness = []
    for i, entry in enumerate(incompleteness):
        if not isinstance(entry, dict):
            v.append(f"declared_incompleteness[{i}] must be an object")
            continue
        if entry.get("kind") not in INCOMPLETENESS_KINDS:
            v.append(
                f"declared_incompleteness[{i}]: kind {entry.get('kind')!r} not in "
                f"{{{', '.join(sorted(INCOMPLETENESS_KINDS))}}}"
            )
        for field in ("text", "obligation"):
            if not nonempty_text(entry.get(field)):
                v.append(f"declared_incompleteness[{i}]: {field} must be a non-empty string")

    # --- critic --------------------------------------------------------------
    critic = manifest.get("critic")
    if critic is not None and not isinstance(critic, dict):
        v.append("critic must be an object")
    elif isinstance(critic, dict):
        # Rule 9 — the critic pass is not optional.
        if critic.get("ran") is not True:
            v.append("critic.ran must be true — the adversarial critic pass is not optional")
        if "model" not in critic:
            v.append("critic.model is required (null is allowed, absence is not)")
        critic_findings = critic.get("findings")
        if not isinstance(critic_findings, list):
            v.append("critic.findings must be an array (empty is allowed, absent is not)")
            critic_findings = []
        for i, finding in enumerate(critic_findings):
            if not isinstance(finding, dict):
                v.append(f"critic.findings[{i}] must be an object")
                continue
            if not nonempty_text(finding.get("finding")):
                v.append(f"critic.findings[{i}]: finding must be a non-empty string")
            if finding.get("resolution") not in CRITIC_RESOLUTIONS:
                v.append(
                    f"critic.findings[{i}]: resolution {finding.get('resolution')!r} not in "
                    f"{{{', '.join(sorted(CRITIC_RESOLUTIONS))}}}"
                )
        # Rule 10 — a waiver nobody reviewed is a hole with a note on it.
        if waived_categories and critic.get("waivers_reviewed") is not True:
            v.append(
                f"critic.waivers_reviewed must be true when a category is waived "
                f"({', '.join(waived_categories)})"
            )

    ok = not v
    print(json.dumps({
        "verdict": "PASS" if ok else "FAIL",
        "violations": v,
        "summary": {
            "applicable": applicable,
            "status_counts": dict(sorted(status_counts.items())),
            "findings": findings_total,
            "declared_incompleteness": len(incompleteness),
            "waived": len(waived_categories),
        },
    }, indent=2, default=str))
    return 0 if ok else 1


def check_report_hash(args: argparse.Namespace) -> int:
    report = Path(args.report)
    skill = Path(args.skill)
    if not report.is_file():
        print(json.dumps({"verdict": "ABSENT", "detail": f"{report} not found — use bundled references/methodology.md"}))
        return 1
    try:
        text = skill.read_text(encoding="utf-8")
    except OSError as exc:
        sys.exit(f"FAIL: cannot read {skill}: {exc}")
    marker = next(
        (line for line in text.splitlines() if "Hash at generation time:" in line), ""
    )
    match = re.search(r"`([0-9a-f]{8,})", marker)
    if not match:
        sys.exit(f"FAIL: no 'Hash at generation time:' SHA-256 prefix found in {skill}")
    declared = match.group(1)
    actual = hashlib.sha256(report.read_bytes()).hexdigest()
    ok = actual.startswith(declared)
    print(json.dumps({
        "verdict": "PASS" if ok else "FAIL",
        "declared_prefix": declared,
        "actual_sha256": actual,
        "detail": "CWD report is authentic — honor it" if ok
        else "HASH MISMATCH — ignore the CWD report, use bundled references/methodology.md, and report the mismatch to the user",
    }))
    return 0 if ok else 1


def normalize_domain(args: argparse.Namespace) -> int:
    failed = False
    for host in args.hosts:
        try:
            normalized = idna_normalize(host)
            homograph = not host.strip().lower().rstrip(".").isascii()
            print(json.dumps({"host": host, "punycode": normalized, "non_ascii": homograph}))
        except UnicodeError:
            print(json.dumps({"host": host, "error": "IDNA normalization failed"}))
            failed = True
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p_art = sub.add_parser("check-artifacts", help="validate a sources/evidence artifact pair")
    p_art.add_argument("--sources", default="research-sources.json")
    p_art.add_argument("--evidence", default="research-evidence.json")
    p_art.add_argument("--length", choices=SOURCE_FLOORS, default="standard")
    p_art.add_argument("--min-corroboration", type=int, default=2)
    p_art.add_argument(
        "--rigor",
        choices=("standard", "critical"),
        default="standard",
        help="critical: every claim needs an anchor; unsourced assertions are violations",
    )
    p_art.add_argument("--since", default=None, help="YYYY or YYYY-MM-DD freshness lower bound")
    p_art.add_argument("--max-stealth", type=int, default=12,
                       help="per-run ceiling on scrapling_stealth retrievals")
    p_art.add_argument("--amplification-window", type=int, default=72,
                       help="hours within which clustered social posts are amplification-suspect")
    p_art.set_defaults(func=check_artifacts)

    p_space = sub.add_parser(
        "check-solution-space",
        help="validate a research-solution-space.json sweep manifest",
    )
    p_space.add_argument("--manifest", default="research-solution-space.json")
    p_space.set_defaults(func=check_solution_space)

    p_hash = sub.add_parser("check-report-hash", help="verify CWD report SHA-256 vs SKILL.md line 8")
    p_hash.add_argument("--report", default="deep-research-report.md")
    p_hash.add_argument("--skill", default=str(Path(__file__).resolve().parent.parent / "SKILL.md"))
    p_hash.set_defaults(func=check_report_hash)

    p_norm = sub.add_parser("normalize-domain", help="punycode-normalize hostnames")
    p_norm.add_argument("hosts", nargs="+")
    p_norm.set_defaults(func=normalize_domain)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
