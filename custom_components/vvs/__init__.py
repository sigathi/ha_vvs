"""The VVS integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

import os
import sys

current_path = os.path.dirname(__file__)
if current_path not in sys.path:
    sys.path.append(current_path)

from .const import (
    DOMAIN,
    CONF_START,
    CONF_DESTINATION,
    CONF_MAX_CONNECTIONS,
    CONF_ROUTE_TYPE,
    CONF_OFFSET,
)
from .coordinator import VVSDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up VVS from a config entry."""

    coordinator = VVSDataUpdateCoordinator(
        hass,
        start_station=entry.data[CONF_START],
        dest_station=entry.data[CONF_DESTINATION],
        limit=entry.data[CONF_MAX_CONNECTIONS],
        route_type=entry.data[CONF_ROUTE_TYPE],
        offset=entry.data[CONF_OFFSET],
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
