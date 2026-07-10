"""Config flow for Hik-Connect Local."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_ACCOUNT,
    CONF_BASE_URL,
    CONF_PASSWORD,
    CONF_SERVER,
    DEFAULT_BASE_URL,
    DOMAIN,
    SERVER_CUSTOM,
    SERVERS,
)
from .hikconnect_api import HikConnectAuthError, HikConnectClient


def _resolve_base_url(user_input: dict[str, Any]) -> str | None:
    """Map the selected server (or custom override) to a base URL."""
    server = user_input.get(CONF_SERVER, DEFAULT_BASE_URL)
    if server != SERVER_CUSTOM:
        return server
    custom = (user_input.get(CONF_BASE_URL) or "").strip().rstrip("/")
    if not custom:
        return None
    if not custom.startswith(("http://", "https://")):
        custom = f"https://{custom}"
    return custom


class HikConnectLocalConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the Hik-Connect account login."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            base_url = _resolve_base_url(user_input)
            if base_url is None:
                errors["base"] = "custom_url_required"
            else:
                client = HikConnectClient(
                    user_input[CONF_ACCOUNT], user_input[CONF_PASSWORD], base_url
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
                        title=user_input[CONF_ACCOUNT],
                        data={
                            CONF_ACCOUNT: user_input[CONF_ACCOUNT],
                            CONF_PASSWORD: user_input[CONF_PASSWORD],
                            CONF_BASE_URL: base_url,
                        },
                    )

        options = [
            SelectOptionDict(value=url, label=label) for url, label in SERVERS.items()
        ]
        options.append(SelectOptionDict(value=SERVER_CUSTOM, label="Custom…"))
        schema = vol.Schema(
            {
                vol.Required(CONF_ACCOUNT): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Required(CONF_SERVER, default=DEFAULT_BASE_URL): SelectSelector(
                    SelectSelectorConfig(
                        options=options, mode=SelectSelectorMode.DROPDOWN
                    )
                ),
                vol.Optional(CONF_BASE_URL): str,
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )
