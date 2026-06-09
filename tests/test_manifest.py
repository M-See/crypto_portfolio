from __future__ import annotations

import json
from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = (
    PROJECT_ROOT / "custom_components" / "crypto_portfolio" / "manifest.json"
)


class ManifestTest(unittest.TestCase):
    def test_frontend_is_a_setup_dependency(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

        self.assertIn("frontend", manifest["dependencies"])
        self.assertIn("lovelace", manifest["dependencies"])


if __name__ == "__main__":
    unittest.main()
