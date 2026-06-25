"""Single egress gate: mask secrets/PII and drop identity keys before any Langfuse POST."""
import re

_PATTERNS = [
    re.compile(r"(?i)sk-ant-[a-z0-9-]{20,}"),
    re.compile(r"(?i)sk-lf-[a-z0-9-]{8,}"),
    re.compile(r"(?i)pk-lf-[a-z0-9-]{8,}"),
    re.compile(r"(?i)sk-[a-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)gh[pousr]_[a-z0-9]{20,}"),
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    re.compile(r"\+33[.\s-]?[0-9](?:[.\s-]?[0-9]){8}"),
    re.compile(r"(?i)CANARY-[A-Z0-9-]+"),
]
_MASK = "****REDACTED-SECRET****"

IDENTITY_PII_KEYS = frozenset({
    "user.email", "user.id", "user.account_id", "user.account_uuid", "organization.id",
})

def redact(value):
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

def strip_identity(attrs: dict) -> dict:
    return {k: v for k, v in attrs.items() if k not in IDENTITY_PII_KEYS}
