"""CoinGecko API helpers."""

from __future__ import annotations

from typing import Any

from aiohttp import ClientSession

from .const import COINGECKO_SIMPLE_PRICE_URL


async def async_fetch_prices(
    session: ClientSession,
    coin_ids: list[str],
    currency: str,
) -> dict[str, dict[str, Any]]:
    """Fetch current prices from CoinGecko."""
    params = {
        "ids": ",".join(sorted(set(coin_ids))),
        "vs_currencies": currency.lower(),
        "include_24hr_change": "true",
    }

    async with session.get(COINGECKO_SIMPLE_PRICE_URL, params=params) as response:
        response.raise_for_status()
        data = await response.json()

    if not isinstance(data, dict):
        raise ValueError("CoinGecko returned an unexpected response")

    return data
