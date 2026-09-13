"""Select platform for UniFi Connect (display mode: web/app/youtube/etc)."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import UnifiConnectData
from .const import DOMAIN, SELECTS
from .entity import UnifiConnectEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data: UnifiConnectData = hass.data[DOMAIN][entry.entry_id]
    coordinator = data.coordinator

    entities: list[SelectEntity] = []
    for device_id in coordinator.data:
        for key, spec in SELECTS.items():
            if coordinator.device_supports(device_id, spec["action"]):
                entities.append(UnifiConnectSelect(coordinator, device_id, key, spec))

    async_add_entities(entities)


class UnifiConnectSelect(UnifiConnectEntity, SelectEntity):
    """A select backed by an action taking {"<args_key>": <option>}."""

    def __init__(self, coordinator, device_id: str, key: str, spec: dict) -> None:
        super().__init__(coordinator, device_id)
        self._spec = spec
        self._attr_unique_id = f"{device_id}_{key}"
        self._attr_name = spec["name"]
        self._attr_icon = spec.get("icon")
        self._attr_entity_registry_enabled_default = spec.get("verified", True)

    @property
    def options(self) -> list[str]:
        flag = self.feature_flags.get(self._spec["feature_flag_key"], {})
        return flag.get("enum", [])

    @property
    def current_option(self) -> str | None:
        return self.shadow.get(self._spec["shadow_key"])

    async def async_select_option(self, option: str) -> None:
        await self.async_send_action(
            self._spec["action"], {self._spec["args_key"]: option}
        )
