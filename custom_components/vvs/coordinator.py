"""DataUpdateCoordinator for VVS."""
from datetime import datetime, timedelta
import logging
from typing import Any

from . import vvspy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

class VVSDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching VVS data."""

    def __init__(
        self,
        hass: HomeAssistant,
        start_station: str,
        dest_station: str,
        limit: int,
        route_type: str,
        offset: int,
    ) -> None:
        """Initialize."""
        self.start_station = start_station
        self.dest_station = dest_station
        self.limit = limit
        self.route_type = route_type
        self.offset = offset

        super().__init__(
            hass,
            _LOGGER,
            name=f"VVS {start_station} to {dest_station}",
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from VVS API."""
        try:
            # Calculate the check time (now + offset)
            check_time = datetime.now() + timedelta(minutes=self.offset)
            
            # Run the blocking library call in a separate thread
            trips = await self.hass.async_add_executor_job(
                self._get_trips_internal, check_time
            )

            if not trips:
                _LOGGER.warning("No trips found for %s to %s", self.start_station, self.dest_station)
                return {}

            return self._parse_trips(trips)

        except Exception as err:
            raise UpdateFailed(f"Error fetching VVS data: {err}") from err

    def _get_trips_internal(self, check_time):
        """Wrapper to call vvspy synchronously."""
        # Note: vvspy documentation suggests get_trips might return a list of Trip objects
        return vvspy.get_trips(
            self.start_station,
            self.dest_station,
            check_time=check_time,
            limit=self.limit,
            # Note: vvspy might not support route_type directly in get_trips 
            # depending on version, but we keep the plumbing here.
        )

    def _parse_trips(self, raw_trips) -> dict:
        """Parse the raw vvspy objects into a clean dictionary."""
        parsed_data = {"trips": []}
        
        for trip in raw_trips:
            # Basic error safety if a trip is malformed
            if not trip.connections:
                continue

            first_leg = trip.connections[0]
            last_leg = trip.connections[-1]
            
            # Calculate duration
            arrival_planned = last_leg.destination.arrival_time_planned
            departure_planned = first_leg.origin.departure_time_planned
            
            # Handle potential None values in API response
            if not arrival_planned or not departure_planned:
                continue

            duration = (arrival_planned - departure_planned).total_seconds() / 60

            # Build the trip details
            trip_info = {
                "departure": dt_util.as_local(departure_planned),
                "departure_delay": first_leg.origin.delay or 0,
                "arrival": dt_util.as_local(arrival_planned),
                "arrival_delay": last_leg.destination.delay or 0,
                "duration": int(duration),
                "transports": [],
                "via": []
            }

            for connection in trip.connections:
                # Skip pure walking legs at start/end if desired, 
                # but usually we want to see the transport chain.
                if connection.transportation:
                     trip_info["transports"].append(connection.transportation.number)
                
                if connection.destination:
                    trip_info["via"].append(connection.destination.name)

            parsed_data["trips"].append(trip_info)

        return parsed_data
