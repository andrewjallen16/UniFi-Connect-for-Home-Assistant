"""Config flow for UniFi Connect."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
from aiohttp import CookieJar
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import UnifiConnectApiClient, UnifiConnectApiError, UnifiConnectAuthError
from .const import CONF_VERIFY_SSL, DEFAULT_PORT, DEFAULT_VERIFY_SSL, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): bool,
    }
)


class UnifiConnectConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for UniFi Connect."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(
                f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}"
            )
            self._abort_if_unique_id_configured()

            # Own, non-shared session: console TLS certs are self-signed and
            # verify_ssl is per-entry, so this must not be the HA-shared session.
            # unsafe=True is required because the console is usually addressed
            # by bare IP -- aiohttp's default cookie jar silently drops
            # Set-Cookie headers for IP-address hosts otherwise, which makes
            # a perfectly successful login look like a bad password.
            session = async_create_clientsession(
                self.hass,
                verify_ssl=user_input[CONF_VERIFY_SSL],
                cookie_jar=CookieJar(unsafe=True),
            )
            api = UnifiConnectApiClient(
                session,
                user_input[CONF_HOST],
                user_input[CONF_PORT],
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
                user_input[CONF_VERIFY_SSL],
            )
            try:
                await api.async_login()
                await api.async_get_devices()
            except UnifiConnectAuthError:
                errors["base"] = "invalid_auth"
            except (UnifiConnectApiError, aiohttp.ClientError):
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error during setup validation")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"UniFi Connect ({user_input[CONF_HOST]})",
                    data=user_input,
                )
            finally:
                await session.close()

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors
        )
