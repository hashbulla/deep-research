"""Route content log records to Langfuse observation updates.

Posture: reduced surface + fail-closed (POSTURE AMENDMENT 2026-06-26).

Egress routing table:
- user_prompt  → span update: {input: SANITIZE(prompt)}
- api_request  → generation update (if request_id mapped): {cost_usd: <float>}
                 Completion text is NOT egressed — the Claude Code OTEL records
                 do not carry a completion/response field outside raw API bodies,
                 and raw bodies are forbidden under the reduced-surface posture.
                 Status: DONE_WITH_CONCERNS — traces show prompt + cost + tool names,
                 no completion text under this posture.
- tool_result  → span update: {name: tool_name} — tool I/O bytes NOT egressed.
- tool_decision → ignored (name already in tool_result; avoiding duplicate name updates).

SANITIZE(x) = fail_closed(x) for plain strings.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from enrich_redact import fail_closed


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

    for r in records:
        if r.event_name == "user_prompt":
            prompt_raw = r.attrs.get("prompt", "")
            updates.append(ObservationUpdate(
                obs_id=r.span_id,
                kind="span",
                fields={"input": fail_closed(prompt_raw)},
            ))

        elif r.event_name == "api_request":
            obs_id = request_id_to_obs.get(r.attrs.get("request_id", ""))
            if not obs_id:
                # Unmapped request — skip; don't guess the observation id.
                continue
            fields: dict = {}
            cost = r.attrs.get("cost_usd")
            if cost is not None:
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

        elif r.event_name == "tool_result":
            # Egress: tool name only. tool_input / tool_output bytes are forbidden.
            tool_name = r.attrs.get("tool_name", "")
            updates.append(ObservationUpdate(
                obs_id=r.span_id,
                kind="span",
                fields={"name": tool_name},
            ))

        # tool_decision: ignored — name already captured via tool_result.
        # Unknown event names: silently skipped (forward-compatible).

    return updates
