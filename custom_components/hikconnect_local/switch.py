"""Switches: Do Not Disturb (account cloud) and DST (device time config)."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    client = data["client"]
    coordinator = data["status_coordinator"]
    entities = []
    for dev in data["devices"]:
        if not dev.locks:  # intercoms only
            continue
        entities.append(HikDndSwitch(coordinator, client, hass, dev.serial))
        entities.append(HikDstSwitch(coordinator, client, hass, dev.serial))
    async_add_entities(entities)


class _Base(CoordinatorEntity, SwitchEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, client, hass, serial):
        super().__init__(coordinator)
        self.hass = hass
        self._client = client
        self._serial = serial

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(identifiers={(DOMAIN, self._serial)})

    def _status(self) -> dict:
        return (self.coordinator.data or {}).get(self._serial) or {}


class HikDndSwitch(_Base):
    _attr_name = "Do not disturb"
    _attr_icon = "mdi:bell-off"

    def __init__(self, coordinator, client, hass, serial):
        super().__init__(coordinator, client, hass, serial)
        self._attr_unique_id = f"{DOMAIN}_{serial}_dnd"

    @property
    def is_on(self) -> bool | None:
        return self._status().get("dnd")

    async def _set(self, on: bool) -> None:
        await self.hass.async_add_executor_job(self._client.set_dnd, self._serial, on)
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self, **kwargs) -> None:
        await self._set(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self._set(False)


class HikDstSwitch(_Base):
    _attr_name = "Daylight saving time"
    _attr_icon = "mdi:sun-clock"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, client, hass, serial):
        super().__init__(coordinator, client, hass, serial)
        self._attr_unique_id = f"{DOMAIN}_{serial}_dst"

    @property
    def is_on(self) -> bool | None:
        return self._status().get("dst")

    async def _set(self, on: bool) -> None:
        st = self._status()
        await self.hass.async_add_executor_job(
            _dst_call(self._client, self._serial, st, on)
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self, **kwargs) -> None:
        await self._set(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self._set(False)


def _dst_call(client, serial, status, on):
    """Return a thunk that writes DST while preserving the other time fields."""
    def work():
        client.set_time_config(
            serial,
            daylight_saving=1 if on else 0,
            time_zone=status.get("time_zone"),
            time_zone_no=status.get("time_zone_no"),
            time_format=status.get("time_format"),
        )
    return work
