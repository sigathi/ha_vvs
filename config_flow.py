"""Config flow for VVS integration."""
from __future__ import annotations

import logging
from typing import Any
import voluptuous as vol
import vvspy

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig, SelectSelectorMode
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_DESTINATION,
    CONF_START,
    CONF_OFFSET,
    CONF_ROUTE_TYPE,
    CONF_MAX_CONNECTIONS,
    DEFAULT_OFFSET,
    DEFAULT_MAX_CONNECTIONS,
    DEFAULT_ROUTE_TYPE,
    ROUTE_TYPE_OPTIONS,
)

_LOGGER = logging.getLogger(__name__)

async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    
    def _test_connection():
        # Try to fetch 1 trip to see if stations are valid
        return vvspy.get_trips(
            data[CONF_START],
            data[CONF_DESTINATION],
            limit=1
        )

    try:
        result = await hass.async_add_executor_job(_test_connection)
        if not result:
            raise ValueError("no_trips_found")
    except Exception as err:
        # generic catch-all for library errors
        _LOGGER.error("Validation error: %s", err)
        raise ValueError("cannot_connect") from err

    return {"title": f"{data[CONF_START]} - {data[CONF_DESTINATION]}"}


class VVSConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for VVS."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                
                # Create unique ID to prevent duplicates
                await self.async_set_unique_id(
                    f"{user_input[CONF_START]}-{user_input[CONF_DESTINATION]}"
                )
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=info["title"], data=user_input)
            
            except ValueError as err:
                if "no_trips_found" in str(err):
                    errors["base"] = "invalid_station"
                else:
                    errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_START): cv.string,
                    vol.Required(CONF_DESTINATION): cv.string,
                    vol.Optional(CONF_OFFSET, default=DEFAULT_OFFSET): cv.positive_int,
                    vol.Optional(CONF_MAX_CONNECTIONS, default=DEFAULT_MAX_CONNECTIONS): cv.positive_int,
                    vol.Optional(CONF_ROUTE_TYPE, default=DEFAULT_ROUTE_TYPE): SelectSelector(
                        SelectSelectorConfig(
                            options=list(ROUTE_TYPE_OPTIONS.keys()),
                            mode=SelectSelectorMode.DROPDOWN,
                            translation_key=CONF_ROUTE_TYPE
                        )
                    ),
                }
            ),
            errors=errors,
        )
