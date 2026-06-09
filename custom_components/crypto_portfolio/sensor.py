"""Sensor platform for Crypto Portfolio."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
import logging
from typing import Any

from aiohttp import ClientError

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, CONF_SCAN_INTERVAL, PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .api import async_fetch_prices
from .const import (
    CONF_CURRENCY,
    CONF_HOLDINGS,
    DEFAULT_CURRENCY,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DOMAIN,
)
from .options import DEFAULT_HOLDINGS
from .portfolio import PortfolioSummary, build_holdings, calculate_portfolio

_LOGGER = logging.getLogger(__name__)


def decimal_to_float(value: Decimal | None) -> float | None:
    """Convert Decimal sensor values to float."""
    if value is None:
        return None
    return float(value)


@dataclass(frozen=True, kw_only=True)
class PortfolioSensorDescription(SensorEntityDescription):
    """Description for a summary portfolio sensor."""

    value_fn: Callable[[PortfolioSummary], Decimal | None]
    extra_attrs_fn: Callable[[PortfolioSummary], dict[str, Any]] | None = None


SUMMARY_DESCRIPTIONS: tuple[PortfolioSensorDescription, ...] = (
    PortfolioSensorDescription(
        key="value",
        translation_key="value",
        name="Value",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda summary: summary.total_value,
        extra_attrs_fn=lambda summary: {
            "invested": decimal_to_float(summary.total_invested),
            "priced_invested": decimal_to_float(summary.priced_invested),
            "profit": decimal_to_float(summary.total_profit),
            "profit_percent": decimal_to_float(summary.total_profit_percent),
            "missing_prices": list(summary.missing_prices),
            "positions_count": len(summary.positions),
            "positions": [
                {
                    "coin_id": position.coin_id,
                    "symbol": position.symbol,
                    "amount": decimal_to_float(position.amount),
                    "invested": decimal_to_float(position.invested),
                    "current_price": decimal_to_float(position.current_price),
                    "value": decimal_to_float(position.value),
                    "profit": decimal_to_float(position.profit),
                    "profit_percent": decimal_to_float(position.profit_percent),
                    "change_24h_percent": decimal_to_float(
                        position.change_24h_percent
                    ),
                }
                for position in summary.positions
            ],
        },
    ),
    PortfolioSensorDescription(
        key="invested",
        translation_key="invested",
        name="Invested",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda summary: summary.total_invested,
    ),
    PortfolioSensorDescription(
        key="profit",
        translation_key="profit",
        name="Profit",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda summary: summary.total_profit,
    ),
    PortfolioSensorDescription(
        key="profit_percent",
        translation_key="profit_percent",
        name="Profit Percent",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda summary: summary.total_profit_percent,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Crypto Portfolio sensors from a config entry."""
    name = entry.options.get(CONF_NAME, entry.data.get(CONF_NAME, DEFAULT_NAME))
    currency = entry.options.get(CONF_CURRENCY, DEFAULT_CURRENCY).lower()
    raw_holdings = entry.options.get(CONF_HOLDINGS, DEFAULT_HOLDINGS)
    holdings = build_holdings(raw_holdings)
    scan_interval_minutes = entry.options.get(
        CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES
    )
    session = async_get_clientsession(hass)
    latest_summary = calculate_portfolio(holdings, {}, currency)

    async def async_update_data() -> PortfolioSummary:
        """Fetch latest data from CoinGecko and calculate the portfolio."""
        nonlocal latest_summary
        try:
            prices = await async_fetch_prices(
                session,
                [holding.coin_id for holding in holdings],
                currency,
            )
        except (ClientError, TimeoutError, ValueError) as err:
            _LOGGER.warning(
                "Could not update CoinGecko prices; keeping existing data: %s",
                err,
            )
            return latest_summary

        latest_summary = calculate_portfolio(holdings, prices, currency)
        return latest_summary

    coordinator: DataUpdateCoordinator[PortfolioSummary] = DataUpdateCoordinator(
        hass,
        _LOGGER,
        config_entry=entry,
        name=f"{DOMAIN}_{entry.entry_id}",
        update_method=async_update_data,
        update_interval=timedelta(minutes=scan_interval_minutes),
    )
    coordinator.async_set_updated_data(latest_summary)

    unique_prefix = f"{DOMAIN}_{entry.entry_id}"
    entities: list[SensorEntity] = [
        CryptoPortfolioSummarySensor(coordinator, description, name, unique_prefix)
        for description in SUMMARY_DESCRIPTIONS
    ]
    entities.extend(
        CryptoPortfolioCoinSensor(coordinator, position.coin_id, name, unique_prefix)
        for position in coordinator.data.positions
    )

    async_add_entities(entities)
    entry.async_create_background_task(
        hass,
        coordinator.async_request_refresh(),
        name=f"{DOMAIN}_{entry.entry_id}_initial_refresh",
    )


class CryptoPortfolioSummarySensor(
    CoordinatorEntity[DataUpdateCoordinator[PortfolioSummary]], SensorEntity
):
    """Summary sensor for portfolio values."""

    entity_description: PortfolioSensorDescription
    _attr_has_entity_name = False

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[PortfolioSummary],
        description: PortfolioSensorDescription,
        portfolio_name: str,
        unique_prefix: str,
    ) -> None:
        """Initialize the summary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_name = f"{portfolio_name} {description.name}"
        self._attr_unique_id = f"{unique_prefix}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, unique_prefix)},
            "name": portfolio_name,
            "manufacturer": "Local",
        }
        if description.device_class == SensorDeviceClass.MONETARY:
            self._attr_native_unit_of_measurement = (
                self.coordinator.data.currency.upper()
            )

    @property
    def native_value(self) -> float | None:
        """Return the sensor value."""
        return decimal_to_float(self.entity_description.value_fn(self.coordinator.data))

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        if self.entity_description.extra_attrs_fn is None:
            return None
        return self.entity_description.extra_attrs_fn(self.coordinator.data)


class CryptoPortfolioCoinSensor(
    CoordinatorEntity[DataUpdateCoordinator[PortfolioSummary]], SensorEntity
):
    """Current value sensor for one coin position."""

    _attr_has_entity_name = False
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[PortfolioSummary],
        coin_id: str,
        portfolio_name: str,
        unique_prefix: str,
    ) -> None:
        """Initialize the coin sensor."""
        super().__init__(coordinator)
        self._coin_id = coin_id
        self._attr_name = f"{portfolio_name} {coin_id.title()} Value"
        self._attr_unique_id = f"{unique_prefix}_{coin_id}_value"
        self._attr_native_unit_of_measurement = self.coordinator.data.currency.upper()
        self._attr_device_info = {
            "identifiers": {(DOMAIN, unique_prefix)},
            "name": portfolio_name,
            "manufacturer": "Local",
        }

    @property
    def native_value(self) -> float | None:
        """Return the current value for this coin."""
        position = self._position
        if position is None:
            return None
        return decimal_to_float(position.value)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        position = self._position
        if position is None:
            return None
        return {
            "coin_id": position.coin_id,
            "symbol": position.symbol,
            "amount": decimal_to_float(position.amount),
            "invested": decimal_to_float(position.invested),
            "current_price": decimal_to_float(position.current_price),
            "profit": decimal_to_float(position.profit),
            "profit_percent": decimal_to_float(position.profit_percent),
            "change_24h_percent": decimal_to_float(position.change_24h_percent),
        }

    @property
    def _position(self):
        """Return the latest position for this sensor."""
        return next(
            (
                position
                for position in self.coordinator.data.positions
                if position.coin_id == self._coin_id
            ),
            None,
        )
