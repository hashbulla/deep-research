"""Tests for enrich_route.py — TDD RED → GREEN.

Posture: reduced surface, fail-closed.
Forbidden in egress: raw messages bodies, tool_input/tool_output bytes, identity PII.
"""
import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from enrich_parse import LogRecord, parse_jsonl
from enrich_redact import _DROP_PLACEHOLDER
from enrich_route import ObservationUpdate, build_updates


class TestUserPromptRouting(unittest.TestCase):
    """user_prompt routes to the GENERATION's input via prompt.id → request_id join.

    Span-update does not persist input on Langfuse Hobby (M3 fix, AI-182 review).
    """

    def _records_with_join(self, prompt: str = "hello") -> list:
        """Minimal record pair that satisfies the prompt.id join."""
        return [
            LogRecord("t" * 32, "iface000000000aa", "user_prompt",
                      {"prompt": prompt, "prompt.id": "pid_0001"}),
            LogRecord("t" * 32, "rootspan00000000", "api_request",
                      {"prompt.id": "pid_0001", "request_id": "req_X", "cost_usd": 0.01}),
        ]

    def test_user_prompt_routes_to_generation_kind(self):
        ups = build_updates(self._records_with_join(), {"req_X": "gen_obs_id_0001"})
        prompt_ups = [u for u in ups if u.fields.get("input") is not None]
        self.assertEqual(len(prompt_ups), 1)
        self.assertEqual(prompt_ups[0].kind, "generation")

    def test_user_prompt_obs_id_is_generation_id(self):
        ups = build_updates(self._records_with_join(), {"req_X": "gen_obs_id_0001"})
        prompt_ups = [u for u in ups if u.fields.get("input") is not None]
        self.assertEqual(prompt_ups[0].obs_id, "gen_obs_id_0001")

    def test_user_prompt_input_field_is_prompt(self):
        ups = build_updates(self._records_with_join("hello"), {"req_X": "gen_obs_id_0001"})
        prompt_ups = [u for u in ups if u.fields.get("input") is not None]
        self.assertEqual(prompt_ups[0].fields["input"], "hello")

    def test_user_prompt_unmapped_promptid_skipped(self):
        """user_prompt whose prompt.id has no matching api_request → no update emitted."""
        recs = [
            LogRecord("t" * 32, "iface000000000aa", "user_prompt",
                      {"prompt": "hello", "prompt.id": "pid_ORPHAN"}),
        ]
        ups = build_updates(recs, {"req_X": "gen_obs_id_0001"})
        # No api_request with pid_ORPHAN → no update for this user_prompt.
        prompt_ups = [u for u in ups if u.fields.get("input") is not None]
        self.assertEqual(prompt_ups, [])

    def test_user_prompt_no_promptid_skipped(self):
        """user_prompt with no prompt.id at all → skipped (cannot join)."""
        recs = [
            LogRecord("t" * 32, "iface000000000aa", "user_prompt", {"prompt": "hello"}),
        ]
        ups = build_updates(recs, {"req_X": "gen_obs_id_0001"})
        prompt_ups = [u for u in ups if u.fields.get("input") is not None]
        self.assertEqual(prompt_ups, [])


class TestApiRequestRouting(unittest.TestCase):
    def test_api_request_mapped_request_id_routes_to_generation(self):
        recs = [LogRecord("t" * 32, "rootspan00000000", "api_request",
                          {"request_id": "req_X", "cost_usd": 0.05})]
        ups = build_updates(recs, {"req_X": "gen_obs_id_0001"})
        self.assertEqual(len(ups), 1)
        self.assertEqual(ups[0].kind, "generation")

    def test_api_request_obs_id_from_lookup_table(self):
        recs = [LogRecord("t" * 32, "rootspan00000000", "api_request",
                          {"request_id": "req_X", "cost_usd": 0.05})]
        ups = build_updates(recs, {"req_X": "gen_obs_id_0001"})
        self.assertEqual(ups[0].obs_id, "gen_obs_id_0001")

    def test_api_request_cost_usd_in_fields(self):
        recs = [LogRecord("t" * 32, "rootspan00000000", "api_request",
                          {"request_id": "req_X", "cost_usd": 0.08})]
        ups = build_updates(recs, {"req_X": "gen_obs_id_0001"})
        self.assertAlmostEqual(ups[0].fields["cost_usd"], 0.08)

    def test_api_request_unmapped_request_id_is_skipped(self):
        recs = [LogRecord("t" * 32, "rootspan00000000", "api_request",
                          {"request_id": "req_UNKNOWN", "cost_usd": 0.05})]
        ups = build_updates(recs, {})
        self.assertEqual(ups, [])

    def test_api_request_no_raw_messages_field(self):
        recs = [LogRecord("t" * 32, "rootspan00000000", "api_request",
                          {"request_id": "req_X", "cost_usd": 0.05, "messages": "[{role:user}]"})]
        ups = build_updates(recs, {"req_X": "gen_obs_id_0001"})
        self.assertNotIn("messages", ups[0].fields)


class TestToolResultRouting(unittest.TestCase):
    def test_tool_result_routes_to_span_kind(self):
        recs = [LogRecord("t" * 32, "span0000000000aa", "tool_result",
                          {"tool_name": "Read", "tool_use_id": "toolu_001"})]
        ups = build_updates(recs, {})
        self.assertEqual(len(ups), 1)
        self.assertEqual(ups[0].kind, "span")

    def test_tool_result_obs_id_is_span_id(self):
        recs = [LogRecord("t" * 32, "span0000000000aa", "tool_result",
                          {"tool_name": "Read", "tool_use_id": "toolu_001"})]
        ups = build_updates(recs, {})
        self.assertEqual(ups[0].obs_id, "span0000000000aa")

    def test_tool_result_fields_contain_name(self):
        recs = [LogRecord("t" * 32, "span0000000000aa", "tool_result",
                          {"tool_name": "Read", "tool_use_id": "toolu_001"})]
        ups = build_updates(recs, {})
        self.assertEqual(ups[0].fields["name"], "Read")

    def test_tool_result_does_not_egress_tool_input(self):
        recs = [LogRecord("t" * 32, "span0000000000aa", "tool_result",
                          {"tool_name": "Read", "tool_input": '{"file_path": "/etc/passwd"}'})]
        ups = build_updates(recs, {})
        self.assertNotIn("input", ups[0].fields)

    def test_tool_result_does_not_egress_tool_output(self):
        recs = [LogRecord("t" * 32, "span0000000000aa", "tool_result",
                          {"tool_name": "Read", "tool_output": "sensitive file contents"})]
        ups = build_updates(recs, {})
        self.assertNotIn("output", ups[0].fields)


class TestAssistantResponseRouting(unittest.TestCase):
    def test_assistant_response_routes_to_generation_output(self):
        """Mapped request_id → generation-kind update with output = sanitized response."""
        recs = [LogRecord("t" * 32, "f1a2b3c4d5e6f708", "assistant_response",
                          {"request_id": "req_X", "response": "synthetic completion: the answer is 42"})]
        ups = build_updates(recs, {"req_X": "gen_obs_id_0001"})
        self.assertEqual(len(ups), 1)
        self.assertEqual(ups[0].kind, "generation")
        self.assertEqual(ups[0].obs_id, "gen_obs_id_0001")
        self.assertEqual(ups[0].fields["output"], "synthetic completion: the answer is 42")

    def test_assistant_response_unmapped_request_skipped(self):
        """Unmapped request_id → no update emitted."""
        recs = [LogRecord("t" * 32, "f1a2b3c4d5e6f708", "assistant_response",
                          {"request_id": "req_UNKNOWN", "response": "something"})]
        ups = build_updates(recs, {})
        self.assertEqual(ups, [])

    def test_assistant_response_output_redacted(self):
        """Response containing a secret → output has the secret masked."""
        recs = [LogRecord("t" * 32, "f1a2b3c4d5e6f708", "assistant_response",
                          {"request_id": "req_X",
                           "response": "here is your key: sk-ant-FAKE0123456789abcdef0123 use it well"})]
        ups = build_updates(recs, {"req_X": "gen_obs_id_0001"})
        self.assertEqual(len(ups), 1)
        self.assertNotIn("sk-ant-FAKE0123456789abcdef0123", ups[0].fields["output"])


class TestToolDecisionIgnored(unittest.TestCase):
    def test_tool_decision_produces_no_update(self):
        recs = [LogRecord("t" * 32, "span0000000000aa", "tool_decision",
                          {"tool_name": "Read", "decision": "accept"})]
        ups = build_updates(recs, {})
        self.assertEqual(ups, [])


class TestFixtureJoin(unittest.TestCase):
    def _fixture_recs_and_rid(self):
        fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "logs-sample.jsonl")
        recs = parse_jsonl(fixture_path)
        rid = next(r.attrs["request_id"] for r in recs if r.event_name == "api_request")
        return recs, rid

    def test_fixture_assistant_response_joins_to_generation(self):
        """Fixture: api_request request_id must match assistant_response request_id for join."""
        recs, rid = self._fixture_recs_and_rid()
        ups = build_updates(recs, {rid: "gen_fixture_1"})
        gen_outputs = [u for u in ups if u.obs_id == "gen_fixture_1" and "output" in u.fields]
        self.assertTrue(gen_outputs, "assistant_response should route output to the generation via request_id join")

    def test_fixture_user_prompt_routes_to_generation_input(self):
        """Fixture: user_prompt.prompt.id → api_request.prompt.id → request_id → generation input."""
        recs, rid = self._fixture_recs_and_rid()
        ups = build_updates(recs, {rid: "gen_fixture_1"})
        gen_inputs = [u for u in ups if u.obs_id == "gen_fixture_1" and "input" in u.fields]
        self.assertTrue(gen_inputs, "user_prompt should route input to the generation via prompt.id join")
        # Verify the secret in the fixture prompt is redacted.
        self.assertNotIn("sk-ant-FAKE0123456789abcdef0123", gen_inputs[0].fields["input"])


class TestRedactionGates(unittest.TestCase):
    def _records_with_join(self, prompt: str) -> list:
        """Minimal record pair that satisfies the prompt.id join for redaction tests."""
        return [
            LogRecord("t" * 32, "iface000000000aa", "user_prompt",
                      {"prompt": prompt, "prompt.id": "pid_0001"}),
            LogRecord("t" * 32, "rootspan00000000", "api_request",
                      {"prompt.id": "pid_0001", "request_id": "req_X", "cost_usd": 0.01}),
        ]

    def test_secret_in_prompt_is_masked(self):
        recs = self._records_with_join("leak sk-ant-FAKE0123456789abcdef0123 please help")
        ups = build_updates(recs, {"req_X": "gen_obs_id_0001"})
        prompt_ups = [u for u in ups if u.fields.get("input") is not None]
        self.assertNotIn("sk-ant-FAKE0123456789abcdef0123", prompt_ups[0].fields["input"])

    def test_pem_in_prompt_triggers_drop(self):
        pem_prompt = "here is my key:\n-----BEGIN PRIVATE KEY-----\nMIIEv...\n-----END PRIVATE KEY-----"
        recs = self._records_with_join(pem_prompt)
        ups = build_updates(recs, {"req_X": "gen_obs_id_0001"})
        prompt_ups = [u for u in ups if u.fields.get("input") is not None]
        self.assertEqual(prompt_ups[0].fields["input"], _DROP_PLACEHOLDER)

    def test_no_update_fields_contain_raw_bodies_keys(self):
        """Regression: forbidden keys must never appear in any update's fields."""
        recs = [
            LogRecord("t" * 32, "iface000000000aa", "user_prompt",
                      {"prompt": "hello", "prompt.id": "pid_0001"}),
            LogRecord("t" * 32, "rootspan00000000", "api_request",
                      {"prompt.id": "pid_0001", "request_id": "req_X",
                       "cost_usd": 0.05, "messages": "raw", "tool_input": "raw", "tool_output": "raw"}),
            LogRecord("t" * 32, "span0000000000aa", "tool_result",
                      {"tool_name": "Read", "tool_input": "raw", "tool_output": "raw"}),
        ]
        ups = build_updates(recs, {"req_X": "gen_obs_id_0001"})
        forbidden = {"messages", "tool_input", "tool_output"}
        for u in ups:
            overlap = forbidden & set(u.fields.keys())
            self.assertFalse(overlap, f"Forbidden key(s) {overlap} found in {u.obs_id} fields")


if __name__ == "__main__":
    unittest.main()
