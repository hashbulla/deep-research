import os, unittest
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

if __name__ == "__main__":
    unittest.main()
