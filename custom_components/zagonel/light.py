"""Sensor platform for zagonel."""
from __future__ import annotations

from typing import Any

import homeassistant.util.color as color_util
from homeassistant.components.light import ColorMode, LightEntity, LightEntityDescription
from homeassistant.util import slugify
from .api import ZagonelRGBMode
from .const import DOMAIN
from .coordinator import ZagonelDataUpdateCoordinator
from .entity import ZagonelEntity

ENTITY_DESCRIPTIONS = (
    LightEntityDescription(
        key="shower_light",
        name="Shower light",
        icon="mdi:led-strip",
        translation_key="shower_light"
    ),
)


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    unique_id = slugify(coordinator.data.chars.Device_Id)
    async_add_devices(
        ZagonelLight(
            unique_id=f"{entity_description.key}_{unique_id}",
            coordinator=coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class ZagonelLight(ZagonelEntity, LightEntity):
    """Zagonel Light class."""

    _attr_color_mode = ColorMode.RGB
    _attr_supported_color_modes = {ColorMode.RGB}

    def __init__(
            self,
            unique_id: str,
            coordinator: ZagonelDataUpdateCoordinator,
            entity_description: LightEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(unique_id, coordinator)
        self.entity_description = entity_description

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        """Return the rgb color value [int, int, int]."""
        hex_color = self.coordinator.data.chars.Rgb_Color
        rgb_color = color_util.rgb_hex_to_rgb_list(hex_color[1:])
        return rgb_color[0], rgb_color[1], rgb_color[2]

    @property
    def is_on(self) -> bool | None:
        """Return True if entity is on."""
        return self.coordinator.data.chars.Rgb_Mode == ZagonelRGBMode.FIXED

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        if not self.is_on:
            await self.send(
                "Rgb_Mode",
                ZagonelRGBMode.FIXED
            )
        rgb_color = kwargs.get("rgb_color")
        if rgb_color is not None:
            await self.send(
                "Rgb_Color",
                f"#{color_util.color_rgb_to_hex(rgb_color[0], rgb_color[1], rgb_color[2]).upper()}"
            )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await self.send(
            "Rgb_Mode",
            ZagonelRGBMode.POWER
        )
