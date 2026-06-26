"""Tests for enrich_route.py — TDD RED → GREEN.

Posture: reduced surface, fail-closed.
Forbidden in egress: raw messages bodies, tool_input/tool_output bytes, identity PII.
"""
import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from enrich_parse import LogRecord
from enrich_redact import _DROP_PLACEHOLDER
from enrich_route import ObservationUpdate, build_updates


class TestUserPromptRouting(unittest.TestCase):
    def test_user_prompt_routes_to_span_kind(self):
        recs = [LogRecord("t" * 32, "iface000000000aa", "user_prompt", {"prompt": "hello"})]
        ups = build_updates(recs, {})
        self.assertEqual(len(ups), 1)
        self.assertEqual(ups[0].kind, "span")

    def test_user_prompt_obs_id_is_span_id(self):
        recs = [LogRecord("t" * 32, "iface000000000aa", "user_prompt", {"prompt": "hello"})]
        ups = build_updates(recs, {})
        self.assertEqual(ups[0].obs_id, "iface000000000aa")

    def test_user_prompt_input_field_is_prompt(self):
        recs = [LogRecord("t" * 32, "iface000000000aa", "user_prompt", {"prompt": "hello"})]
        ups = build_updates(recs, {})
        self.assertEqual(ups[0].fields["input"], "hello")


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


class TestToolDecisionIgnored(unittest.TestCase):
    def test_tool_decision_produces_no_update(self):
        recs = [LogRecord("t" * 32, "span0000000000aa", "tool_decision",
                          {"tool_name": "Read", "decision": "accept"})]
        ups = build_updates(recs, {})
        self.assertEqual(ups, [])


class TestRedactionGates(unittest.TestCase):
    def test_secret_in_prompt_is_masked(self):
        recs = [LogRecord("t" * 32, "iface000000000aa", "user_prompt",
                          {"prompt": "leak sk-ant-FAKE0123456789abcdef0123 please help"})]
        ups = build_updates(recs, {})
        self.assertNotIn("sk-ant-FAKE0123456789abcdef0123", ups[0].fields["input"])

    def test_pem_in_prompt_triggers_drop(self):
        pem_prompt = "here is my key:\n-----BEGIN PRIVATE KEY-----\nMIIEv...\n-----END PRIVATE KEY-----"
        recs = [LogRecord("t" * 32, "iface000000000aa", "user_prompt", {"prompt": pem_prompt})]
        ups = build_updates(recs, {})
        self.assertEqual(ups[0].fields["input"], _DROP_PLACEHOLDER)

    def test_no_update_fields_contain_raw_bodies_keys(self):
        """Regression: forbidden keys must never appear in any update's fields."""
        recs = [
            LogRecord("t" * 32, "iface000000000aa", "user_prompt", {"prompt": "hello"}),
            LogRecord("t" * 32, "rootspan00000000", "api_request",
                      {"request_id": "req_X", "cost_usd": 0.05, "messages": "raw", "tool_input": "raw", "tool_output": "raw"}),
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
