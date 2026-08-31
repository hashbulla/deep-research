"""Langfuse REST client: request_id index + ingestion POST.

Implements:
- build_request_id_index — GET /api/public/observations?traceId=... → {request_id: obs_id}
- ingestion_body         — PURE function: [ObservationUpdate] → ingestion batch dict
- post_updates           — POST /api/public/ingestion, returns parsed JSON

Contracts (from eval/langfuse/M3-CONTRACT.md, Task 1 spike):
- GENERATION observations → event type "generation-update"
- SPAN observations       → event type "span-update"
- "observation-update" is rejected by Langfuse (HTTP 207/400).
- request_id lives at metadata.attributes.request_id (primary)
  or metadata.attributes."gen_ai.response.id" (fallback).
- Must use the LIST endpoint (/api/public/observations?traceId=...)
  because the single-observation GET drops metadata.attributes after a PATCH.

stdlib only (urllib.request, json, uuid, datetime). Zero network calls in pure functions.
"""
from __future__ import annotations

import json
import urllib.request
from typing import Any

from enrich_route import ObservationUpdate

# Fixed ISO timestamp — ingestion requires the field to be present; a constant
# is fine because Langfuse uses the observation's own startTime for display.
_TIMESTAMP = "2026-06-26T00:00:00Z"

# Map semantic field names used by enrich_route to Langfuse body keys.
_FIELD_MAP: dict[str, str] = {
    "input": "input",
    "output": "output",
    "name": "name",
}
_COST_KEY = "cost_usd"


def _parse_request_id_index(data: dict[str, Any]) -> dict[str, str]:
    """Parse the /api/public/observations list response into {request_id: obs_id}.

    Pure function — no network. Exposed for unit testing.

    Args:
        data: Parsed JSON dict from the observations list endpoint.

    Returns:
        Mapping of Anthropic request_id → Langfuse GENERATION observation id.
        Non-GENERATION observations are ignored.
        Falls back to gen_ai.response.id when request_id is absent.
    """
    index: dict[str, str] = {}
    for obs in data.get("data", []):
        if obs.get("type") != "GENERATION":
            continue
        attrs = (obs.get("metadata") or {}).get("attributes") or {}
        rid: str | None = attrs.get("request_id") or attrs.get("gen_ai.response.id")
        oid: str | None = obs.get("id")
        if rid and oid:
            index[rid] = oid
    return index


def build_request_id_index(base: str, auth: str, trace_id: str) -> dict[str, str]:
    """GET the observations list and return {request_id: obs_id} for GENERATION observations.

    Args:
        base: Langfuse base URL, e.g. "https://cloud.langfuse.com".
        auth: HTTP Basic auth header value, e.g. "Basic <b64>".
        trace_id: Hex trace id (32 chars).

    Returns:
        Mapping of Anthropic request_id → Langfuse GENERATION observation id.
    """
    url = f"{base}/api/public/observations?traceId={trace_id}"
    req = urllib.request.Request(url, headers={"Authorization": auth})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data: dict[str, Any] = json.load(resp)
    return _parse_request_id_index(data)


def ingestion_body(updates: list[ObservationUpdate]) -> dict[str, Any]:
    """Build the /api/public/ingestion request body from a list of observation updates.

    Pure function — no network calls.

    Event type is determined by ObservationUpdate.kind:
    - "generation" → "generation-update"
    - "span"        → "span-update"

    Field mapping (enrich_route semantic keys → Langfuse body keys):
    - input    → input
    - output   → output
    - name     → name
    - cost_usd → costDetails: {"total": <value>}

    Fields absent in the update dict are omitted from the body.

    Args:
        updates: List of ObservationUpdate produced by enrich_route.build_updates.

    Returns:
        Dict ready for JSON serialisation and POST to /api/public/ingestion.
    """
    batch = []
    for i, u in enumerate(updates):
        event_type = "generation-update" if u.kind == "generation" else "span-update"
        body: dict[str, Any] = {"id": u.obs_id}

        for src_key, dst_key in _FIELD_MAP.items():
            if src_key in u.fields:
                body[dst_key] = u.fields[src_key]

        if _COST_KEY in u.fields:
            body["costDetails"] = {"total": u.fields[_COST_KEY]}

        batch.append({
            "id": f"m3-{i}-{u.obs_id}",
            "type": event_type,
            "timestamp": _TIMESTAMP,
            "body": body,
        })

    return {"batch": batch}


def post_updates(base: str, auth: str, updates: list[ObservationUpdate]) -> dict[str, Any]:
    """POST observation updates to /api/public/ingestion.

    Args:
        base: Langfuse base URL.
        auth: HTTP Basic auth header value.
        updates: List of ObservationUpdate to POST.

    Returns:
        Parsed JSON response from Langfuse ({"successes": [...], "errors": [...]}).
    """
    payload = json.dumps(ingestion_body(updates)).encode("utf-8")
    req = urllib.request.Request(
        f"{base}/api/public/ingestion",
        data=payload,
        method="POST",
        headers={
            "Authorization": auth,
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)  # type: ignore[no-any-return]
