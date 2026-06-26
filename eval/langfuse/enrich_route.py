"""Route content log records to Langfuse observation updates.

Posture: reduced surface + fail-closed (POSTURE AMENDMENT 2026-06-26).

Egress routing table:
- user_prompt        → generation update: {input: SANITIZE(prompt)}
                       Join: user_prompt.prompt.id → api_request.prompt.id → request_id
                       → generation observation id.  If the join fails (unmapped
                       prompt.id), the record is SKIPPED — span-update does not
                       persist input on Langfuse Hobby.
- api_request        → generation update (if request_id mapped): {cost_usd: <float>}
- assistant_response → generation update (if request_id mapped): {output: SANITIZE(response)}
                       Claude Code emits a clean `response` attribute on this event —
                       no raw API body needed. output is sanitized via fail_closed.
- tool_result        → span update: {name: tool_name} — tool I/O bytes NOT egressed.
- tool_decision      → ignored (name already in tool_result; avoiding duplicate name updates).

SANITIZE(x) = sanitize(x) — strip_identity (recursive dict key drop) then fail_closed (drop/mask).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from enrich_redact import sanitize


@dataclass
class ObservationUpdate:
    obs_id: str
    kind: str        # 'generation' | 'span' — Task 6 emits generation-update vs span-update
    fields: dict = field(default_factory=dict)


def build_updates(records: list, request_id_to_obs: dict) -> list[ObservationUpdate]:
    """Map log records to observation updates, applying the egress gate on every value.

    Args:
        records: List of LogRecord from enrich_parse.parse_jsonl.
        request_id_to_obs: Maps api_request.request_id → generation observation id.
                           Built by Task 6 from the Langfuse trace structure.

    Returns:
        List of ObservationUpdate ready for Task 6 to POST.
    """
    updates: list[ObservationUpdate] = []

    # Build promptid_to_requestid from api_request records that carry both fields.
    # This join is needed to route user_prompt → generation input (M3 fix).
    promptid_to_requestid: dict[str, str] = {}
    for r in records:
        if r.event_name == "api_request":
            pid = r.attrs.get("prompt.id", "")
            rid = r.attrs.get("request_id", "")
            if pid and rid:
                promptid_to_requestid[pid] = rid

    for r in records:
        if r.event_name == "user_prompt":
            # Join: prompt.id → request_id → generation obs id.
            # span-update does NOT persist input on Langfuse Hobby, so we target
            # the generation's input field instead.  If the join fails, skip —
            # there is no reliable fallback that renders.
            pid = r.attrs.get("prompt.id", "")
            rid = promptid_to_requestid.get(pid, "")
            obs_id = request_id_to_obs.get(rid, "")
            if not obs_id:
                continue
            prompt_raw = r.attrs.get("prompt", "")
            updates.append(ObservationUpdate(
                obs_id=obs_id,
                kind="generation",
                fields={"input": sanitize(prompt_raw)},
            ))

        elif r.event_name == "api_request":
            obs_id = request_id_to_obs.get(r.attrs.get("request_id", ""))
            if not obs_id:
                # Unmapped request — skip; don't guess the observation id.
                continue
            fields: dict = {}
            cost = r.attrs.get("cost_usd")
            if cost is not None:
                # cost_usd is numeric — gate-exempt; no string redaction needed.
                fields["cost_usd"] = cost
            # Completion text: not egressed.
            # The Claude Code OTEL records have no completion/response attribute
            # at the top-level attrs; it only exists inside raw Messages API
            # bodies which are forbidden under the reduced-surface posture.
            if fields:
                updates.append(ObservationUpdate(
                    obs_id=obs_id,
                    kind="generation",
                    fields=fields,
                ))

        elif r.event_name == "assistant_response":
            obs_id = request_id_to_obs.get(r.attrs.get("request_id", ""))
            if not obs_id:
                # Unmapped request — skip; don't guess the observation id.
                continue
            response_raw = r.attrs.get("response", "")
            updates.append(ObservationUpdate(
                obs_id=obs_id,
                kind="generation",
                fields={"output": sanitize(response_raw)},
            ))

        elif r.event_name == "tool_result":
            # Egress: tool name only. tool_input / tool_output bytes are forbidden.
            tool_name = r.attrs.get("tool_name", "")
            updates.append(ObservationUpdate(
                obs_id=r.span_id,
                kind="span",
                fields={"name": sanitize(tool_name)},
            ))

        # tool_decision: ignored — name already captured via tool_result.
        # Unknown event names: silently skipped (forward-compatible).

    return updates
