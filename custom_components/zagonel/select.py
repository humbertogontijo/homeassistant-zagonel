"""Sensor platform for zagonel."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.util import slugify

from .api import ZagonelControlMode, ZagonelParentalMode, ZagonelRGBMode
from .const import DOMAIN
from .coordinator import ZagonelDataUpdateCoordinator
from .entity import ZagonelEntity


@dataclass
class ZagonelSelectEntityDescriptionMixin:
    """ZagonelSelectEntityDescriptionMixin."""

    dict_key: str
    enum: type[Enum]


@dataclass
class ZagonelSelectEntityDescription(
    SelectEntityDescription, ZagonelSelectEntityDescriptionMixin
):
    """ZagonelSelectEntityDescription."""


ENTITY_DESCRIPTIONS = (
    ZagonelSelectEntityDescription(
        key="shower_parental_mode",
        name="Shower Parental Mode",
        translation_key="shower_parental_mode",
        dict_key="Parental_Mode",
        enum=ZagonelParentalMode,
        icon="mdi:account-lock",
        options=[parental_mode.name for parental_mode in ZagonelParentalMode]
    ),
    ZagonelSelectEntityDescription(
        key="shower_control_mode",
        name="Shower Control Mode",
        translation_key="shower_control_mode",
        dict_key="Control_Mode",
        enum=ZagonelControlMode,
        icon="mdi:refresh-auto",
        options=[control_mode.name for control_mode in ZagonelControlMode]
    ),
    ZagonelSelectEntityDescription(
        key="shower_rgb_mode",
        name="Shower RGB Mode",
        translation_key="shower_rgb_mode",
        dict_key="Rgb_Mode",
        enum=ZagonelRGBMode,
        icon="mdi:led-on",
        options=[rgb_mode.name for rgb_mode in ZagonelRGBMode]
    ),
)


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    unique_id = slugify(coordinator.data.chars.Device_Id)
    async_add_devices(
        ZagonelSelect(
            unique_id=f"{entity_description.key}_{unique_id}",
            coordinator=coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class ZagonelSelect(ZagonelEntity, SelectEntity):
    """zagonel Select class."""

    entity_description: ZagonelSelectEntityDescription

    def __init__(
            self,
            unique_id: str,
            coordinator: ZagonelDataUpdateCoordinator,
            entity_description: ZagonelSelectEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(unique_id, coordinator)
        self.entity_description = entity_description

    @property
    def current_option(self) -> str | None:
        """Return the selected entity option to represent the entity state."""
        return getattr(self.coordinator.data.chars, self.entity_description.dict_key).name

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self.send(
            self.entity_description.dict_key,
            next(enum_option.value for enum_option in self.entity_description.enum if enum_option.name == option)
        )
