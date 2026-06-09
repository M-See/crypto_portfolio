"""JSON file storage helpers for portfolio holdings."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .const import DOMAIN
from .options import HoldingsValidationError, holdings_from_json, holdings_to_json

DEFAULT_HOLDINGS_FILENAME = "holdings.json"


def holdings_data_dir(config_dir: str) -> Path:
    """Return the directory containing portfolio JSON files."""
    return Path(config_dir) / "custom_components" / DOMAIN / "data"


def holdings_file_path(
    config_dir: str, filename: str = DEFAULT_HOLDINGS_FILENAME
) -> Path:
    """Return the JSON file path for one config entry."""
    return holdings_data_dir(config_dir) / filename


def holdings_file_display_path(
    filename: str = DEFAULT_HOLDINGS_FILENAME,
) -> str:
    """Return the config-relative path shown in the File editor."""
    return f"custom_components/{DOMAIN}/data/{filename}"


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
) -> str:
    """Return a simple unique filename and migrate legacy ID-based files."""
    if _is_valid_filename(configured_filename):
        return configured_filename

    data_dir = holdings_data_dir(config_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    legacy_paths = [
        data_dir / f"{legacy_entry_id}.json",
        Path(config_dir) / DOMAIN / f"{legacy_entry_id}.json",
    ]
    legacy_path = next((path for path in legacy_paths if path.exists()), None)

    index = 1
    while True:
        filename = (
            DEFAULT_HOLDINGS_FILENAME
            if index == 1
            else f"holdings-{index}.json"
        )
        path = data_dir / filename
        if not path.exists():
            if legacy_path is not None:
                legacy_path.replace(path)
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
