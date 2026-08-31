"""TDD tests for enrich_langfuse — pure-function coverage only (no live network)."""
import sys
import os
import unittest

# Ensure the parent langfuse dir is on path so imports resolve without install.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from enrich_route import ObservationUpdate
from enrich_langfuse import ingestion_body, _parse_request_id_index


class TestIngestionBodyGenerationUpdate(unittest.TestCase):
    """generation-update event type + field mapping."""

    def test_event_type_is_generation_update(self) -> None:
        ups = [ObservationUpdate("obs1", "generation", {"output": "hi", "cost_usd": 0.05})]
        body = ingestion_body(ups)
        ev = body["batch"][0]
        self.assertEqual(ev["type"], "generation-update")

    def test_body_id_matches_obs_id(self) -> None:
        ups = [ObservationUpdate("obs1", "generation", {"output": "hi", "cost_usd": 0.05})]
        ev = ingestion_body(ups)["batch"][0]
        self.assertEqual(ev["body"]["id"], "obs1")

    def test_output_field_passed_through(self) -> None:
        ups = [ObservationUpdate("obs1", "generation", {"output": "hi", "cost_usd": 0.05})]
        ev = ingestion_body(ups)["batch"][0]
        self.assertEqual(ev["body"]["output"], "hi")

    def test_cost_usd_mapped_to_cost_details(self) -> None:
        ups = [ObservationUpdate("obs1", "generation", {"output": "hi", "cost_usd": 0.05})]
        ev = ingestion_body(ups)["batch"][0]
        self.assertEqual(ev["body"]["costDetails"], {"total": 0.05})
        self.assertNotIn("cost_usd", ev["body"])

    def test_event_has_id_and_timestamp(self) -> None:
        ups = [ObservationUpdate("obs1", "generation", {"output": "hi"})]
        ev = ingestion_body(ups)["batch"][0]
        self.assertIn("id", ev)
        self.assertIn("timestamp", ev)
        self.assertTrue(ev["timestamp"])  # non-empty string


class TestIngestionBodySpanUpdate(unittest.TestCase):
    """span-update event type."""

    def test_event_type_is_span_update(self) -> None:
        ups = [ObservationUpdate("span1", "span", {"name": "Read"})]
        ev = ingestion_body(ups)["batch"][0]
        self.assertEqual(ev["type"], "span-update")

    def test_body_id_matches_obs_id(self) -> None:
        ups = [ObservationUpdate("span1", "span", {"name": "Read"})]
        ev = ingestion_body(ups)["batch"][0]
        self.assertEqual(ev["body"]["id"], "span1")


class TestIngestionBodyOmitsAbsentFields(unittest.TestCase):
    """Fields not in the update dict must not appear in the body."""

    def test_name_only_no_output_input_costdetails(self) -> None:
        ups = [ObservationUpdate("span2", "span", {"name": "Read"})]
        body_ev = ingestion_body(ups)["batch"][0]["body"]
        self.assertEqual(body_ev["name"], "Read")
        self.assertNotIn("output", body_ev)
        self.assertNotIn("input", body_ev)
        self.assertNotIn("costDetails", body_ev)

    def test_input_field_passed_through(self) -> None:
        ups = [ObservationUpdate("obs2", "generation", {"input": "hello"})]
        body_ev = ingestion_body(ups)["batch"][0]["body"]
        self.assertEqual(body_ev["input"], "hello")
        self.assertNotIn("output", body_ev)


class TestRequestIdIndexParsing(unittest.TestCase):
    """_parse_request_id_index: sample list-endpoint response → {request_id: obs_id}."""

    SAMPLE_RESPONSE = {
        "data": [
            {
                "id": "gen-obs-1",
                "type": "GENERATION",
                "metadata": {
                    "attributes": {
                        "request_id": "req_ABC123",
                        "gen_ai.response.id": "req_ABC123",
                    }
                },
            },
            {
                # Non-generation observation — must be ignored.
                "id": "span-obs-1",
                "type": "SPAN",
                "metadata": {
                    "attributes": {"request_id": "req_SHOULD_NOT_APPEAR"}
                },
            },
            {
                "id": "gen-obs-2",
                "type": "GENERATION",
                "metadata": {
                    "attributes": {
                        # Fallback: no request_id, use gen_ai.response.id.
                        "gen_ai.response.id": "req_DEF456",
                    }
                },
            },
        ]
    }

    def test_generation_request_id_mapped(self) -> None:
        idx = _parse_request_id_index(self.SAMPLE_RESPONSE)
        self.assertEqual(idx["req_ABC123"], "gen-obs-1")

    def test_span_observations_ignored(self) -> None:
        idx = _parse_request_id_index(self.SAMPLE_RESPONSE)
        self.assertNotIn("req_SHOULD_NOT_APPEAR", idx)

    def test_fallback_to_gen_ai_response_id(self) -> None:
        idx = _parse_request_id_index(self.SAMPLE_RESPONSE)
        self.assertEqual(idx["req_DEF456"], "gen-obs-2")

    def test_empty_data_returns_empty_dict(self) -> None:
        idx = _parse_request_id_index({"data": []})
        self.assertEqual(idx, {})


if __name__ == "__main__":
    unittest.main()
