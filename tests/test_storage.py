from __future__ import annotations

import os
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
            Path("/config/crypto_portfolio/holdings.json"),
        )
        self.assertEqual(
            holdings_file_display_path(),
            "crypto_portfolio/holdings.json",
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
            legacy_path = (
                Path(temp_dir)
                / "custom_components"
                / "crypto_portfolio"
                / "data"
                / "entry-id.json"
            )
            write_holdings_file(legacy_path, self.holdings)

            filename = resolve_holdings_filename(temp_dir, None, "entry-id")

            self.assertEqual(filename, DEFAULT_HOLDINGS_FILENAME)
            self.assertFalse(legacy_path.exists())
            self.assertEqual(
                read_holdings_file(holdings_file_path(temp_dir, filename)),
                self.holdings,
            )

    def test_migrates_configured_component_data_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            legacy_path = (
                Path(temp_dir)
                / "custom_components"
                / "crypto_portfolio"
                / "data"
                / DEFAULT_HOLDINGS_FILENAME
            )
            write_holdings_file(legacy_path, self.holdings)

            filename = resolve_holdings_filename(
                temp_dir, DEFAULT_HOLDINGS_FILENAME, "entry-id"
            )

            self.assertEqual(filename, DEFAULT_HOLDINGS_FILENAME)
            self.assertFalse(legacy_path.exists())
            self.assertEqual(
                read_holdings_file(holdings_file_path(temp_dir, filename)),
                self.holdings,
            )

    def test_removes_matching_legacy_id_file_during_migration(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            component_path = (
                Path(temp_dir)
                / "custom_components"
                / "crypto_portfolio"
                / "data"
                / DEFAULT_HOLDINGS_FILENAME
            )
            legacy_id_path = holdings_file_path(temp_dir, "entry-id.json")
            write_holdings_file(component_path, self.holdings)
            write_holdings_file(legacy_id_path, self.holdings)

            resolve_holdings_filename(
                temp_dir, DEFAULT_HOLDINGS_FILENAME, "entry-id"
            )

            self.assertFalse(legacy_id_path.exists())

    def test_removes_matching_component_file_when_target_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            component_path = (
                Path(temp_dir)
                / "custom_components"
                / "crypto_portfolio"
                / "data"
                / DEFAULT_HOLDINGS_FILENAME
            )
            target_path = holdings_file_path(temp_dir)
            write_holdings_file(component_path, self.holdings)
            write_holdings_file(target_path, self.holdings)

            resolve_holdings_filename(
                temp_dir, DEFAULT_HOLDINGS_FILENAME, "entry-id"
            )

            self.assertFalse(component_path.exists())
            self.assertEqual(read_holdings_file(target_path), self.holdings)

    def test_preserves_different_legacy_file_as_migration_backup(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            component_path = (
                Path(temp_dir)
                / "custom_components"
                / "crypto_portfolio"
                / "data"
                / DEFAULT_HOLDINGS_FILENAME
            )
            target_path = holdings_file_path(temp_dir)
            legacy_holdings = [{**self.holdings[0], "amount": 2}]
            write_holdings_file(component_path, legacy_holdings)
            write_holdings_file(target_path, self.holdings)
            os.utime(component_path, (1, 1))

            resolve_holdings_filename(
                temp_dir, DEFAULT_HOLDINGS_FILENAME, "entry-id"
            )

            backup_path = holdings_file_path(
                temp_dir, "holdings-migration-backup.json"
            )
            self.assertFalse(component_path.exists())
            self.assertEqual(read_holdings_file(target_path), self.holdings)
            self.assertEqual(read_holdings_file(backup_path), legacy_holdings)

    def test_newer_legacy_file_becomes_active_and_preserves_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            component_path = (
                Path(temp_dir)
                / "custom_components"
                / "crypto_portfolio"
                / "data"
                / DEFAULT_HOLDINGS_FILENAME
            )
            target_path = holdings_file_path(temp_dir)
            legacy_holdings = [{**self.holdings[0], "amount": 2}]
            write_holdings_file(component_path, legacy_holdings)
            write_holdings_file(target_path, self.holdings)
            os.utime(target_path, (1, 1))

            resolve_holdings_filename(
                temp_dir, DEFAULT_HOLDINGS_FILENAME, "entry-id"
            )

            backup_path = holdings_file_path(
                temp_dir, "holdings-migration-backup.json"
            )
            self.assertFalse(component_path.exists())
            self.assertEqual(read_holdings_file(target_path), legacy_holdings)
            self.assertEqual(read_holdings_file(backup_path), self.holdings)

    def test_uses_numbered_filename_for_another_portfolio(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            write_holdings_file(holdings_file_path(temp_dir), self.holdings)

            filename = resolve_holdings_filename(
                temp_dir, None, "entry-id", {DEFAULT_HOLDINGS_FILENAME}
            )

            self.assertEqual(filename, "holdings-2.json")

    def test_reuses_unclaimed_file_after_reinstall(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            write_holdings_file(holdings_file_path(temp_dir), self.holdings)

            filename = resolve_holdings_filename(temp_dir, None, "new-entry-id")

            self.assertEqual(filename, DEFAULT_HOLDINGS_FILENAME)
            self.assertEqual(
                read_holdings_file(holdings_file_path(temp_dir, filename)),
                self.holdings,
            )

    def test_reuses_unclaimed_numbered_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            write_holdings_file(holdings_file_path(temp_dir), self.holdings)
            numbered_path = holdings_file_path(temp_dir, "holdings-2.json")
            write_holdings_file(numbered_path, self.holdings)

            filename = resolve_holdings_filename(
                temp_dir, None, "new-entry-id", {DEFAULT_HOLDINGS_FILENAME}
            )

            self.assertEqual(filename, "holdings-2.json")


if __name__ == "__main__":
    unittest.main()
