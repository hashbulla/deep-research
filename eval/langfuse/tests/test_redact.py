import unittest
from enrich_redact import redact, strip_identity, fail_closed

_DROP_PLACEHOLDER = "[REDACTED: dropped — possible secret]"


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

    # --- NEW TESTS (RED phase) ---

    def test_masks_lowercase_akia(self):
        """(?i) fix: lowercased AKIA-shaped token must be masked."""
        out = redact("creds: akiaiosfodnn7example123456")
        self.assertNotIn("akiaiosfodnn7example", out)
        self.assertIn("REDACTED", out)

    def test_masks_fr_phone(self):
        """Synthetic FR number must be masked — never use a real number."""
        out = redact("contact: +33 6 00 00 00 00 end")
        self.assertNotIn("+33 6 00 00 00 00", out)
        self.assertIn("REDACTED", out)

    def test_masks_new_families(self):
        """Google, Slack, Stripe live key, and PEM header are each masked."""
        google = "AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ1234567"
        slack = "xoxb-faketokenforredactiontest"
        stripe = "sk_live_fakekeyforredacttest"
        pem = "-----BEGIN RSA PRIVATE KEY-----"

        self.assertIn("REDACTED", redact(google), "Google API key not masked")
        self.assertIn("REDACTED", redact(slack), "Slack token not masked")
        self.assertIn("REDACTED", redact(stripe), "Stripe live key not masked")
        self.assertIn("REDACTED", redact(pem), "PEM header not masked")

    def test_strip_identity_recursive(self):
        """Identity keys must be dropped at any nesting depth."""
        obj = {
            "outer": {"user.email": "x@y.com", "keep": 1},
            "list": [{"organization.id": "o", "safe": "yes"}],
        }
        out = strip_identity(obj)
        self.assertNotIn("user.email", out["outer"])
        self.assertEqual(out["outer"]["keep"], 1)
        self.assertNotIn("organization.id", out["list"][0])
        self.assertEqual(out["list"][0]["safe"], "yes")

    def test_fail_closed_drops_pem(self):
        """fail_closed must drop a PEM-bearing string but leave normal prose alone."""
        pem_input = "config: -----BEGIN OPENSSH PRIVATE KEY----- blah"
        redacted_first = redact(pem_input)
        result = fail_closed(redacted_first)
        self.assertEqual(result, _DROP_PLACEHOLDER)

        normal = "normal research text about kubernetes"
        self.assertEqual(fail_closed(normal), normal)


if __name__ == "__main__":
    unittest.main()
