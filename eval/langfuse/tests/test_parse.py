import os, json, tempfile, unittest
from enrich_parse import parse_jsonl, LogRecord

FIX = os.path.join(os.path.dirname(__file__), "fixtures", "logs-sample.jsonl")

class TestParse(unittest.TestCase):
    def test_extracts_records_with_ids_and_attrs(self):
        recs = parse_jsonl(FIX)
        self.assertTrue(any(r.event_name == "user_prompt" for r in recs))
        up = next(r for r in recs if r.event_name == "user_prompt")
        self.assertRegex(up.trace_id, r"^[0-9a-f]{32}$")
        self.assertRegex(up.span_id, r"^[0-9a-f]{16}$")
        self.assertIn("prompt", up.attrs)

    def test_malformed_line_skipped_valid_line_returned(self):
        """A JSONL with one garbage line + one valid line must not raise and must return the valid record."""
        valid = {
            "resourceLogs": [{
                "scopeLogs": [{
                    "logRecords": [{
                        "traceId": "a" * 32,
                        "spanId": "b" * 16,
                        "attributes": [
                            {"key": "event.name", "value": {"stringValue": "user_prompt"}},
                            {"key": "prompt", "value": {"stringValue": "hello"}},
                        ],
                    }]
                }]
            }]
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write("NOT VALID JSON\n")
            f.write(json.dumps(valid) + "\n")
            path = f.name
        try:
            recs = parse_jsonl(path)
            self.assertEqual(len(recs), 1)
            self.assertEqual(recs[0].event_name, "user_prompt")
        finally:
            os.unlink(path)

if __name__ == "__main__":
    unittest.main()
