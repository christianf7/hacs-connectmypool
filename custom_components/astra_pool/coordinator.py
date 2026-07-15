"""DataUpdateCoordinator for the Astra Pool integration."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AstraPoolApiClient
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, LOGGER
from .exceptions import (
    AstraPoolAuthenticationError,
    AstraPoolConnectionError,
    AstraPoolError,
    AstraPoolRateLimitError,
)
from .models import AstraPoolData, PoolConfiguration


class AstraPoolDataUpdateCoordinator(DataUpdateCoordinator[AstraPoolData]):
    """Central coordinator that fetches data from the ConnectMyPool API."""

    config_entry: ConfigEntry
    pool_config: PoolConfiguration

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        api: AstraPoolApiClient,
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
        except AstraPoolAuthenticationError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except AstraPoolConnectionError as err:
            raise UpdateFailed(
                f"Cannot connect to ConnectMyPool: {err}"
            ) from err
        except AstraPoolError as err:
            raise UpdateFailed(str(err)) from err

    async def _async_update_data(self) -> AstraPoolData:
        """Fetch current pool status (called every update_interval)."""
        try:
            status = await self.api.async_get_status()
            self._consecutive_throttles = 0
        except AstraPoolAuthenticationError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except AstraPoolRateLimitError:
            self._consecutive_throttles += 1
            if self._consecutive_throttles <= 3:
                LOGGER.debug(
                    "API throttle hit (%d consecutive) — will retry next cycle",
                    self._consecutive_throttles,
                )
                if self.data is not None:
                    return self.data
            raise UpdateFailed("ConnectMyPool API rate-limit exceeded repeatedly")
        except AstraPoolConnectionError as err:
            raise UpdateFailed(
                f"Cannot connect to ConnectMyPool: {err}"
            ) from err
        except AstraPoolError as err:
            raise UpdateFailed(str(err)) from err

        return AstraPoolData(config=self.pool_config, status=status)

    async def async_reload_config(self) -> None:
        """Re-fetch pool configuration on demand."""
        self.pool_config = await self.api.async_get_configuration()
