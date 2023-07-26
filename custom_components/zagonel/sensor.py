"""Sensor platform for zagonel."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar
from collections.abc import Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription, SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS,
    UnitOfElectricPotential,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
    UnitOfVolume,
)
from homeassistant.util import slugify

from .const import DOMAIN
from .coordinator import ZagonelDataUpdateCoordinator
from .entity import ZagonelEntity

T = TypeVar("T")


@dataclass
class ZagonelSensorEntityDescriptionMixin:
    """ZagonelSensorEntityDescriptionMixin."""

    value: Callable[[T], T] = None


@dataclass
class ZagonelSensorEntityDescription(
    ZagonelSensorEntityDescriptionMixin, SensorEntityDescription
):
    """ZagonelSensorEntityDescription."""


ENTITY_DESCRIPTIONS = (
    ZagonelSensorEntityDescription(
        key="St",
        name="State",
        translation_key="shower_state",
        value=lambda value: str(value).lower(),
    ),
    ZagonelSensorEntityDescription(
        key="Fl",
        name="Water Flow",
        translation_key="shower_water_flow",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.WATER,
        native_unit_of_measurement=f"{UnitOfVolume.MILLILITERS}/m",
    ),
    ZagonelSensorEntityDescription(
        key="Vi",
        name="Voltage",
        translation_key="shower_voltage",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_display_precision=2,
        value=lambda value: value / 1000,
    ),
    ZagonelSensorEntityDescription(
        key="Ti",
        name="Ti",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ZagonelSensorEntityDescription(
        key="Ts",
        name="Current Temperature Target",
        translation_key="shower_expected_temperature",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value=lambda value: value / 1000,
    ),
    ZagonelSensorEntityDescription(
        key="Ps",
        name="Current Power Factor",
        translation_key="shower_power_factor",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER_FACTOR,
        native_unit_of_measurement=PERCENTAGE,
    ),
    ZagonelSensorEntityDescription(
        key="De",
        name="Target Power",
        translation_key="shower_target_power",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        value=lambda value: 8000 - value,
    ),
    ZagonelSensorEntityDescription(
        key="Pw",
        name="Power",
        translation_key="shower_power",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        value=lambda value: value / 10,
    ),
    ZagonelSensorEntityDescription(
        key="Hp",
        name="Hp",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ZagonelSensorEntityDescription(
        key="Up",
        name="Uptime",
        translation_key="shower_uptime",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
    ),
    ZagonelSensorEntityDescription(
        key="Pp",
        name="Pp",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ZagonelSensorEntityDescription(
        key="Wi",
        name="Wifi strength",
        translation_key="shower_wifi_strength",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS,
    ),
)


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    unique_id = slugify(coordinator.data.chars.Device_Id)
    async_add_devices(
        ZagonelSensor(
            unique_id=f"{entity_description.key}_{unique_id}",
            coordinator=coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class ZagonelSensor(ZagonelEntity, SensorEntity):
    """Zagonel Binary Sensor class."""

    entity_description: ZagonelSensorEntityDescription

    def __init__(
            self,
            unique_id: str,
            coordinator: ZagonelDataUpdateCoordinator,
            entity_description: ZagonelSensorEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(unique_id, coordinator)
        self.entity_description = entity_description

    @property
    def native_value(self):
        """Return the value reported by the sensor."""
        value = getattr(self.coordinator.data.status, self.entity_description.key)
        if self.entity_description.value:
            return self.entity_description.value(value)
        return value
