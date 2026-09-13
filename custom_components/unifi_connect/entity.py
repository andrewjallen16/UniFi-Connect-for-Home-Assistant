"""Base entity for UniFi Connect devices."""
from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import UnifiConnectCoordinator


class UnifiConnectEntity(CoordinatorEntity[UnifiConnectCoordinator]):
    """Common device_info / availability handling for one Connect device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: UnifiConnectCoordinator, device_id: str) -> None:
        super().__init__(coordinator)
        self._device_id = device_id

    @property
    def device(self) -> dict[str, Any]:
        return self.coordinator.data.get(self._device_id, {})

    @property
    def shadow(self) -> dict[str, Any]:
        return self.device.get("shadow", {})

    @property
    def feature_flags(self) -> dict[str, Any]:
        return self.device.get("featureFlags", {})

    @property
    def available(self) -> bool:
        return super().available and self._device_id in (self.coordinator.data or {})

    @property
    def device_info(self) -> DeviceInfo:
        device = self.device
        type_info = device.get("type", {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("name") or type_info.get("fullName", "UniFi Connect Device"),
            manufacturer="Ubiquiti",
            model=type_info.get("fullName") or type_info.get("platform"),
            sw_version=device.get("firmwareVersion"),
            connections={("mac", device.get("mac"))} if device.get("mac") else set(),
        )

    async def async_send_action(self, action_name: str, args: dict | None = None) -> None:
        action = self.coordinator.get_action(self._device_id, action_name)
        if action is None:
            raise RuntimeError(
                f"Device {self._device_id} does not support action '{action_name}'"
            )
        await self.coordinator.api.async_send_action(
            self._device_id, action["id"], action_name, args
        )
        await self.coordinator.async_request_refresh()
