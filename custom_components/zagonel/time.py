"""Sensor platform for zagonel."""
from __future__ import annotations

from datetime import datetime, time, timedelta

from homeassistant.components.time import TimeEntity, TimeEntityDescription
from homeassistant.util import slugify
from .const import DOMAIN
from .coordinator import ZagonelDataUpdateCoordinator
from .entity import ZagonelEntity

ENTITY_DESCRIPTIONS = (
    TimeEntityDescription(
        key="parental_limit",
        name="Parental Limit",
        icon="mdi:timer-stop",
    ),
)


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    unique_id = slugify(coordinator.data.chars.Device_Id)
    async_add_devices(
        ZagonelTime(
            unique_id=f"{entity_description.key}_{unique_id}",
            coordinator=coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class ZagonelTime(ZagonelEntity, TimeEntity):
    """Zagonel Number class."""

    def __init__(
            self,
            unique_id: str,
            coordinator: ZagonelDataUpdateCoordinator,
            entity_description: TimeEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(unique_id, coordinator)
        self.entity_description = entity_description

    @property
    def native_value(self) -> time | None:
        """Get native value."""
        delta = timedelta(seconds=self.coordinator.client.data.chars.Parental_Limit)
        return (datetime.min + delta).time()

    async def async_set_value(self, value: time) -> None:
        """Set native value."""
        seconds = (value.hour * 60 + value.minute) * 60 + value.second
        await self.send("Parental_Limit", seconds)
