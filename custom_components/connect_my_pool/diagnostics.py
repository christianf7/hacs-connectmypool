"""Diagnostics support for the Connect My Pool integration."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.core import HomeAssistant

from . import ConnectMyPoolConfigEntry
from .const import CONF_POOL_API_CODE

REDACTED = "**REDACTED**"


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConnectMyPoolConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    data = coordinator.data

    config_data: dict[str, Any] = dict(entry.data)
    if CONF_POOL_API_CODE in config_data:
        config_data[CONF_POOL_API_CODE] = REDACTED

    result: dict[str, Any] = {
        "config_entry": {
            "title": entry.title,
            "data": config_data,
        },
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "update_interval_seconds": (
                coordinator.update_interval.total_seconds()
                if coordinator.update_interval
                else None
            ),
        },
    }

    if data is not None:
        result["pool_configuration"] = _redact_dict(asdict(data.config))
        result["pool_status"] = _redact_dict(asdict(data.status))

    return result


def _redact_dict(d: dict[str, Any]) -> dict[str, Any]:
    """Recursively redact sensitive keys from a dictionary."""
    sensitive_keys = {"pool_api_code", "api_code", "api_key"}
    out: dict[str, Any] = {}
    for key, value in d.items():
        if key in sensitive_keys:
            out[key] = REDACTED
        elif isinstance(value, dict):
            out[key] = _redact_dict(value)
        elif isinstance(value, (list, tuple)):
            out[key] = [
                _redact_dict(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            out[key] = value
    return out
