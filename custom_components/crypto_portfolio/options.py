"""Validation and serialization helpers for portfolio options."""

from __future__ import annotations

from decimal import Decimal
import json
from typing import Any

from .const import CONF_AMOUNT, CONF_COIN_ID, CONF_INVESTED, CONF_SYMBOL
from .portfolio import decimal_value


class HoldingsValidationError(ValueError):
    """Raised when holdings JSON cannot be used."""


DEFAULT_HOLDINGS: list[dict[str, Any]] = [
    {
        CONF_COIN_ID: "bitcoin",
        CONF_SYMBOL: "BTC",
        CONF_AMOUNT: 0.05,
        CONF_INVESTED: 1200,
    },
    {
        CONF_COIN_ID: "ethereum",
        CONF_SYMBOL: "ETH",
        CONF_AMOUNT: 1.2,
        CONF_INVESTED: 2500,
    },
]


def holdings_to_json(holdings: list[dict[str, Any]]) -> str:
    """Serialize holdings for the Home Assistant textarea selector."""
    return json.dumps(holdings, indent=2, ensure_ascii=False)


def normalize_holding(item: dict[str, Any], index: int = 1) -> dict[str, Any]:
    """Validate and normalize one holding."""
    try:
        coin_id = str(item[CONF_COIN_ID]).strip().lower()
        symbol = str(item[CONF_SYMBOL]).strip().upper()
        amount = decimal_value(item[CONF_AMOUNT], CONF_AMOUNT)
        invested = decimal_value(item[CONF_INVESTED], CONF_INVESTED)
    except KeyError as err:
        raise HoldingsValidationError(
            f"Holding {index} is missing {err.args[0]}"
        ) from err
    except ValueError as err:
        raise HoldingsValidationError(f"Holding {index}: {err}") from err

    if not coin_id:
        raise HoldingsValidationError(f"Holding {index}: coin_id is required")
    if not symbol:
        raise HoldingsValidationError(f"Holding {index}: symbol is required")
    if amount < Decimal(0):
        raise HoldingsValidationError(f"Holding {index}: amount must be >= 0")
    if invested < Decimal(0):
        raise HoldingsValidationError(f"Holding {index}: invested must be >= 0")

    return {
        CONF_COIN_ID: coin_id,
        CONF_SYMBOL: symbol,
        CONF_AMOUNT: float(amount),
        CONF_INVESTED: float(invested),
    }


def holdings_from_json(value: str) -> list[dict[str, Any]]:
    """Parse and normalize holdings from the Home Assistant textarea selector."""
    try:
        raw_holdings = json.loads(value)
    except json.JSONDecodeError as err:
        raise HoldingsValidationError("Holdings must be valid JSON") from err

    if not isinstance(raw_holdings, list) or not raw_holdings:
        raise HoldingsValidationError("Holdings must be a non-empty JSON list")

    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(raw_holdings, start=1):
        if not isinstance(item, dict):
            raise HoldingsValidationError(f"Holding {index} must be an object")
        normalized.append(normalize_holding(item, index))

    return normalized
