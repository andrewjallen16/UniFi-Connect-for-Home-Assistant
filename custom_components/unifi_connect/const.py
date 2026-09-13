"""Constants for the UniFi Connect integration."""
from __future__ import annotations

DOMAIN = "unifi_connect"

CONF_VERIFY_SSL = "verify_ssl"

DEFAULT_PORT = 443
DEFAULT_VERIFY_SSL = False
DEFAULT_SCAN_INTERVAL = 30  # seconds

API_BASE_PATH = "/proxy/connect/api/v2"
LOGIN_PATH = "/api/auth/login"

# ---------------------------------------------------------------------------
# Capability tables.
#
# These are keyed off the REAL `type.supportedActions` (by "name") and
# `shadow` fields captured from a live UniFi Connect console (see the
# project README for the raw capture). Entities are only created for a given
# device if that device's `supportedActions` actually contains the required
# action name(s) -- so a UC Cast (no sleep/rotate actions) simply won't get
# a Sleep Mode or Auto Rotate switch, while a UC Display will.
#
# This is intentionally NOT keyed by device model/platform string, so any
# current or future UniFi Connect device that exposes these standard
# actions will be picked up automatically.
# ---------------------------------------------------------------------------

# Simple boolean toggles: two zero-arg actions (on_action / off_action),
# reflecting a boolean field in `shadow`.
# Verified against a real capture: display_on/display_off.
# The remaining enable_x/disable_x pairs use the identical zero-arg
# envelope, so they're implemented the same way, but have not each been
# individually captured -- check Settings > System > Logs > unifi_connect
# if one of these doesn't seem to take effect, and please report back.
TOGGLE_SWITCHES = {
    "display_power": {
        "name": "Display Power",
        "shadow_key": "display",
        "on_action": "display_on",
        "off_action": "display_off",
        "verified": True,
        "icon": "mdi:monitor",
    },
    "sleep_mode": {
        "name": "Sleep Mode",
        "shadow_key": "sleepMode",
        "on_action": "enable_sleep",
        "off_action": "disable_sleep",
        "verified": False,
        "icon": "mdi:sleep",
    },
    "auto_rotate": {
        "name": "Auto Rotate",
        "shadow_key": "autoRotate",
        "on_action": "enable_auto_rotate",
        "off_action": "disable_auto_rotate",
        "verified": False,
        "icon": "mdi:screen-rotation",
    },
    "auto_reload": {
        "name": "Auto Reload",
        "shadow_key": "autoReload",
        "on_action": "enable_auto_reload",
        "off_action": "disable_auto_reload",
        "verified": False,
        "icon": "mdi:refresh-auto",
    },
    "memorize_playlist": {
        "name": "Memorize Playlist",
        "shadow_key": "memorizePlaylist",
        "on_action": "enable_memorize_playlist",
        "off_action": "disable_memorize_playlist",
        "verified": False,
        "icon": "mdi:playlist-check",
    },
    "locating": {
        "name": "Locating",
        "shadow_key": "locating",
        "on_action": "start_locating",
        "off_action": "stop_locating",
        "verified": False,
        "icon": "mdi:map-marker-radius",
    },
}

# Single-action boolean toggles where the SAME action name is sent with a
# `value` arg for on/off, instead of two separate action names. Unverified
# -- CEC auto-on/auto-off appear in supportedActions without an obvious
# disable_* counterpart, so this is the best-guess envelope shared by every
# other value-carrying action (brightness/volume use {"value": N}).
# Disabled by default until confirmed.
VALUE_TOGGLE_SWITCHES = {
    "cec_auto_on": {
        "name": "CEC Auto Power On",
        "shadow_key": "cecAutoOn",
        "action": "cec_auto_on",
        "verified": False,
        "icon": "mdi:hdmi-port",
    },
    "cec_auto_off": {
        "name": "CEC Auto Power Off",
        "shadow_key": "cecAutoOff",
        "action": "cec_auto_off",
        "verified": False,
        "icon": "mdi:hdmi-port",
    },
}

# Numbers: action + args{"value": N}, range comes from the device's own
# featureFlags rather than a hardcoded min/max.
# Verified against a real capture: both brightness and volume.
NUMBERS = {
    "brightness": {
        "name": "Brightness",
        "shadow_key": "brightness",
        "action": "brightness",
        "feature_flag_key": "brightness",
        "verified": True,
        "icon": "mdi:brightness-6",
    },
    "volume": {
        "name": "Volume",
        "shadow_key": "volume",
        "action": "volume",
        "feature_flag_key": "volume",
        "verified": True,
        "icon": "mdi:volume-high",
    },
}

# Selects: action "switch" + args{"mode": <option>}, options come from
# featureFlags.mode.enum.
# Verified against a real capture.
SELECTS = {
    "mode": {
        "name": "Mode",
        "shadow_key": "mode",
        "action": "switch",
        "args_key": "mode",
        "feature_flag_key": "mode",
        "verified": True,
        "icon": "mdi:tune-variant",
    },
}

# Buttons: zero-arg, fire-and-forget actions.
# Verified against a real capture: none of these individually, but they
# share the exact zero-arg envelope proven by display_on/display_off.
BUTTONS = {
    "reboot": {"name": "Reboot", "action": "reboot", "icon": "mdi:restart"},
    "refresh_website": {
        "name": "Reload Web Page",
        "action": "refresh_website",
        "icon": "mdi:refresh",
    },
}

# Text: action "load_website" + args{<key>: <url>}. The exact args key
# name was NOT captured -- "url" is a best guess based on the field name
# `currentHomePage` in `shadow`. Disabled by default until confirmed; check
# the debug logs after setting a value and adjust ARGS_KEY_WEB_URL below if
# the console returns an error instead of {"err": null}.
ARGS_KEY_WEB_URL = "url"
TEXTS = {
    "web_url": {
        "name": "Web URL",
        "shadow_key": "currentHomePage",
        "action": "load_website",
        "verified": False,
        "icon": "mdi:web",
    },
}
