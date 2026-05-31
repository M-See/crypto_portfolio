from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from custom_components.crypto_portfolio.portfolio import (  # noqa: E402
    Holding,
    build_holdings,
    calculate_portfolio,
)


class PortfolioCalculationTest(unittest.TestCase):
    def test_calculates_summary_and_positions(self) -> None:
        holdings = [
            Holding("bitcoin", "BTC", Decimal("0.1"), Decimal("2000")),
            Holding("ethereum", "ETH", Decimal("1"), Decimal("1000")),
        ]
        prices = {
            "bitcoin": {"eur": 30000, "eur_24h_change": 2.5},
            "ethereum": {"eur": 2000, "eur_24h_change": -1.25},
        }

        summary = calculate_portfolio(holdings, prices, "eur")

        self.assertEqual(summary.total_invested, Decimal("3000"))
        self.assertEqual(summary.total_value, Decimal("5000.0"))
        self.assertEqual(summary.total_profit, Decimal("2000.0"))
        self.assertAlmostEqual(float(summary.total_profit_percent), 66.6666666667)
        self.assertEqual(summary.missing_prices, ())
        self.assertEqual(summary.positions[0].value, Decimal("3000.0"))

    def test_tracks_missing_prices_without_breaking_known_totals(self) -> None:
        holdings = [
            Holding("bitcoin", "BTC", Decimal("0.1"), Decimal("2000")),
            Holding("unknown", "UNK", Decimal("5"), Decimal("50")),
        ]
        prices = {"bitcoin": {"eur": 30000}}

        summary = calculate_portfolio(holdings, prices, "eur")

        self.assertEqual(summary.total_invested, Decimal("2050"))
        self.assertEqual(summary.priced_invested, Decimal("2000"))
        self.assertEqual(summary.total_value, Decimal("3000.0"))
        self.assertEqual(summary.total_profit, Decimal("1000.0"))
        self.assertEqual(summary.missing_prices, ("unknown",))

    def test_build_holdings_accepts_known_symbols_as_coin_ids(self) -> None:
        holdings = build_holdings(
            [
                {
                    "coin_id": "BTC",
                    "symbol": "BTC",
                    "amount": 0.1,
                    "invested": 500,
                }
            ]
        )

        self.assertEqual(holdings[0].coin_id, "bitcoin")


if __name__ == "__main__":
    unittest.main()
