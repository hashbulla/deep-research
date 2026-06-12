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
  check-report-hash  Verify the SHA-256 of a deep-research-report.md found in
                     the invocation CWD against the prefix declared on
                     SKILL.md line 8 (invariant I1; runtime defense per
                     anti-pattern guidance — a CWD report that fails this
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
from datetime import date, timedelta
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
SCORELESS_TOOLS = {"tavily_extract", "tavily_map", "tavily_crawl", "WebSearch"}


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


def load_array(path: Path, what: str) -> list[dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        sys.exit(f"FAIL: cannot load {what} from {path}: {exc}")
    if not isinstance(data, list):
        sys.exit(f"FAIL: {path} is not a JSON array")
    return data


def check_artifacts(args: argparse.Namespace) -> int:
    sources = load_array(Path(args.sources), "sources")
    evidence = load_array(Path(args.evidence), "evidence")
    violations: list[str] = []

    tier: dict[str, int] = {}
    for src in sources:
        sid = src.get("id", "<missing-id>")
        if sid in tier:
            violations.append(f"duplicate source id {sid}")
        tier[sid] = src.get("domain_tier", 99)

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

        if sup and all(r in tier for r in sup):
            grounded += 1
        if s12 >= args.min_corroboration:
            corroborated += 1

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


def check_report_hash(args: argparse.Namespace) -> int:
    report = Path(args.report)
    skill = Path(args.skill)
    if not report.is_file():
        print(json.dumps({"verdict": "ABSENT", "detail": f"{report} not found — use bundled references/methodology.md"}))
        return 1
    try:
        line8 = skill.read_text(encoding="utf-8").splitlines()[7]
    except (OSError, IndexError) as exc:
        sys.exit(f"FAIL: cannot read line 8 of {skill}: {exc}")
    match = re.search(r"`([0-9a-f]{8,})", line8)
    if not match:
        sys.exit(f"FAIL: no SHA-256 prefix found on {skill} line 8")
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
    p_art.add_argument("--since", default=None, help="YYYY or YYYY-MM-DD freshness lower bound")
    p_art.set_defaults(func=check_artifacts)

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
