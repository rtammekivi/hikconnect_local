"""Hik-Connect Local: native LAN video for Hik-Connect indoor stations (CPD7)."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from .const import CONF_ACCOUNT, CONF_BASE_URL, CONF_PASSWORD, DEFAULT_BASE_URL, DOMAIN
from .hikconnect_api import HikConnectAuthError, HikConnectClient

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.CAMERA]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    client = HikConnectClient(
        entry.data[CONF_ACCOUNT],
        entry.data[CONF_PASSWORD],
        entry.data.get(CONF_BASE_URL, DEFAULT_BASE_URL),
    )

    def _login_and_list():
        client.login()
        return client.get_devices()

    try:
        devices = await hass.async_add_executor_job(_login_and_list)
    except HikConnectAuthError as err:
        raise ConfigEntryAuthFailed(str(err)) from err
    except Exception as err:  # noqa: BLE001
        raise ConfigEntryNotReady(f"Hik-Connect setup failed: {err}") from err

    streamable = [d for d in devices if d.local_ip]
    _LOGGER.info(
        "Hik-Connect Local: %d device(s), %d LAN-reachable", len(devices), len(streamable)
    )

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "client": client,
        "devices": streamable,
    }
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
