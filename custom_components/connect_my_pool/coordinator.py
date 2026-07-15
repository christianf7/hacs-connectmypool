"""DataUpdateCoordinator for the Connect My Pool integration."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ConnectMyPoolApiClient
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, LOGGER
from .exceptions import (
    ConnectMyPoolAuthenticationError,
    ConnectMyPoolConnectionError,
    ConnectMyPoolError,
    ConnectMyPoolRateLimitError,
)
from .models import ConnectMyPoolData, PoolConfiguration


class ConnectMyPoolDataUpdateCoordinator(DataUpdateCoordinator[ConnectMyPoolData]):
    """Central coordinator that fetches data from the ConnectMyPool API."""

    config_entry: ConfigEntry
    pool_config: PoolConfiguration

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        api: ConnectMyPoolApiClient,
    ) -> None:
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            config_entry=config_entry,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.api = api
        self._consecutive_throttles = 0

    async def _async_setup(self) -> None:
        """Load pool configuration once during first refresh."""
        try:
            self.pool_config = await self.api.async_get_configuration()
        except ConnectMyPoolAuthenticationError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except ConnectMyPoolConnectionError as err:
            raise UpdateFailed(
                f"Cannot connect to ConnectMyPool: {err}"
            ) from err
        except ConnectMyPoolError as err:
            raise UpdateFailed(str(err)) from err

    async def _async_update_data(self) -> ConnectMyPoolData:
        """Fetch current pool status (called every update_interval)."""
        try:
            status = await self.api.async_get_status()
            self._consecutive_throttles = 0
        except ConnectMyPoolAuthenticationError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except ConnectMyPoolRateLimitError:
            self._consecutive_throttles += 1
            if self._consecutive_throttles <= 3:
                LOGGER.debug(
                    "API throttle hit (%d consecutive) — will retry next cycle",
                    self._consecutive_throttles,
                )
                if self.data is not None:
                    return self.data
            raise UpdateFailed("ConnectMyPool API rate-limit exceeded repeatedly")
        except ConnectMyPoolConnectionError as err:
            raise UpdateFailed(
                f"Cannot connect to ConnectMyPool: {err}"
            ) from err
        except ConnectMyPoolError as err:
            raise UpdateFailed(str(err)) from err

        return ConnectMyPoolData(config=self.pool_config, status=status)

    async def async_reload_config(self) -> None:
        """Re-fetch pool configuration on demand."""
        self.pool_config = await self.api.async_get_configuration()
