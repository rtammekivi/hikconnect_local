"""Config flow for Hik-Connect Local."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import (
    CONF_ACCOUNT,
    CONF_BASE_URL,
    CONF_PASSWORD,
    DEFAULT_BASE_URL,
    DOMAIN,
)
from .hikconnect_api import HikConnectAuthError, HikConnectClient


class HikConnectLocalConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the Hik-Connect account login."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            client = HikConnectClient(
                user_input[CONF_ACCOUNT],
                user_input[CONF_PASSWORD],
                user_input.get(CONF_BASE_URL, DEFAULT_BASE_URL),
            )
            try:
                await self.hass.async_add_executor_job(client.login)
            except HikConnectAuthError:
                errors["base"] = "invalid_auth"
            except Exception:  # noqa: BLE001
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(user_input[CONF_ACCOUNT].lower())
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_ACCOUNT], data=user_input
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_ACCOUNT): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Optional(CONF_BASE_URL, default=DEFAULT_BASE_URL): str,
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )
