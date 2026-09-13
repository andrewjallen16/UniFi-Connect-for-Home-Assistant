"""Text platform for UniFi Connect (web URL).

EXPERIMENTAL: the `load_website` action's args key was not directly
captured -- see const.ARGS_KEY_WEB_URL. Entity is disabled by default.
If it doesn't work, check Settings > System > Logs, filter `unifi_connect`,
and report the response body so ARGS_KEY_WEB_URL can be corrected.
"""
from __future__ import annotations

from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import UnifiConnectData
from .const import ARGS_KEY_WEB_URL, DOMAIN, TEXTS
from .entity import UnifiConnectEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data: UnifiConnectData = hass.data[DOMAIN][entry.entry_id]
    coordinator = data.coordinator

    entities: list[TextEntity] = []
    for device_id in coordinator.data:
        for key, spec in TEXTS.items():
            if coordinator.device_supports(device_id, spec["action"]):
                entities.append(UnifiConnectText(coordinator, device_id, key, spec))

    async_add_entities(entities)


class UnifiConnectText(UnifiConnectEntity, TextEntity):
    def __init__(self, coordinator, device_id: str, key: str, spec: dict) -> None:
        super().__init__(coordinator, device_id)
        self._spec = spec
        self._attr_unique_id = f"{device_id}_{key}"
        self._attr_name = spec["name"]
        self._attr_icon = spec.get("icon")
        self._attr_entity_registry_enabled_default = spec.get("verified", False)

    @property
    def native_value(self) -> str | None:
        return self.shadow.get(self._spec["shadow_key"])

    async def async_set_value(self, value: str) -> None:
        await self.async_send_action(
            self._spec["action"], {ARGS_KEY_WEB_URL: value}
        )
