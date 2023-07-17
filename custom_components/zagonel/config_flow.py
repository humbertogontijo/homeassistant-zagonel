"""Adds config flow for Zagonel."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

from .api import (
    ZagonelApiClient,
    ZagonelApiClientAuthenticationError,
    ZagonelApiClientCommunicationError,
    ZagonelApiClientError,
)
from .const import CONF_DEVICE_ID, DOMAIN, LOGGER


class ZagonelFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Zagonel."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.FlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            try:
                await self._test_credentials(
                    device_id=user_input[CONF_DEVICE_ID]
                )
            except ZagonelApiClientAuthenticationError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "auth"
            except ZagonelApiClientCommunicationError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except ZagonelApiClientError as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_DEVICE_ID],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_DEVICE_ID,
                        default=(user_input or {}).get(CONF_DEVICE_ID),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
                }
            ),
            errors=_errors,
        )

    async def _test_credentials(self, device_id: str) -> None:
        """Validate credentials."""
        client = ZagonelApiClient(
            device_id=device_id,
        )
        await client.async_load_data()
