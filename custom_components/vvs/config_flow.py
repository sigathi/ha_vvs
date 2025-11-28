"""Config flow for VVS integration."""

import os
import sys

# Add the current folder to sys.path so 'import vvspy' works
current_path = os.path.dirname(__file__)
if current_path not in sys.path:
    sys.path.append(current_path)

import logging
import re
from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    SelectOptionDict,
)
import homeassistant.helpers.config_validation as cv

from .vvspy.enums.stations import Station

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

CONF_START_SEARCH = "start_search"
CONF_DEST_SEARCH = "dest_search"


def get_station_matches(search_term: str) -> list[SelectOptionDict]:
    """Search the Station Enum, deduplicate variants, and return options."""
    clean_term = search_term.lower().replace(" ", "_")

    matches = []
    seen_labels = set()

    for name, member in Station.__members__.items():
        if clean_term in name.lower():
            # Deduplication: Remove trailing numbers (WALDBURGSTRASSE_1 -> WALDBURGSTRASSE)
            base_name = re.sub(r"_\d+$", "", name)
            readable_label = base_name.replace("_", " ").title()

            if readable_label not in seen_labels:
                matches.append({"label": readable_label, "value": member.value})
                seen_labels.add(readable_label)

            if len(matches) >= 50:
                break

    return sorted(matches, key=lambda x: x["label"])


async def validate_connection(
    hass: HomeAssistant, data: dict[str, Any]
) -> dict[str, Any]:
    """Validate that the selected specific stations actually have a connection."""
    import vvspy

    def _test_connection():
        return vvspy.get_trips(data[CONF_START], data[CONF_DESTINATION], limit=1, routeType=data[CONF_ROUTE_TYPE])

    try:
        result = await hass.async_add_executor_job(_test_connection)
    except Exception as err:
        _LOGGER.exception("VVS connection test failed")
        raise Exception(f"Connection Error: {str(err)}") from err

    if not result:
        raise Exception("No trips found between these specific stations.")

    return {"success": True}


class VVSConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for VVS."""

    VERSION = 1

    def __init__(self):
        """Initialize the flow state."""
        self._search_data = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 1: Ask user for search terms and validate matches exist."""
        errors = {}

        # Defaults allow the user to keep their text if validation fails
        default_start = ""
        default_dest = ""

        if user_input is not None:
            self._search_data = user_input
            start_term = user_input[CONF_START_SEARCH]
            dest_term = user_input[CONF_DEST_SEARCH]

            # Keep what they typed so they don't have to start over
            default_start = start_term
            default_dest = dest_term

            # 1. Validate Length
            if len(start_term) < 3:
                errors[CONF_START_SEARCH] = "search_too_short"
            if len(dest_term) < 3:
                errors[CONF_DEST_SEARCH] = "search_too_short"

            if not errors:
                # 2. Check if matches actually exist
                start_matches = get_station_matches(start_term)
                dest_matches = get_station_matches(dest_term)

                if not start_matches:
                    errors[CONF_START_SEARCH] = "no_start_matches"
                if not dest_matches:
                    errors[CONF_DEST_SEARCH] = "no_dest_matches"

            # 3. Only proceed if absolutely no errors
            if not errors:
                return await self.async_step_select_stations()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_START_SEARCH, default=default_start): cv.string,
                    vol.Required(CONF_DEST_SEARCH, default=default_dest): cv.string,
                }
            ),
            errors=errors,
        )

    async def async_step_select_stations(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 2: Show dropdowns populated with unique search results."""
        errors = {}

        # Re-run search to populate dropdowns (fast enough to not need caching)
        start_options = get_station_matches(self._search_data[CONF_START_SEARCH])
        dest_options = get_station_matches(self._search_data[CONF_DEST_SEARCH])

        if user_input is not None:
            try:
                await validate_connection(self.hass, user_input)

                # Get friendly label for the title
                start_label = next(
                    (
                        o["label"]
                        for o in start_options
                        if o["value"] == user_input[CONF_START]
                    ),
                    user_input[CONF_START],
                )
                dest_label = next(
                    (
                        o["label"]
                        for o in dest_options
                        if o["value"] == user_input[CONF_DESTINATION]
                    ),
                    user_input[CONF_DESTINATION],
                )

                return self.async_create_entry(
                    title=f"{start_label} - {dest_label}", data=user_input
                )
            except Exception:
                errors["base"] = "unknown_error"

        return self.async_show_form(
            step_id="select_stations",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_START): SelectSelector(
                        SelectSelectorConfig(
                            options=start_options,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Required(CONF_DESTINATION): SelectSelector(
                        SelectSelectorConfig(
                            options=dest_options,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional(CONF_OFFSET, default=DEFAULT_OFFSET): cv.positive_int,
                    vol.Optional(
                        CONF_MAX_CONNECTIONS, default=DEFAULT_MAX_CONNECTIONS
                    ): cv.positive_int,
                    vol.Optional(
                        CONF_ROUTE_TYPE, default=DEFAULT_ROUTE_TYPE
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=list(ROUTE_TYPE_OPTIONS.keys()),
                            mode=SelectSelectorMode.DROPDOWN,
                            translation_key=CONF_ROUTE_TYPE,
                        )
                    ),
                }
            ),
            errors=errors,
        )
