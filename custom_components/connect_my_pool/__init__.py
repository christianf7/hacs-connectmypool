"""The Connect My Pool integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ConnectMyPoolApiClient
from .const import CONF_POOL_API_CODE, LOGGER
from .coordinator import ConnectMyPoolDataUpdateCoordinator
from .entity import derive_pool_id
from .exceptions import ConnectMyPoolConnectionError, ConnectMyPoolError

PLATFORMS: list[Platform] = [
    Platform.BUTTON,
    Platform.CLIMATE,
    Platform.LIGHT,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]

ConnectMyPoolConfigEntry = ConfigEntry[ConnectMyPoolDataUpdateCoordinator]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConnectMyPoolConfigEntry
) -> bool:
    """Set up Connect My Pool from a config entry."""
    api_code: str = entry.data[CONF_POOL_API_CODE]
    session = async_get_clientsession(hass)
    client = ConnectMyPoolApiClient(session, api_code)

    coordinator = ConnectMyPoolDataUpdateCoordinator(hass, entry, client)

    try:
        await coordinator.async_config_entry_first_refresh()
    except ConfigEntryNotReady:
        raise
    except (ConnectMyPoolConnectionError, ConnectMyPoolError) as err:
        raise ConfigEntryNotReady(str(err)) from err

    pool_id = derive_pool_id(api_code)
    LOGGER.debug("Pool ID derived: %s", pool_id)

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: ConnectMyPoolConfigEntry
) -> bool:
    """Unload a Connect My Pool config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
