"""DataUpdateCoordinator for VVS."""

from datetime import timedelta, timezone
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

import os
import sys

current_path = os.path.dirname(__file__)
if current_path not in sys.path:
    sys.path.append(current_path)

import vvspy
from .vvspy.enums.stations import Station
from .const import SCAN_INTERVAL

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

        self.start_station_name = self._get_friendly_name(start_station)
        self.dest_station_name = self._get_friendly_name(dest_station)

        super().__init__(
            hass,
            _LOGGER,
            name=f"VVS {self.start_station_name} to {self.dest_station_name}",
            update_interval=SCAN_INTERVAL,
        )

    def _get_friendly_name(self, station_id: str) -> str:
        """Reverse lookup: Find the human name for a station ID."""
        for name, member in Station.__members__.items():
            if member.value == station_id:
                return name.replace("_", " ").title()
        return station_id

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from VVS API."""
        try:
            # 1. Prepare search time (Current Local Time + Offset)
            now_utc = dt_util.now()
            now_local = dt_util.as_local(now_utc)
            check_time = now_local + timedelta(minutes=self.offset)

            # Send 'naive' local time to API so it searches for "20:01" not "19:01"
            check_time_naive = check_time.replace(tzinfo=None)

            trips = await self.hass.async_add_executor_job(
                self._get_trips_internal, check_time_naive
            )

            if not trips:
                return {}

            return self._parse_trips(trips)

        except Exception as err:
            raise UpdateFailed(f"Error fetching VVS data: {err}") from err

    def _get_trips_internal(self, check_time):
        """Wrapper to call vvspy synchronously."""
        return vvspy.get_trips(
            self.start_station,
            self.dest_station,
            check_time=check_time,
            limit=self.limit,
        )

    def _parse_trips(self, raw_trips) -> dict:
        """Parse the raw vvspy objects into a clean dictionary."""
        parsed_data = {"trips": []}

        for trip in raw_trips:
            if not trip.connections:
                continue

            first_leg = trip.connections[0]
            last_leg = trip.connections[-1]

            arrival_planned = last_leg.destination.arrival_time_planned
            departure_planned = first_leg.origin.departure_time_planned

            if not arrival_planned or not departure_planned:
                continue

            duration = (arrival_planned - departure_planned).total_seconds() / 60

            # --- TIMEZONE FIX ---
            # The API returns Naive UTC (e.g. 19:01)
            # 1. Force UTC timezone onto the naive object
            dep_utc = departure_planned.replace(tzinfo=timezone.utc)
            arr_utc = arrival_planned.replace(tzinfo=timezone.utc)

            # 2. Convert to HA Local Time (e.g. 19:01 UTC -> 20:01 CET)
            local_dep = dt_util.as_local(dep_utc)
            local_arr = dt_util.as_local(arr_utc)

            # 3. Format string
            dep_str = local_dep.strftime("%H:%M")
            arr_str = local_arr.strftime("%H:%M")
            # --------------------

            trip_info = {
                "departure": dep_str,
                "departure_delay": first_leg.origin.delay or 0,
                "arrival": arr_str,
                "arrival_delay": last_leg.destination.delay or 0,
                "duration": int(duration),
                "transports": [],
                "via": [],
            }

            for connection in trip.connections:
                if connection.transportation:
                    trip_info["transports"].append(connection.transportation.number)

                if connection.destination:
                    trip_info["via"].append(connection.destination.name)

            parsed_data["trips"].append(trip_info)

        return parsed_data
