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
        """Google, Slack, Stripe live key are each MASK-tier (field kept, secret replaced).
        PEM is now a DROP-tier family — assert fail_closed drops it, not redact()."""
        google = "AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ1234567"
        slack = "xoxb-faketokenforredactiontest"
        stripe = "sk_live_fakekeyforredacttest"
        pem_raw = "-----BEGIN RSA PRIVATE KEY-----"

        self.assertIn("REDACTED", redact(google), "Google API key not masked")
        self.assertIn("REDACTED", redact(slack), "Slack token not masked")
        self.assertIn("REDACTED", redact(stripe), "Stripe live key not masked")
        # PEM is DROP-tier: fail_closed on the raw value must drop the whole field.
        self.assertEqual(fail_closed(pem_raw), _DROP_PLACEHOLDER, "PEM raw not dropped by fail_closed")

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
        """fail_closed on a RAW PEM-bearing string must drop it; normal prose untouched."""
        pem_input = "config -----BEGIN OPENSSH PRIVATE KEY----- xyz"
        self.assertEqual(fail_closed(pem_input), _DROP_PLACEHOLDER)

        normal = "normal research text about kubernetes"
        self.assertEqual(fail_closed(normal), normal)

    def test_fail_closed_masks_email_keeps_field(self):
        """Regression: a benign field containing only an email must be MASKED (field kept),
        not dropped — the over-drop bug from the _MASK-sentinel design."""
        out = fail_closed("please email bob@example.com today")
        self.assertNotEqual(out, _DROP_PLACEHOLDER, "field was dropped — over-drop regression")
        self.assertNotIn("bob@example.com", out, "email was not masked")

    def test_fail_closed_drops_bearer(self):
        """A Bearer token assignment string must cause fail_closed to drop the whole field."""
        bearer_raw = "Authorization: Bearer abcdef0123456789abcd"
        self.assertEqual(fail_closed(bearer_raw), _DROP_PLACEHOLDER)

    def test_fail_closed_drops_nested_high_severity(self):
        """fail_closed on nested structures must recursively drop high-severity secrets."""
        out = fail_closed({"auth": {"token": "Bearer abcdef0123456789abcd"}})
        self.assertEqual(out["auth"]["token"], _DROP_PLACEHOLDER)

    def test_masks_github_fine_grained_pat(self):
        """GitHub fine-grained PATs (github_pat_*) must be masked."""
        out = redact("token github_pat_11ABCDE0123456789abcdefgh")
        self.assertNotIn("github_pat_11ABCDE0123456789abcdefgh", out)
        self.assertIn("REDACTED", out)


if __name__ == "__main__":
    unittest.main()
