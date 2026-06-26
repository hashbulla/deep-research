"""Single egress gate: mask secrets/PII and drop identity keys before any Langfuse POST."""
import re
from typing import Any

# MASK tier — keep field, replace the secret in place.
_PATTERNS = [
    # Anthropic
    re.compile(r"(?i)sk-ant-[a-z0-9-]{20,}"),
    # Langfuse
    re.compile(r"(?i)sk-lf-[a-z0-9-]{8,}"),
    re.compile(r"(?i)pk-lf-[a-z0-9-]{8,}"),
    # Generic sk- (OpenAI-style and similar)
    re.compile(r"(?i)sk-[a-z0-9]{20,}"),
    # AWS access key
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
    re.compile(r"(?i)AIza[0-9A-Za-z_\-]{35}"),
    # Slack tokens
    re.compile(r"(?i)xox[baprs]-[0-9A-Za-z-]{10,}"),
    # Stripe live keys
    re.compile(r"(?i)(?:sk|rk)_live_[0-9A-Za-z]{16,}"),
    # GitHub fine-grained PATs
    re.compile(r"(?i)github_pat_[0-9a-z_]{20,}"),
]
_MASK = "****REDACTED-SECRET****"

# DROP tier — whole field dropped; checked on the RAW value before any masking.
# Covers PEM private-key blocks and labelled credential assignments.
_DROP_HEURISTIC = re.compile(
    r"(?i)(?:-----BEGIN[ A-Z0-9]*PRIVATE KEY-----|"
    r"(?:secret|token|api[_-]?key|password|bearer|authorization)\b[\"'\s:=]+[A-Za-z0-9+/_\-]{8,})"
)

_DROP_PLACEHOLDER = "[REDACTED: dropped — possible secret]"

IDENTITY_PII_KEYS = frozenset({
    "user.email", "user.id", "user.account_id", "user.account_uuid", "organization.id",
})


def redact(value: Any) -> Any:
    """Recursively mask MASK-tier secrets and PII in str/dict/list using _PATTERNS."""
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
    """Composed sanitizer applied to RAW values (before any masking).

    Two-tier strategy:
    - DROP tier: if the raw string matches _DROP_HEURISTIC (PEM block or labelled
      credential assignment), replace the entire field with _DROP_PLACEHOLDER.
    - MASK tier: otherwise, delegate to redact() to mask known secrets/PII in place
      while keeping the field.

    Caller must pass the RAW value, not the output of redact() — the drop check must
    see the original plaintext before masking obscures the pattern.
    """
    if isinstance(value, str):
        if _DROP_HEURISTIC.search(value):
            return _DROP_PLACEHOLDER
        return redact(value)
    if isinstance(value, dict):
        return {k: fail_closed(v) for k, v in value.items()}
    if isinstance(value, list):
        return [fail_closed(v) for v in value]
    return value
