"""JSON file storage helpers for portfolio holdings."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .const import DOMAIN
from .options import HoldingsValidationError, holdings_from_json, holdings_to_json


def holdings_file_path(config_dir: str, entry_id: str) -> Path:
    """Return the JSON file path for one config entry."""
    return Path(config_dir) / DOMAIN / f"{entry_id}.json"


def holdings_file_display_path(entry_id: str) -> str:
    """Return the config-relative path shown in the File editor."""
    return f"{DOMAIN}/{entry_id}.json"


def read_holdings_file(path: Path) -> list[dict[str, Any]]:
    """Read and validate holdings from a JSON file."""
    try:
        value = path.read_text(encoding="utf-8")
    except UnicodeError as err:
        raise HoldingsValidationError("Holdings file must be UTF-8") from err
    return holdings_from_json(value)


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
