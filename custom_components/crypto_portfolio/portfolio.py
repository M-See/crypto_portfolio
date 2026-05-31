"""Portfolio calculation logic without Home Assistant dependencies."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from .coins import normalize_coin_id


@dataclass(frozen=True)
class Holding:
    """A configured crypto holding."""

    coin_id: str
    symbol: str
    amount: Decimal
    invested: Decimal


@dataclass(frozen=True)
class CoinPosition:
    """Calculated values for one coin position."""

    coin_id: str
    symbol: str
    amount: Decimal
    invested: Decimal
    current_price: Decimal | None
    value: Decimal | None
    profit: Decimal | None
    profit_percent: Decimal | None
    change_24h_percent: Decimal | None


@dataclass(frozen=True)
class PortfolioSummary:
    """Calculated values for the whole portfolio."""

    currency: str
    positions: tuple[CoinPosition, ...]
    total_invested: Decimal
    priced_invested: Decimal
    total_value: Decimal
    total_profit: Decimal | None
    total_profit_percent: Decimal | None
    missing_prices: tuple[str, ...]


def decimal_value(value: Any, field_name: str) -> Decimal:
    """Convert a config/API value to Decimal."""
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as err:
        raise ValueError(f"{field_name} must be a number") from err


def optional_decimal(value: Any) -> Decimal | None:
    """Convert an optional config/API value to Decimal."""
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def percent(part: Decimal, total: Decimal) -> Decimal | None:
    """Return part as percentage of total."""
    if total == 0:
        return None
    return (part / total) * Decimal(100)


def build_holdings(raw_holdings: list[dict[str, Any]]) -> list[Holding]:
    """Build typed holdings from config entry options."""
    return [
        Holding(
            coin_id=normalize_coin_id(item["coin_id"]),
            symbol=str(item["symbol"]).upper(),
            amount=decimal_value(item["amount"], "amount"),
            invested=decimal_value(item["invested"], "invested"),
        )
        for item in raw_holdings
    ]


def calculate_portfolio(
    holdings: list[Holding],
    prices: dict[str, dict[str, Any]],
    currency: str,
) -> PortfolioSummary:
    """Calculate portfolio statistics from holdings and price data."""
    currency = currency.lower()
    positions: list[CoinPosition] = []
    missing_prices: list[str] = []
    total_invested = Decimal(0)
    priced_invested = Decimal(0)
    total_value = Decimal(0)

    for holding in holdings:
        total_invested += holding.invested
        coin_prices = prices.get(holding.coin_id, {})
        current_price = optional_decimal(coin_prices.get(currency))
        change_24h = optional_decimal(coin_prices.get(f"{currency}_24h_change"))

        if current_price is None:
            missing_prices.append(holding.coin_id)
            positions.append(
                CoinPosition(
                    coin_id=holding.coin_id,
                    symbol=holding.symbol,
                    amount=holding.amount,
                    invested=holding.invested,
                    current_price=None,
                    value=None,
                    profit=None,
                    profit_percent=None,
                    change_24h_percent=change_24h,
                )
            )
            continue

        value = holding.amount * current_price
        profit_value = value - holding.invested
        priced_invested += holding.invested
        total_value += value

        positions.append(
            CoinPosition(
                coin_id=holding.coin_id,
                symbol=holding.symbol,
                amount=holding.amount,
                invested=holding.invested,
                current_price=current_price,
                value=value,
                profit=profit_value,
                profit_percent=percent(profit_value, holding.invested),
                change_24h_percent=change_24h,
            )
        )

    total_profit = None
    total_profit_percent = None
    if priced_invested:
        total_profit = total_value - priced_invested
        total_profit_percent = percent(total_profit, priced_invested)

    return PortfolioSummary(
        currency=currency,
        positions=tuple(positions),
        total_invested=total_invested,
        priced_invested=priced_invested,
        total_value=total_value,
        total_profit=total_profit,
        total_profit_percent=total_profit_percent,
        missing_prices=tuple(missing_prices),
    )
