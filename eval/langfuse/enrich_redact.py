"""Single egress gate: mask secrets/PII and drop identity keys before any Langfuse POST."""
import re
from typing import Any

_PATTERNS = [
    # Anthropic
    re.compile(r"(?i)sk-ant-[a-z0-9-]{20,}"),
    # Langfuse
    re.compile(r"(?i)sk-lf-[a-z0-9-]{8,}"),
    re.compile(r"(?i)pk-lf-[a-z0-9-]{8,}"),
    # Generic sk- (OpenAI-style and similar)
    re.compile(r"(?i)sk-[a-z0-9]{20,}"),
    # AWS access key — case-insensitive fix
    re.compile(r"(?i)AKIA[0-9A-Z]{16}"),
    # GitHub tokens
    re.compile(r"(?i)gh[pousr]_[a-z0-9]{20,}"),
    # Email addresses
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    # French phone numbers
    re.compile(r"\+33[.\s-]?[0-9](?:[.\s-]?[0-9]){8}"),
    # Canary tokens
    re.compile(r"(?i)CANARY-[A-Z0-9-]+"),
    # Google API key
    re.compile(r"AIza[0-9A-Za-z_\-]{35}"),
    # Slack tokens
    re.compile(r"(?i)xox[baprs]-[0-9A-Za-z-]{10,}"),
    # Stripe live keys
    re.compile(r"(?i)(?:sk|rk)_live_[0-9A-Za-z]{16,}"),
    # PEM private-key header
    re.compile(r"(?i)-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"),
    # Labelled secret assignment
    re.compile(r"(?i)(secret|token|api[_-]?key|password|passwd|bearer)[\"'\s:=]+[A-Za-z0-9+/_\-]{8,}"),
]
_MASK = "****REDACTED-SECRET****"

# High-severity residual heuristic — used by fail_closed as a backstop.
# Targets unknown-format credentials without nuking normal research prose.
_HIGH_SEVERITY_RESIDUAL = re.compile(
    r"(?i)(?:-----BEGIN[ A-Z0-9]*PRIVATE KEY-----|"
    r"(?:secret|token|api[_-]?key|password|bearer|authorization)\b[\"'\s:=]+[A-Za-z0-9+/_\-]{12,})"
)

_DROP_PLACEHOLDER = "[REDACTED: dropped — possible secret]"

IDENTITY_PII_KEYS = frozenset({
    "user.email", "user.id", "user.account_id", "user.account_uuid", "organization.id",
})


def redact(value: Any) -> Any:
    """Recursively mask secrets and PII in str/dict/list using _PATTERNS."""
    if isinstance(value, str):
        out = value
        for pat in _PATTERNS:
            out = pat.sub(_MASK, out)
        return out
    if isinstance(value, dict):
        return {k: redact(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    return value


def strip_identity(obj: Any) -> Any:
    """Recursively drop IDENTITY_PII_KEYS at any nesting depth in dicts/lists."""
    if isinstance(obj, dict):
        return {
            k: strip_identity(v)
            for k, v in obj.items()
            if k not in IDENTITY_PII_KEYS
        }
    if isinstance(obj, list):
        return [strip_identity(item) for item in obj]
    return obj


def fail_closed(value: Any) -> Any:
    """Backstop: replace any string that either (a) still matches a high-severity
    residual heuristic OR (b) contains the _MASK sentinel (meaning redact() already
    found a secret in this field) with _DROP_PLACEHOLDER.  Apply AFTER redact().
    Does NOT drop strings merely for being long — only on the heuristic / sentinel.
    """
    if isinstance(value, str):
        if _MASK in value or _HIGH_SEVERITY_RESIDUAL.search(value):
            return _DROP_PLACEHOLDER
        return value
    if isinstance(value, dict):
        return {k: fail_closed(v) for k, v in value.items()}
    if isinstance(value, list):
        return [fail_closed(v) for v in value]
    return value
