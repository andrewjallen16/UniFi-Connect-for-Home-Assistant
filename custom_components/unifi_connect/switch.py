"""Switch platform for UniFi Connect."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import UnifiConnectData
from .const import DOMAIN, TOGGLE_SWITCHES, VALUE_TOGGLE_SWITCHES
from .entity import UnifiConnectEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data: UnifiConnectData = hass.data[DOMAIN][entry.entry_id]
    coordinator = data.coordinator

    entities: list[SwitchEntity] = []
    for device_id in coordinator.data:
        for key, spec in TOGGLE_SWITCHES.items():
            if coordinator.device_supports(
                device_id, spec["on_action"], spec["off_action"]
            ):
                entities.append(
                    UnifiConnectToggleSwitch(coordinator, device_id, key, spec)
                )
        for key, spec in VALUE_TOGGLE_SWITCHES.items():
            if coordinator.device_supports(device_id, spec["action"]):
                entities.append(
                    UnifiConnectValueToggleSwitch(coordinator, device_id, key, spec)
                )

    async_add_entities(entities)


class UnifiConnectToggleSwitch(UnifiConnectEntity, SwitchEntity):
    """A switch backed by two zero-arg actions (on_action / off_action)."""

    def __init__(self, coordinator, device_id: str, key: str, spec: dict) -> None:
        super().__init__(coordinator, device_id)
        self._spec = spec
        self._attr_unique_id = f"{device_id}_{key}"
        self._attr_name = spec["name"]
        self._attr_icon = spec.get("icon")
        self._attr_entity_registry_enabled_default = spec.get("verified", True)

    @property
    def is_on(self) -> bool | None:
        return self.shadow.get(self._spec["shadow_key"])

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.async_send_action(self._spec["on_action"])

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.async_send_action(self._spec["off_action"])


class UnifiConnectValueToggleSwitch(UnifiConnectEntity, SwitchEntity):
    """A switch backed by a single action sent with {"value": bool}.

    Unverified envelope -- see const.py. Disabled by default.
    """

    def __init__(self, coordinator, device_id: str, key: str, spec: dict) -> None:
        super().__init__(coordinator, device_id)
        self._spec = spec
        self._attr_unique_id = f"{device_id}_{key}"
        self._attr_name = spec["name"]
        self._attr_icon = spec.get("icon")
        self._attr_entity_registry_enabled_default = spec.get("verified", False)

    @property
    def is_on(self) -> bool | None:
        return self.shadow.get(self._spec["shadow_key"])

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.async_send_action(self._spec["action"], {"value": True})

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.async_send_action(self._spec["action"], {"value": False})
