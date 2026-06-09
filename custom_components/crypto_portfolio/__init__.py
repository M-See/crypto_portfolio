"""Crypto Portfolio custom integration."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

from .const import CONF_HOLDINGS, DOMAIN, FRONTEND_CARD_URL
from .options import DEFAULT_HOLDINGS, HoldingsValidationError
from .storage import holdings_file_path, load_or_create_holdings_file

PLATFORMS = ["sensor"]

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration and expose the bundled frontend card."""
    from homeassistant.components import frontend
    from homeassistant.components.http import StaticPathConfig

    frontend_path = Path(__file__).parent / "frontend"
    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                f"/{DOMAIN}",
                str(frontend_path),
                cache_headers=True,
            )
        ]
    )
    frontend.add_extra_js_url(hass, FRONTEND_CARD_URL)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Crypto Portfolio from a config entry."""
    options = dict(entry.options)
    current_holdings = options.get(CONF_HOLDINGS, DEFAULT_HOLDINGS)
    path = holdings_file_path(hass.config.config_dir, entry.entry_id)

    try:
        file_holdings = await hass.async_add_executor_job(
            load_or_create_holdings_file, path, current_holdings
        )
    except (HoldingsValidationError, OSError) as err:
        _LOGGER.error("Could not load holdings from %s: %s", path, err)
    else:
        if file_holdings != current_holdings:
            options[CONF_HOLDINGS] = file_holdings
            hass.config_entries.async_update_entry(entry, options=options)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Crypto Portfolio config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
