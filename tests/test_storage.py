from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from custom_components.crypto_portfolio.storage import (  # noqa: E402
    holdings_file_display_path,
    holdings_file_path,
    load_or_create_holdings_file,
    read_holdings_file,
    write_holdings_file,
)


class HoldingsStorageTest(unittest.TestCase):
    def setUp(self) -> None:
        self.holdings = [
            {
                "coin_id": "bitcoin",
                "symbol": "BTC",
                "amount": 0.5,
                "invested": 1000.0,
            }
        ]

    def test_builds_config_relative_entry_path(self) -> None:
        path = holdings_file_path("/config", "entry-id")

        self.assertEqual(
            path,
            Path(
                "/config/custom_components/crypto_portfolio/data/entry-id.json"
            ),
        )
        self.assertEqual(
            holdings_file_display_path("entry-id"),
            "custom_components/crypto_portfolio/data/entry-id.json",
        )

    def test_writes_and_reads_holdings_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = holdings_file_path(temp_dir, "entry-id")

            write_holdings_file(path, self.holdings)

            self.assertEqual(read_holdings_file(path), self.holdings)
            self.assertTrue(path.read_text(encoding="utf-8").endswith("\n"))

    def test_load_or_create_preserves_existing_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = holdings_file_path(temp_dir, "entry-id")
            write_holdings_file(path, self.holdings)
            fallback = [{**self.holdings[0], "amount": 99}]

            loaded = load_or_create_holdings_file(path, fallback)

            self.assertEqual(loaded, self.holdings)


if __name__ == "__main__":
    unittest.main()
