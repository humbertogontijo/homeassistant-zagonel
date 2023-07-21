"""Sensor platform for zagonel."""
from __future__ import annotations

import math

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityDescription,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util import slugify

from .const import DOMAIN
from .coordinator import ZagonelDataUpdateCoordinator
from .entity import ZagonelEntity

ENTITY_DESCRIPTIONS = (
    ClimateEntityDescription(
        key="shower",
        name="Shower",
        icon="mdi:shower-head",
        translation_key="shower"
    ),
)


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    unique_id = slugify(coordinator.data.chars.Device_Id)
    async_add_devices(
        ZagonelClimate(
            unique_id=f"{entity_description.key}_{unique_id}",
            coordinator=coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class ZagonelClimate(ZagonelEntity, ClimateEntity):
    """Zagonel Climate class."""

    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_target_temperature_step = 1
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp = 25
    _attr_max_temp = 50

    def __init__(
            self,
            unique_id: str,
            coordinator: ZagonelDataUpdateCoordinator,
            entity_description: ClimateEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(unique_id, coordinator)
        self.entity_description = entity_description

    @property
    def hvac_mode(self) -> HVACMode | None:
        """Return the current HVAC mode."""
        return HVACMode.HEAT if self.coordinator.client.is_running() else HVACMode.OFF

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return math.floor(self.coordinator.data.status.To / 1000)

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        return math.floor(self.coordinator.data.status.Ts / 1000)

    async def async_set_temperature(self, **kwargs) -> None:
        """async_set_temperature."""
        temperature = kwargs[ATTR_TEMPERATURE]
        await self.send("Preset_1", math.floor(temperature * 1000))

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """async_set_hvac_mode."""
        raise HomeAssistantError("Can't change mode from the api")
