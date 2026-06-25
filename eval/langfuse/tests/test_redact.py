import unittest
from enrich_redact import redact, strip_identity

class TestRedact(unittest.TestCase):
    def test_masks_secret_and_email(self):
        s = "key sk-ant-FAKE0123456789abcdef0123 mail canary@example.com end"
        out = redact(s)
        self.assertNotIn("sk-ant-FAKE0123456789abcdef0123", out)
        self.assertNotIn("canary@example.com", out)
        self.assertIn("REDACTED", out)

    def test_masks_lowercase_tail(self):
        self.assertNotIn("deadbeef", redact("sk-ant-ABCDEF0123456789deadbeef"))

    def test_strip_identity_drops_pii_keys(self):
        attrs = {"user.email": "x@y.com", "organization.id": "org", "prompt": "keep"}
        out = strip_identity(attrs)
        self.assertNotIn("user.email", out)
        self.assertNotIn("organization.id", out)
        self.assertEqual(out["prompt"], "keep")

if __name__ == "__main__":
    unittest.main()
