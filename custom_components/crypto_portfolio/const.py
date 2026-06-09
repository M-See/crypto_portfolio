"""Constants for the Crypto Portfolio integration."""

from datetime import timedelta

DOMAIN = "crypto_portfolio"

CONF_AMOUNT = "amount"
CONF_COIN_ID = "coin_id"
CONF_CURRENCY = "currency"
CONF_HOLDINGS = "holdings"
CONF_HOLDINGS_JSON = "holdings_json"
CONF_INVESTED = "invested"
CONF_SYMBOL = "symbol"

DEFAULT_CURRENCY = "eur"
DEFAULT_NAME = "Crypto Portfolio"
DEFAULT_SCAN_INTERVAL_MINUTES = 10
DEFAULT_SCAN_INTERVAL = timedelta(minutes=DEFAULT_SCAN_INTERVAL_MINUTES)

COINGECKO_SIMPLE_PRICE_URL = "https://api.coingecko.com/api/v3/simple/price"
FRONTEND_CARD_URL = f"/{DOMAIN}/crypto-portfolio-card.js?v=13"
