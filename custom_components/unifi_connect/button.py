"""Button platform for UniFi Connect (reboot, refresh web page)."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import UnifiConnectData
from .const import BUTTONS, DOMAIN
from .entity import UnifiConnectEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data: UnifiConnectData = hass.data[DOMAIN][entry.entry_id]
    coordinator = data.coordinator

    entities: list[ButtonEntity] = []
    for device_id in coordinator.data:
        for key, spec in BUTTONS.items():
            if coordinator.device_supports(device_id, spec["action"]):
                entities.append(UnifiConnectButton(coordinator, device_id, key, spec))

    async_add_entities(entities)


class UnifiConnectButton(UnifiConnectEntity, ButtonEntity):
    def __init__(self, coordinator, device_id: str, key: str, spec: dict) -> None:
        super().__init__(coordinator, device_id)
        self._spec = spec
        self._attr_unique_id = f"{device_id}_{key}"
        self._attr_name = spec["name"]
        self._attr_icon = spec.get("icon")

    async def async_press(self) -> None:
        await self.async_send_action(self._spec["action"])
