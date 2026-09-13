"""Number platform for UniFi Connect (brightness, volume)."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import UnifiConnectData
from .const import DOMAIN, NUMBERS
from .entity import UnifiConnectEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data: UnifiConnectData = hass.data[DOMAIN][entry.entry_id]
    coordinator = data.coordinator

    entities: list[NumberEntity] = []
    for device_id in coordinator.data:
        for key, spec in NUMBERS.items():
            if coordinator.device_supports(device_id, spec["action"]):
                entities.append(UnifiConnectNumber(coordinator, device_id, key, spec))

    async_add_entities(entities)


class UnifiConnectNumber(UnifiConnectEntity, NumberEntity):
    """A slider-style number backed by an action taking {"value": N}."""

    _attr_mode = NumberMode.SLIDER
    _attr_native_step = 1

    def __init__(self, coordinator, device_id: str, key: str, spec: dict) -> None:
        super().__init__(coordinator, device_id)
        self._spec = spec
        self._attr_unique_id = f"{device_id}_{key}"
        self._attr_name = spec["name"]
        self._attr_icon = spec.get("icon")
        self._attr_entity_registry_enabled_default = spec.get("verified", True)

    @property
    def native_min_value(self) -> float:
        flag = self.feature_flags.get(self._spec["feature_flag_key"], {})
        return float(flag.get("min", 0))

    @property
    def native_max_value(self) -> float:
        flag = self.feature_flags.get(self._spec["feature_flag_key"], {})
        return float(flag.get("max", 100))

    @property
    def native_value(self) -> float | None:
        value = self.shadow.get(self._spec["shadow_key"])
        return float(value) if value is not None else None

    async def async_set_native_value(self, value: float) -> None:
        await self.async_send_action(self._spec["action"], {"value": int(value)})
