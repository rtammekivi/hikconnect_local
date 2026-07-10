"""Call-status sensor for a Hik-Connect indoor station.

State comes from the authoritative cloud poll (idle / ringing / call in
progress). The MQTT push listener (see ``push.py``) triggers an immediate
coordinator refresh on a call event, so ringing appears in near real time
without having to interpret opaque push alert codes.
"""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CALL_STATES, DOMAIN

_ICONS = {
    "idle": "mdi:phone-hangup",
    "ringing": "mdi:phone-ring",
    "call in progress": "mdi:phone-in-talk",
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    async_add_entities(
        HikCallStatusSensor(coordinator, dev.serial) for dev in data["devices"]
    )


class HikCallStatusSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Call status"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = CALL_STATES

    def __init__(self, coordinator, serial):
        super().__init__(coordinator)
        self._serial = serial
        self._attr_unique_id = f"{DOMAIN}_{serial}_call_status"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(identifiers={(DOMAIN, self._serial)})

    def _entry(self) -> dict:
        return (self.coordinator.data or {}).get(self._serial) or {}

    @property
    def native_value(self) -> str | None:
        status = self._entry().get("status")
        return status if status in CALL_STATES else None  # reserved states -> unknown

    @property
    def icon(self) -> str:
        return _ICONS.get(self.native_value, "mdi:phone-alert")

    @property
    def extra_state_attributes(self) -> dict:
        return self._entry().get("info") or {}
