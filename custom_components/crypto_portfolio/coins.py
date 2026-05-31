"""Coin id normalization helpers."""

from __future__ import annotations

from typing import Any

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


def normalize_coin_id(value: Any) -> str:
    """Normalize a CoinGecko id or a known ticker symbol."""
    raw_value = str(value).strip()
    if not raw_value:
        return ""
    return COIN_SYMBOL_ALIASES.get(raw_value.upper(), raw_value.lower())
