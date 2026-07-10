"""Call-operation buttons (answer / cancel / hangup) for a Hik-Connect station."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

# (key, label, icon, api-method name)
_BUTTONS = (
    ("answer", "Answer call", "mdi:phone", "answer_call"),
    ("hangup", "Hang up call", "mdi:phone-hangup", "hangup_call"),
    ("cancel", "Cancel call", "mdi:phone-cancel", "cancel_call"),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    client = data["client"]
    entities = [
        HikCallButton(hass, client, dev.serial, *spec)
        for dev in data["devices"]
        for spec in _BUTTONS
    ]
    async_add_entities(entities)


class HikCallButton(ButtonEntity):
    _attr_has_entity_name = True

    def __init__(self, hass, client, serial, key, label, icon, method):
        self.hass = hass
        self._client = client
        self._serial = serial
        self._method = method
        self._attr_name = label
        self._attr_icon = icon
        self._attr_unique_id = f"{DOMAIN}_{serial}_{key}"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(identifiers={(DOMAIN, self._serial)})

    async def async_press(self) -> None:
        await self.hass.async_add_executor_job(
            getattr(self._client, self._method), self._serial
        )
