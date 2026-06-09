from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from custom_components.crypto_portfolio.storage import (  # noqa: E402
    DEFAULT_HOLDINGS_FILENAME,
    holdings_file_display_path,
    holdings_file_path,
    load_or_create_holdings_file,
    read_holdings_file,
    resolve_holdings_filename,
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
        path = holdings_file_path("/config")

        self.assertEqual(
            path,
            Path(
                "/config/custom_components/crypto_portfolio/data/holdings.json"
            ),
        )
        self.assertEqual(
            holdings_file_display_path(),
            "custom_components/crypto_portfolio/data/holdings.json",
        )

    def test_writes_and_reads_holdings_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = holdings_file_path(temp_dir)

            write_holdings_file(path, self.holdings)

            self.assertEqual(read_holdings_file(path), self.holdings)
            self.assertTrue(path.read_text(encoding="utf-8").endswith("\n"))

    def test_load_or_create_preserves_existing_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = holdings_file_path(temp_dir)
            write_holdings_file(path, self.holdings)
            fallback = [{**self.holdings[0], "amount": 99}]

            loaded = load_or_create_holdings_file(path, fallback)

            self.assertEqual(loaded, self.holdings)

    def test_migrates_legacy_entry_id_filename(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            legacy_path = holdings_file_path(temp_dir, "entry-id.json")
            write_holdings_file(legacy_path, self.holdings)

            filename = resolve_holdings_filename(temp_dir, None, "entry-id")

            self.assertEqual(filename, DEFAULT_HOLDINGS_FILENAME)
            self.assertFalse(legacy_path.exists())
            self.assertEqual(
                read_holdings_file(holdings_file_path(temp_dir, filename)),
                self.holdings,
            )

    def test_uses_numbered_filename_for_another_portfolio(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            write_holdings_file(holdings_file_path(temp_dir), self.holdings)

            filename = resolve_holdings_filename(temp_dir, None, "entry-id")

            self.assertEqual(filename, "holdings-2.json")


if __name__ == "__main__":
    unittest.main()
