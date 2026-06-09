"""JSON file storage helpers for portfolio holdings."""

from __future__ import annotations

from collections.abc import Collection
from pathlib import Path
import shutil
from typing import Any

from .const import DOMAIN
from .options import HoldingsValidationError, holdings_from_json, holdings_to_json

DEFAULT_HOLDINGS_FILENAME = "holdings.json"


def holdings_data_dir(config_dir: str) -> Path:
    """Return the directory containing portfolio JSON files."""
    return Path(config_dir) / DOMAIN


def holdings_file_path(
    config_dir: str, filename: str = DEFAULT_HOLDINGS_FILENAME
) -> Path:
    """Return the JSON file path for one config entry."""
    return holdings_data_dir(config_dir) / filename


def holdings_file_display_path(
    filename: str = DEFAULT_HOLDINGS_FILENAME,
) -> str:
    """Return the config-relative path shown in the File editor."""
    return f"{DOMAIN}/{filename}"


def _is_valid_filename(filename: str | None) -> bool:
    """Return whether a stored holdings filename is safe to use."""
    return bool(
        filename
        and Path(filename).name == filename
        and filename.endswith(".json")
    )


def resolve_holdings_filename(
    config_dir: str,
    configured_filename: str | None,
    legacy_entry_id: str,
    reserved_filenames: Collection[str] = (),
) -> str:
    """Return an unclaimed filename and migrate legacy ID-based files."""
    data_dir = holdings_data_dir(config_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    component_data_dir = (
        Path(config_dir) / "custom_components" / DOMAIN / "data"
    )

    if _is_valid_filename(configured_filename):
        target_path = data_dir / configured_filename
        if target_path.exists():
            return configured_filename

        configured_legacy_path = component_data_dir / configured_filename
        if configured_legacy_path.exists():
            shutil.move(configured_legacy_path, target_path)
            legacy_id_path = data_dir / f"{legacy_entry_id}.json"
            if (
                legacy_id_path.exists()
                and legacy_id_path.read_bytes() == target_path.read_bytes()
            ):
                legacy_id_path.unlink()
        return configured_filename

    legacy_paths = [
        component_data_dir / f"{legacy_entry_id}.json",
        data_dir / f"{legacy_entry_id}.json",
    ]
    legacy_path = next((path for path in legacy_paths if path.exists()), None)

    index = 1
    while True:
        filename = (
            DEFAULT_HOLDINGS_FILENAME
            if index == 1
            else f"holdings-{index}.json"
        )
        if filename in reserved_filenames:
            index += 1
            continue

        path = data_dir / filename
        if legacy_path is None:
            # Reuse an orphaned file after a config entry was removed and
            # recreated. load_or_create_holdings_file creates it when absent.
            return filename

        if not path.exists():
            shutil.move(legacy_path, path)
            return filename
        index += 1


def read_holdings_text(path: Path) -> str:
    """Read holdings JSON text from a file."""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeError as err:
        raise HoldingsValidationError("Holdings file must be UTF-8") from err


def read_holdings_file(path: Path) -> list[dict[str, Any]]:
    """Read and validate holdings from a JSON file."""
    return holdings_from_json(read_holdings_text(path))


def write_holdings_file(path: Path, holdings: list[dict[str, Any]]) -> None:
    """Write holdings atomically to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(".json.tmp")
    temporary_path.write_text(f"{holdings_to_json(holdings)}\n", encoding="utf-8")
    temporary_path.replace(path)


def load_or_create_holdings_file(
    path: Path, fallback_holdings: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Load an existing holdings file or create it from current options."""
    if path.exists():
        return read_holdings_file(path)

    write_holdings_file(path, fallback_holdings)
    return fallback_holdings
