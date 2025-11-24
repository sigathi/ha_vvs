"""VVS Sensor platform."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import VVSDataUpdateCoordinator

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the VVS sensor."""
    coordinator: VVSDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([VVSSensor(coordinator, entry)])


class VVSSensor(CoordinatorEntity, SensorEntity):
    """Representation of a VVS Sensor."""

    def __init__(self, coordinator: VVSDataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_next_departure"
        self._attr_name = f"{coordinator.start_station} to {coordinator.dest_station}"
        self._attr_icon = "mdi:train"

    @property
    def native_value(self):
        """Return the state of the sensor (next departure time)."""
        if not self.coordinator.data or not self.coordinator.data.get("trips"):
            return None
        
        # State is the departure time of the very first connection
        return self.coordinator.data["trips"][0]["departure"]

    @property
    def extra_state_attributes(self):
        """Return details about upcoming trips."""
        if not self.coordinator.data:
            return {}
        return self.coordinator.data
