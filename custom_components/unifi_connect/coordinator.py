"""Coordinator for the UniFi Connect integration."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import UnifiConnectApiClient, UnifiConnectApiError, UnifiConnectAuthError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class UnifiConnectCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Polls the console and keeps devices indexed by id."""

    def __init__(self, hass: HomeAssistant, api: UnifiConnectApiClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        try:
            devices = await self.api.async_get_devices()
        except UnifiConnectAuthError as err:
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except UnifiConnectApiError as err:
            raise UpdateFailed(f"Error communicating with console: {err}") from err

        _LOGGER.debug(
            "Fetched %d device(s): %s",
            len(devices),
            [
                (d.get("name"), d.get("type", {}).get("platform"))
                for d in devices
            ],
        )

        return {d["id"]: d for d in devices if "id" in d}

    def get_action(self, device_id: str, action_name: str) -> dict[str, Any] | None:
        """Look up an action's uuid by name for a given device."""
        device = self.data.get(device_id) if self.data else None
        if not device:
            return None
        for action in device.get("type", {}).get("supportedActions", []):
            if action.get("name") == action_name:
                return action
        return None

    def device_supports(self, device_id: str, *action_names: str) -> bool:
        """True if the device's supportedActions includes ALL given names."""
        device = self.data.get(device_id) if self.data else None
        if not device:
            return False
        supported = {
            a.get("name") for a in device.get("type", {}).get("supportedActions", [])
        }
        return all(name in supported for name in action_names)
