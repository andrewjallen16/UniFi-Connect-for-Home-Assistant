# UniFi Connect for Home Assistant

A HACS-installable custom integration for **UniFi Connect** devices
(Displays, Cast, Cast Pro, and any future device using the same local API),
built from a real network capture of a UniFi console rather than guesswork.

This talks directly to your UniFi Console's local, undocumented UniFi
Connect API — there is no cloud dependency and no official Ubiquiti API
this is built against, so treat it as unofficial and best-effort.

## Why this exists / how it differs from other UC integrations

Earlier community integrations for UniFi Connect hardcoded support for a
single model (`UC-Display-SE-21`), so other devices — including UC Display
7/13 and UC Cast/Cast Pro — showed up as zero devices. This version instead:

- Fetches the full device list (`GET /devices?shadow=true`) and creates
  entities for **any** device, generically.
- Decides which entities to create per-device by reading that device's own
  `type.supportedActions` and `featureFlags` — a UC Cast won't get a "Sleep
  Mode" switch because its `supportedActions` doesn't include
  `enable_sleep`/`disable_sleep`; a UC Display will.
- Uses per-device brightness/volume ranges and mode options straight from
  `featureFlags`, instead of hardcoded numbers.

## What's confirmed vs. best-effort

Every action envelope below was either captured directly from a live
console (browser DevTools / HAR), or shares the *exact same* zero-argument
envelope as one that was.

| Entity | Action(s) | Status |
|---|---|---|
| Display Power (switch) | `display_on` / `display_off` | ✅ Captured |
| Brightness (number) | `brightness` `{"value": N}` | ✅ Captured |
| Volume (number) | `volume` `{"value": N}` | ✅ Captured |
| Mode (select) | `switch` `{"mode": "..."}` | ✅ Captured |
| Sleep Mode, Auto Rotate, Auto Reload, Memorize Playlist, Locating (switches) | `enable_x`/`disable_x` or `start_x`/`stop_x` | ⚠️ Same zero-arg envelope as Display Power, not individually captured |
| Reboot, Reload Web Page (buttons) | `reboot`, `refresh_website` | ⚠️ Same zero-arg envelope, not individually captured |
| CEC Auto Power On/Off (switches) | `cec_auto_on` / `cec_auto_off` `{"value": bool}` | ⚠️ Unverified args shape — **disabled by default** |
| Web URL (text) | `load_website` `{"url": "..."}` | ⚠️ Args key name guessed — **disabled by default** |

If a "⚠️" entity doesn't work: **Settings → System → Logs**, filter for
`unifi_connect`, try the action once, and send the resulting error/response
back — it's usually a one-line fix in `const.py`.

## Prerequisites

You need a **local-only** UniFi OS admin account (this does not work with
cloud/SSO-only accounts or accounts with 2FA):

1. Open your console's local web UI (e.g. `https://192.168.1.1`).
2. **Settings → Admins & Users → Add Admin**.
3. Choose **Local Access Only**.
4. Grant **Full Management** access to UniFi Connect.

## Installation

### HACS (custom repository)

1. HACS → Integrations → ⋮ menu → **Custom repositories**.
2. Add this repo's URL, category **Integration**.
3. Search for **UniFi Connect**, install, restart Home Assistant.

### Manual

1. Copy `custom_components/unifi_connect` into your
   `config/custom_components/` directory.
2. Restart Home Assistant.

## Configuration

**Settings → Devices & Services → Add Integration → UniFi Connect**, then
enter:

- **Host** — your console's IP or hostname
- **Port** — defaults to `443`
- **Username / Password** — the local-only account above
- **Verify SSL** — leave off unless you've installed a trusted cert on your
  console (self-signed certs are the default)

## How it works

- Polls `GET {console}/proxy/connect/api/v2/devices?shadow=true` every 30
  seconds.
- Sends commands as `PATCH {console}/proxy/connect/api/v2/devices/{id}/status`
  with body `{"id": "<action-uuid>", "name": "<action-name>", "args": {...}}`,
  where the action uuid is looked up from that specific device's own
  `type.supportedActions` list (these uuids are per-device-type, not
  global).
- Authenticates using the standard UniFi OS local-console pattern: POST
  username/password to `/api/auth/login`, then derive an `X-CSRF-Token`
  header from the resulting session cookie for all mutating requests.
  Re-authenticates automatically on a 401/403.

## Known limitations

- Local console API only — no cloud/remote-access support, and no support
  for accounts with 2FA.
- Read-only fields present in the raw device data (network info, firmware
  version, resolution, etc.) aren't yet exposed as sensors — device_info
  shows firmware version on the device page, but nothing sensor-level yet.
  Straightforward to add if wanted.
- `load_website` (Web URL) and the CEC switches are unverified — see table
  above.

## Contributing

If you capture the real payload for one of the "⚠️ unverified" rows above
(browser DevTools → Network → right-click the request → Copy as cURL),
open an issue or PR with it and it can be marked as confirmed and enabled
by default.
