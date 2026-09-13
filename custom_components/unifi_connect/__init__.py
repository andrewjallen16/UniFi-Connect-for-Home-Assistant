"""The UniFi Connect integration."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME, Platform
from aiohttp import CookieJar
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import UnifiConnectApiClient
from .const import CONF_VERIFY_SSL, DOMAIN
from .coordinator import UnifiConnectCoordinator

PLATFORMS: list[Platform] = [
    Platform.SWITCH,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.BUTTON,
    Platform.TEXT,
]


@dataclass
class UnifiConnectData:
    api: UnifiConnectApiClient
    coordinator: UnifiConnectCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up UniFi Connect from a config entry."""
    verify_ssl = entry.data.get(CONF_VERIFY_SSL, False)
    # Own session per entry: each console has its own (usually self-signed)
    # cert and its own verify_ssl preference, and we don't want an
    # authenticated session cookie for one console bleeding into another.
    # unsafe=True: see the matching comment in config_flow.py -- required
    # for the TOKEN cookie to actually stick when the console is addressed
    # by bare IP instead of a hostname.
    session = async_create_clientsession(
        hass, verify_ssl=verify_ssl, cookie_jar=CookieJar(unsafe=True)
    )

    api = UnifiConnectApiClient(
        session,
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        verify_ssl,
    )
    await api.async_login()

    coordinator = UnifiConnectCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = UnifiConnectData(
        api=api, coordinator=coordinator
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        data: UnifiConnectData = hass.data[DOMAIN].pop(entry.entry_id)
        await data.api._session.close()  # noqa: SLF001 - our own session, owned here
    return unload_ok
