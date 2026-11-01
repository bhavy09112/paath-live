"""Regression cases for preventing accidental credential commits."""

import importlib.util
import unittest
from pathlib import Path


spec = importlib.util.spec_from_file_location(
    "check_secrets", Path(__file__).resolve().parents[1] / "scripts" / "check-secrets.py"
)
check_secrets = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_secrets)


class CredentialHygieneTests(unittest.TestCase):
    def test_common_provider_tokens_detected_without_disclosure(self):
        tokens = ["sk_" + "aB1_" * 8, "AIza" + "aB1_" * 9, "ghp_" + "aB1" * 12]
        for token in tokens:
            with self.subTest(provider_prefix=token[:3]):
                findings = check_secrets.scan_text("config\nAPI_KEY=" + token)
                self.assertEqual(findings[0][0], 2)
                self.assertNotIn(token, repr(findings))

    def test_placeholder_and_environment_reference_are_safe(self):
        text = 'SARVAM_API_KEY=\nGEMINI_API_KEY=\nkey=os.getenv("SARVAM_API_KEY")\n' + "sk_" + "x" * 30
        self.assertEqual(check_secrets.scan_text(text), [])

    def test_private_key_header_detected(self):
        text = "-----BEGIN " + "PRIVATE KEY-----"
        self.assertEqual(check_secrets.scan_text(text), [(1, "private key")])


if __name__ == "__main__":
    unittest.main()
