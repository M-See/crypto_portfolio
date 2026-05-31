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

COIN_SYMBOL_ALIASES: dict[str, str] = {
    "1INCH": "1inch",
    "ADA": "cardano",
    "ALGO": "algorand",
    "ANKR": "ankr",
    "APE": "apecoin",
    "ASTR": "astar",
    "ATOM": "cosmos",
    "AUDIO": "audius",
    "BAT": "basic-attention-token",
    "BNB": "binancecoin",
    "BSW": "biswap",
    "BTC": "bitcoin",
    "CAKE": "pancakeswap-token",
    "CHZ": "chiliz",
    "CRV": "curve-dao-token",
    "CTSI": "cartesi",
    "DAI": "dai",
    "DOGE": "dogecoin",
    "DOT": "polkadot",
    "DYDX": "dydx",
    "ENJ": "enjincoin",
    "ETH": "ethereum",
    "FIDA": "bonfida",
    "FIL": "filecoin",
    "FLOW": "flow",
    "GALA": "gala",
    "GLMR": "moonbeam",
    "GRT": "the-graph",
    "ICX": "icon",
    "KEEP": "keep-network",
    "KIN": "kin",
    "KSM": "kusama",
    "LINK": "chainlink",
    "LRC": "loopring",
    "LTC": "litecoin",
    "MANA": "decentraland",
    "MNGO": "mango-markets",
    "NANO": "nano",
    "OCEAN": "ocean-protocol",
    "OGN": "origin-protocol",
    "OMG": "omisego",
    "OXT": "orchid-protocol",
    "OXY": "oxygen",
    "QNT": "quant-network",
    "REN": "republic-protocol",
    "SAND": "the-sandbox",
    "SBR": "saber",
    "SC": "siacoin",
    "SDN": "shiden",
    "SGB": "songbird",
    "SHIB": "shiba-inu",
    "SOL": "solana",
    "SPELL": "spell-token",
    "STORJ": "storj",
    "SUSHI": "sushi",
    "TON": "toncoin",
    "TRX": "tron",
    "USDC": "usd-coin",
    "USDT": "tether",
    "XLM": "stellar",
    "XMR": "monero",
    "XNO": "nano",
    "XRP": "ripple",
    "XVG": "verge",
}


def holdings_to_json(holdings: list[dict[str, Any]]) -> str:
    """Serialize holdings for the Home Assistant textarea selector."""
    return json.dumps(holdings, indent=2, ensure_ascii=False)


def normalize_coin_id(value: Any) -> str:
    """Normalize a CoinGecko id or a known ticker symbol."""
    raw_value = str(value).strip()
    if not raw_value:
        return ""
    return COIN_SYMBOL_ALIASES.get(raw_value.upper(), raw_value.lower())


def normalize_holding(item: dict[str, Any], index: int = 1) -> dict[str, Any]:
    """Validate and normalize one holding."""
    try:
        coin_id = normalize_coin_id(item[CONF_COIN_ID])
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
