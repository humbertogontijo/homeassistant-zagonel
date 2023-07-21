"""Sensor platform for zagonel."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.util import slugify

from .const import DOMAIN
from .coordinator import ZagonelDataUpdateCoordinator
from .entity import ZagonelEntity

ENTITY_DESCRIPTIONS = (
    NumberEntityDescription(
        key="shower_volume",
        native_unit_of_measurement="%",
        native_max_value=100,
        native_min_value=0,
        native_step=1,
        name="Shower Volume",
        icon="mdi:volume-high",
        translation_key="shower_volume"
    ),
)


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    unique_id = slugify(coordinator.data.chars.Device_Id)
    async_add_devices(
        ZagonelNumber(
            unique_id=f"{entity_description.key}_{unique_id}",
            coordinator=coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class ZagonelNumber(ZagonelEntity, NumberEntity):
    """Zagonel Number class."""

    def __init__(
            self,
            unique_id: str,
            coordinator: ZagonelDataUpdateCoordinator,
            entity_description: NumberEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(unique_id, coordinator)
        self.entity_description = entity_description

    @property
    def native_value(self) -> float | None:
        """Get native value."""
        return self.coordinator.client.data.chars.Buzzer_Volume

    async def async_set_native_value(self, value: float) -> None:
        """Set native value."""
        int_value = int(value)
        await self.send("Buzzer_Volume", int_value)
