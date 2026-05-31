from __future__ import annotations

from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from custom_components.crypto_portfolio.const import (  # noqa: E402
    CONF_AMOUNT,
    CONF_COIN_ID,
    CONF_INVESTED,
    CONF_SYMBOL,
)
from custom_components.crypto_portfolio.coins import normalize_coin_id  # noqa: E402
from custom_components.crypto_portfolio.options import (  # noqa: E402
    HoldingsValidationError,
    holdings_from_json,
    holdings_to_json,
)


class HoldingsOptionsTest(unittest.TestCase):
    def test_round_trips_holdings_json(self) -> None:
        holdings = [
            {
                CONF_COIN_ID: "Bitcoin",
                CONF_SYMBOL: "btc",
                CONF_AMOUNT: "0.5",
                CONF_INVESTED: "1000",
            }
        ]

        parsed = holdings_from_json(holdings_to_json(holdings))

        self.assertEqual(parsed[0][CONF_COIN_ID], "bitcoin")
        self.assertEqual(parsed[0][CONF_SYMBOL], "BTC")
        self.assertEqual(parsed[0][CONF_AMOUNT], 0.5)
        self.assertEqual(parsed[0][CONF_INVESTED], 1000.0)

    def test_rejects_invalid_json(self) -> None:
        with self.assertRaises(HoldingsValidationError):
            holdings_from_json("{not-json")

    def test_rejects_negative_amounts(self) -> None:
        with self.assertRaises(HoldingsValidationError):
            holdings_from_json(
                """
                [
                  {
                    "coin_id": "bitcoin",
                    "symbol": "BTC",
                    "amount": -1,
                    "invested": 1000
                  }
                ]
                """
            )

    def test_known_symbols_are_accepted_as_coin_ids(self) -> None:
        self.assertEqual(normalize_coin_id("BTC"), "bitcoin")
        self.assertEqual(normalize_coin_id("eth"), "ethereum")
        self.assertEqual(normalize_coin_id("cardano"), "cardano")

        parsed = holdings_from_json(
            """
            [
              {
                "coin_id": "BTC",
                "symbol": "BTC",
                "amount": 0.1,
                "invested": 500
              }
            ]
            """
        )

        self.assertEqual(parsed[0][CONF_COIN_ID], "bitcoin")


if __name__ == "__main__":
    unittest.main()
