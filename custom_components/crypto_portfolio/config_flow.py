"""Config flow for Crypto Portfolio."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME, CONF_SCAN_INTERVAL
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_AMOUNT,
    CONF_COIN_ID,
    CONF_CURRENCY,
    CONF_HOLDINGS,
    CONF_HOLDINGS_JSON,
    CONF_INVESTED,
    CONF_SYMBOL,
    DEFAULT_CURRENCY,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DOMAIN,
)
from .options import (
    DEFAULT_HOLDINGS,
    HoldingsValidationError,
    holdings_from_json,
    holdings_to_json,
    normalize_holding,
)
from .storage import (
    holdings_file_display_path,
    holdings_file_path,
    read_holdings_file,
    write_holdings_file,
)

MAX_SCAN_INTERVAL_MINUTES = 1440

FIELD_COIN_INDEX = "coin_index"


def _holdings_selector() -> TextSelector:
    """Return the holdings JSON textarea selector."""
    return TextSelector(
        TextSelectorConfig(
            multiline=True,
            type=TextSelectorType.TEXT,
        )
    )


def _money_selector() -> NumberSelector:
    """Return a box selector for money/amount values."""
    return NumberSelector(
        NumberSelectorConfig(
            min=0,
            step="any",
            mode=NumberSelectorMode.BOX,
        )
    )


def _coin_schema(defaults: dict[str, Any]) -> vol.Schema:
    """Build a schema for one coin position."""
    return vol.Schema(
        {
            vol.Required(
                CONF_COIN_ID,
                default=defaults.get(CONF_COIN_ID, ""),
            ): str,
            vol.Required(
                CONF_SYMBOL,
                default=defaults.get(CONF_SYMBOL, ""),
            ): str,
            vol.Required(
                CONF_AMOUNT,
                default=defaults.get(CONF_AMOUNT, 0),
            ): _money_selector(),
            vol.Required(
                CONF_INVESTED,
                default=defaults.get(CONF_INVESTED, 0),
            ): _money_selector(),
        }
    )


def _config_schema(defaults: dict[str, Any]) -> vol.Schema:
    """Build the initial config flow schema."""
    return vol.Schema(
        {
            vol.Required(
                CONF_NAME,
                default=defaults.get(CONF_NAME, DEFAULT_NAME),
            ): str,
            vol.Required(
                CONF_CURRENCY,
                default=defaults.get(CONF_CURRENCY, DEFAULT_CURRENCY),
            ): str,
            vol.Required(
                CONF_SCAN_INTERVAL,
                default=defaults.get(
                    CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES
                ),
            ): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=MAX_SCAN_INTERVAL_MINUTES)
            ),
            vol.Required(
                CONF_HOLDINGS_JSON,
                default=defaults.get(
                    CONF_HOLDINGS_JSON, holdings_to_json(DEFAULT_HOLDINGS)
                ),
            ): _holdings_selector(),
        }
    )


def _settings_schema(defaults: dict[str, Any]) -> vol.Schema:
    """Build the general settings schema."""
    return vol.Schema(
        {
            vol.Required(
                CONF_NAME,
                default=defaults.get(CONF_NAME, DEFAULT_NAME),
            ): str,
            vol.Required(
                CONF_CURRENCY,
                default=defaults.get(CONF_CURRENCY, DEFAULT_CURRENCY),
            ): str,
            vol.Required(
                CONF_SCAN_INTERVAL,
                default=defaults.get(
                    CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES
                ),
            ): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=MAX_SCAN_INTERVAL_MINUTES)
            ),
        }
    )


def _advanced_json_schema(defaults: dict[str, Any]) -> vol.Schema:
    """Build the advanced JSON editor schema."""
    return vol.Schema(
        {
            vol.Required(
                CONF_HOLDINGS_JSON,
                default=defaults.get(
                    CONF_HOLDINGS_JSON, holdings_to_json(DEFAULT_HOLDINGS)
                ),
            ): _holdings_selector(),
        }
    )


def _normalize_currency(value: str) -> str:
    """Normalize a currency code from user input."""
    currency = value.strip().lower()
    if not currency:
        raise ValueError("currency is required")
    return currency


def _coin_options(holdings: list[dict[str, Any]]) -> list[SelectOptionDict]:
    """Return dropdown options for configured holdings."""
    return [
        SelectOptionDict(
            value=str(index),
            label=f"{holding.get(CONF_SYMBOL, '').upper()} - {holding.get(CONF_COIN_ID, '')}",
        )
        for index, holding in enumerate(holdings)
    ]


def _coin_select_schema(holdings: list[dict[str, Any]]) -> vol.Schema:
    """Build a coin select schema."""
    return vol.Schema(
        {
            vol.Required(FIELD_COIN_INDEX): SelectSelector(
                SelectSelectorConfig(
                    options=_coin_options(holdings),
                    mode=SelectSelectorMode.DROPDOWN,
                )
            )
        }
    )


class CryptoPortfolioConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Crypto Portfolio."""

    VERSION = 1
    MINOR_VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return CryptoPortfolioOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                holdings = holdings_from_json(user_input[CONF_HOLDINGS_JSON])
                currency = _normalize_currency(user_input[CONF_CURRENCY])
            except HoldingsValidationError:
                errors[CONF_HOLDINGS_JSON] = "invalid_holdings"
            except ValueError:
                errors[CONF_CURRENCY] = "invalid_currency"
            else:
                name = user_input[CONF_NAME].strip() or DEFAULT_NAME
                return self.async_create_entry(
                    title=name,
                    data={CONF_NAME: name},
                    options={
                        CONF_NAME: name,
                        CONF_CURRENCY: currency,
                        CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                        CONF_HOLDINGS: holdings,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_config_schema(user_input or {}),
            errors=errors,
        )


class CryptoPortfolioOptionsFlow(config_entries.OptionsFlowWithReload):
    """Handle options for Crypto Portfolio."""

    def _holdings_file_path(self) -> Path:
        """Return the holdings JSON path for this config entry."""
        return holdings_file_path(
            self.hass.config.config_dir, self.config_entry.entry_id
        )

    def _file_description_placeholders(self) -> dict[str, str]:
        """Return placeholders used by JSON file descriptions."""
        return {
            "holdings_file": holdings_file_display_path(self.config_entry.entry_id),
            "file_editor_url": (
                "https://my.home-assistant.io/redirect/supervisor_ingress/"
                "?addon=core_configurator"
            ),
        }

    def _current_options(self) -> dict[str, Any]:
        """Return current options with defaults filled in."""
        options = dict(self.config_entry.options)
        options.setdefault(
            CONF_NAME, self.config_entry.data.get(CONF_NAME, DEFAULT_NAME)
        )
        options.setdefault(CONF_CURRENCY, DEFAULT_CURRENCY)
        options.setdefault(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES)
        options.setdefault(CONF_HOLDINGS, DEFAULT_HOLDINGS)
        return options

    async def _finish(self, options: dict[str, Any]) -> FlowResult:
        """Save options and update the entry title."""
        name = options.get(CONF_NAME, DEFAULT_NAME).strip() or DEFAULT_NAME
        options[CONF_NAME] = name
        await self.hass.async_add_executor_job(
            write_holdings_file,
            self._holdings_file_path(),
            options[CONF_HOLDINGS],
        )
        self.hass.config_entries.async_update_entry(
            self.config_entry,
            title=name,
            data={**self.config_entry.data, CONF_NAME: name},
        )
        return self.async_create_entry(title="", data=options)

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Show the options menu."""
        return self.async_show_menu(
            step_id="init",
            menu_options=[
                "settings",
                "add_coin",
                "select_coin",
                "remove_coin",
                "advanced_json",
                "file_editor",
            ],
            description_placeholders=self._file_description_placeholders(),
        )

    async def async_step_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Edit general portfolio settings."""
        errors: dict[str, str] = {}
        options = self._current_options()

        if user_input is not None:
            try:
                currency = _normalize_currency(user_input[CONF_CURRENCY])
            except ValueError:
                errors[CONF_CURRENCY] = "invalid_currency"
            else:
                options[CONF_NAME] = user_input[CONF_NAME].strip() or DEFAULT_NAME
                options[CONF_CURRENCY] = currency
                options[CONF_SCAN_INTERVAL] = user_input[CONF_SCAN_INTERVAL]
                return await self._finish(options)

        return self.async_show_form(
            step_id="settings",
            data_schema=_settings_schema(user_input or options),
            errors=errors,
        )

    async def async_step_add_coin(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Add a coin position."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                holding = normalize_holding(user_input)
            except HoldingsValidationError:
                errors["base"] = "invalid_coin"
            else:
                options = self._current_options()
                options[CONF_HOLDINGS] = [*options[CONF_HOLDINGS], holding]
                return await self._finish(options)

        return self.async_show_form(
            step_id="add_coin",
            data_schema=_coin_schema(user_input or {}),
            errors=errors,
        )

    async def async_step_select_coin(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Select a coin position to edit."""
        options = self._current_options()
        holdings = options[CONF_HOLDINGS]

        if user_input is not None:
            self._coin_index = int(user_input[FIELD_COIN_INDEX])
            return await self.async_step_edit_coin()

        return self.async_show_form(
            step_id="select_coin",
            data_schema=_coin_select_schema(holdings),
            errors={},
        )

    async def async_step_edit_coin(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Edit one coin position."""
        errors: dict[str, str] = {}
        options = self._current_options()
        holdings = options[CONF_HOLDINGS]
        coin_index = getattr(self, "_coin_index", 0)

        if user_input is not None:
            try:
                holding = normalize_holding(user_input)
            except HoldingsValidationError:
                errors["base"] = "invalid_coin"
            else:
                updated_holdings = list(holdings)
                updated_holdings[coin_index] = holding
                options[CONF_HOLDINGS] = updated_holdings
                return await self._finish(options)

        return self.async_show_form(
            step_id="edit_coin",
            data_schema=_coin_schema(user_input or holdings[coin_index]),
            errors=errors,
        )

    async def async_step_remove_coin(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Remove one coin position."""
        errors: dict[str, str] = {}
        options = self._current_options()
        holdings = options[CONF_HOLDINGS]

        if user_input is not None:
            if len(holdings) <= 1:
                errors["base"] = "cannot_remove_last"
            else:
                coin_index = int(user_input[FIELD_COIN_INDEX])
                options[CONF_HOLDINGS] = [
                    holding
                    for index, holding in enumerate(holdings)
                    if index != coin_index
                ]
                return await self._finish(options)

        return self.async_show_form(
            step_id="remove_coin",
            data_schema=_coin_select_schema(holdings),
            errors=errors,
        )

    async def async_step_advanced_json(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Edit all holdings as raw JSON."""
        errors: dict[str, str] = {}
        options = self._current_options()

        if user_input is not None:
            try:
                holdings = holdings_from_json(user_input[CONF_HOLDINGS_JSON])
            except HoldingsValidationError:
                errors[CONF_HOLDINGS_JSON] = "invalid_holdings"
            else:
                options[CONF_HOLDINGS] = holdings
                return await self._finish(options)

        return self.async_show_form(
            step_id="advanced_json",
            data_schema=_advanced_json_schema(
                user_input
                or {CONF_HOLDINGS_JSON: holdings_to_json(options[CONF_HOLDINGS])}
            ),
            errors=errors,
            description_placeholders=self._file_description_placeholders(),
        )

    async def async_step_file_editor(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Import holdings edited in the external JSON file."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                holdings = await self.hass.async_add_executor_job(
                    read_holdings_file, self._holdings_file_path()
                )
            except FileNotFoundError:
                errors["base"] = "holdings_file_missing"
            except (HoldingsValidationError, OSError):
                errors["base"] = "invalid_holdings_file"
            else:
                options = self._current_options()
                options[CONF_HOLDINGS] = holdings
                return await self._finish(options)

        return self.async_show_form(
            step_id="file_editor",
            data_schema=vol.Schema({}),
            errors=errors,
            description_placeholders=self._file_description_placeholders(),
        )
