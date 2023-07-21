"""ZagonelEntity class."""
from __future__ import annotations

from typing import Any, Optional

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN, NAME, VERSION
from .coordinator import ZagonelDataUpdateCoordinator


class ZagonelEntity(CoordinatorEntity[ZagonelDataUpdateCoordinator]):
    """ZagonelEntity class."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(self, unique_id: str, coordinator: ZagonelDataUpdateCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_unique_id = unique_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.data.chars.Device_Id)},
            name=NAME,
            model=VERSION,
            manufacturer=NAME,
        )

    async def send(self, command: str, value: Optional[Any] = None):
        """send."""
        payload = {
            "command": command
        }
        if value is not None:
            payload["value"] = value
        await self.coordinator.client.send_command(payload)
        await self.coordinator.async_refresh()

