"""Local API client for a UniFi OS console's UniFi Connect app.

Endpoints and payload shapes below were captured directly from a live
console (browser DevTools / HAR export) rather than from any published
Ubiquiti documentation -- UniFi Connect's local API is not publicly
documented. See the project README for the raw capture this was built
from.

Confirmed from a real capture:
    GET  {base}/devices?shadow=true
    PATCH {base}/devices/{deviceId}/status
        body: {"id": "<action-uuid>", "name": "<action-name>", "args": {...}}
        resp: {"err": null, "type": "single", "data": "OK"}

Login uses the standard UniFi OS local-console pattern (shared by the
official Network/Protect/Access local APIs): POST username/password,
receive a `TOKEN` session cookie (a JWT), then read a `csrfToken` claim out
of that JWT and send it back as `X-CSRF-Token` on subsequent mutating
requests. This part was not captured directly in the HAR (cookies are
stripped from HAR exports by the browser), but matches the x-csrf-token
header format seen on every captured PATCH call, and is the well-known
mechanism used by other local UniFi OS integrations.
"""
from __future__ import annotations

import base64
import json
import logging
from typing import Any

import aiohttp

from .const import API_BASE_PATH, LOGIN_PATH

_LOGGER = logging.getLogger(__name__)


class UnifiConnectApiError(Exception):
    """Generic API error."""


class UnifiConnectAuthError(UnifiConnectApiError):
    """Raised when login fails or the session has expired."""


class UnifiConnectApiClient:
    """Talks to a single UniFi OS console's local UniFi Connect API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int,
        username: str,
        password: str,
        verify_ssl: bool = False,
    ) -> None:
        self._session = session
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._verify_ssl = verify_ssl
        self._csrf_token: str | None = None

    @property
    def base_url(self) -> str:
        return f"https://{self._host}:{self._port}"

    @property
    def api_url(self) -> str:
        return f"{self.base_url}{API_BASE_PATH}"

    async def async_login(self) -> None:
        """Authenticate against the console and cache the CSRF token."""
        url = f"{self.base_url}{LOGIN_PATH}"
        try:
            resp = await self._session.post(
                url,
                json={
                    "username": self._username,
                    "password": self._password,
                    "rememberMe": False,
                },
                ssl=self._verify_ssl,
            )
        except aiohttp.ClientError as err:
            raise UnifiConnectApiError(f"Error connecting to {url}: {err}") from err

        if resp.status in (400, 401):
            raise UnifiConnectAuthError("Invalid username or password")
        if resp.status != 200:
            text = await resp.text()
            raise UnifiConnectApiError(
                f"Unexpected login response {resp.status}: {text[:200]}"
            )

        token_cookie = self._session.cookie_jar.filter_cookies(self.base_url).get(
            "TOKEN"
        )
        if token_cookie is None:
            # Distinct from bad credentials: the console accepted the
            # login (200 OK) but we never got the session cookie back into
            # our own cookie jar. Historically caused by aiohttp's default
            # cookie jar dropping cookies for bare-IP hosts -- see the
            # cookie_jar=CookieJar(unsafe=True) setup in config_flow.py /
            # __init__.py. If you hit this after that fix is in place,
            # something else is stripping the cookie (proxy, firewall, etc).
            raise UnifiConnectApiError(
                "Login returned 200 but no TOKEN session cookie was captured "
                "-- this is a session/cookie-jar problem, not invalid "
                "credentials. See api.py for details."
            )

        self._csrf_token = self._extract_csrf_token(token_cookie.value)
        if not self._csrf_token:
            _LOGGER.debug(
                "Could not derive a CSRF token from the session cookie; "
                "mutating requests (switches/numbers/etc.) may fail with a "
                "403 until this is fixed."
            )

    @staticmethod
    def _extract_csrf_token(jwt_value: str) -> str | None:
        """Pull the `csrfToken` claim out of the TOKEN cookie's JWT payload.

        Does not verify the signature -- we're only reading a claim
        already handed to us by our own authenticated session.
        """
        try:
            payload_segment = jwt_value.split(".")[1]
            padding = "=" * (-len(payload_segment) % 4)
            payload = json.loads(
                base64.urlsafe_b64decode(payload_segment + padding)
            )
            return payload.get("csrfToken")
        except Exception:  # noqa: BLE001 - best-effort parsing of a token blob
            return None

    async def _request(
        self, method: str, path: str, retry_on_auth_error: bool = True, **kwargs
    ) -> Any:
        url = f"{self.api_url}{path}"
        headers = kwargs.pop("headers", {})
        if method != "GET" and self._csrf_token:
            headers["X-CSRF-Token"] = self._csrf_token

        try:
            resp = await self._session.request(
                method, url, headers=headers, ssl=self._verify_ssl, **kwargs
            )
        except aiohttp.ClientError as err:
            raise UnifiConnectApiError(f"Error calling {url}: {err}") from err

        if resp.status in (401, 403) and retry_on_auth_error:
            _LOGGER.debug("Session expired or rejected, re-authenticating")
            await self.async_login()
            return await self._request(
                method, path, retry_on_auth_error=False, **kwargs
            )

        if resp.status != 200:
            text = await resp.text()
            raise UnifiConnectApiError(
                f"{method} {url} -> {resp.status}: {text[:300]}"
            )

        return await resp.json()

    async def async_get_devices(self) -> list[dict[str, Any]]:
        """Return the full device collection (adopted UniFi Connect devices)."""
        data = await self._request("GET", "/devices", params={"shadow": "true"})
        return data.get("data", [])

    async def async_send_action(
        self, device_id: str, action_id: str, action_name: str, args: dict | None = None
    ) -> None:
        """Send a device action, e.g. brightness/volume/switch/display_on."""
        body = {"id": action_id, "name": action_name, "args": args or {}}
        result = await self._request(
            "PATCH", f"/devices/{device_id}/status", json=body
        )
        if result.get("err"):
            raise UnifiConnectApiError(
                f"Action {action_name} on {device_id} failed: {result['err']}"
            )
