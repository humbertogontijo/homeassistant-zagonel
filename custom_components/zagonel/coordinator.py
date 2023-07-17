"""DataUpdateCoordinator for zagonel."""
from __future__ import annotations

import asyncio
from datetime import timedelta

import async_timeout
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import (
    ZagonelApiClient,
    ZagonelApiClientAuthenticationError,
    ZagonelApiClientError, ZagonelData,
)
from .const import DOMAIN, LOGGER


class ZagonelDataUpdateCoordinator(DataUpdateCoordinator[ZagonelData]):
    """Class to manage fetching data from the API."""

    config_entry: ConfigEntry

    def __init__(
            self,
            hass: HomeAssistant,
            client: ZagonelApiClient,
    ) -> None:
        """Initialize."""
        self.client = client
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=5),
        )
        self.scheduled_refresh: asyncio.TimerHandle | None = None

    def schedule_refresh(self) -> None:
        """Schedule coordinator refresh after 1 second."""
        if self.scheduled_refresh:
            self.scheduled_refresh.cancel()
        self.scheduled_refresh = self.hass.loop.call_later(
            1, lambda: asyncio.create_task(self.async_refresh())
        )

    def release(self) -> None:
        """Disconnect from API."""
        if self.scheduled_refresh:
            self.scheduled_refresh.cancel()

    async def _async_update_data(self):
        """Update data via library."""
        try:
            async with async_timeout.timeout(5):
                await self.client.async_load_data()
                return self.client.data
        except TimeoutError as exception:
            raise UpdateFailed(exception) from exception
        except ZagonelApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except ZagonelApiClientError as exception:
            raise UpdateFailed(exception) from exception
