"""Async API client for the ConnectMyPool REST API."""

from __future__ import annotations

import asyncio
from typing import Any

import aiohttp

from .const import (
    API_BASE_URL,
    API_TIMEOUT,
    ExecutionStatus,
    FailureCode,
    LOGGER,
    TemperatureScale,
)
from .exceptions import (
    AstraPoolActionError,
    AstraPoolApiNotEnabledError,
    AstraPoolAuthenticationError,
    AstraPoolConnectionError,
    AstraPoolError,
    AstraPoolNotConnectedError,
    AstraPoolRateLimitError,
)
from .models import (
    ChannelConfig,
    ChannelStatus,
    FavouriteConfig,
    HeaterConfig,
    HeaterStatus,
    LightingColorConfig,
    LightingZoneConfig,
    LightingZoneStatus,
    PoolConfiguration,
    PoolStatus,
    SolarConfig,
    SolarStatus,
    ValveConfig,
    ValveStatus,
)


def _mask_api_code(code: str) -> str:
    """Return a masked version of the API code safe for logging."""
    if len(code) <= 4:
        return "****"
    return f"****{code[-4:]}"


class AstraPoolApiClient:
    """Asynchronous client for the ConnectMyPool API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        api_code: str,
        *,
        base_url: str = API_BASE_URL,
    ) -> None:
        self._session = session
        self._api_code = api_code
        self._base_url = base_url.rstrip("/")
        self._masked_code = _mask_api_code(api_code)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _request(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute a POST request against the API and return the JSON body."""
        url = f"{self._base_url}{endpoint}"
        try:
            async with asyncio.timeout(API_TIMEOUT):
                resp = await self._session.post(url, json=payload)
                resp.raise_for_status()
                data: dict[str, Any] = await resp.json(content_type=None)
        except asyncio.TimeoutError as err:
            raise AstraPoolConnectionError(
                f"Timeout connecting to ConnectMyPool ({self._masked_code})"
            ) from err
        except aiohttp.ClientError as err:
            raise AstraPoolConnectionError(
                f"Error connecting to ConnectMyPool ({self._masked_code}): {err}"
            ) from err

        if "failure_code" in data:
            self._raise_for_failure(data)

        return data

    def _raise_for_failure(self, data: dict[str, Any]) -> None:
        """Map an API failure response to a typed exception."""
        code = data.get("failure_code", 0)
        desc = data.get("failure_description", "Unknown error")

        if code in (FailureCode.INVALID_API_CODE, FailureCode.INVALID_API_KEY):
            raise AstraPoolAuthenticationError(desc)
        if code == FailureCode.API_NOT_ENABLED:
            raise AstraPoolApiNotEnabledError(desc)
        if code == FailureCode.TIME_THROTTLE_EXCEEDED:
            raise AstraPoolRateLimitError(desc)
        if code == FailureCode.POOL_NOT_CONNECTED:
            raise AstraPoolNotConnectedError(desc)
        if code in (
            FailureCode.INVALID_ACTION_CODE,
            FailureCode.INVALID_VALUE,
            FailureCode.INVALID_CHANNEL_NUMBER,
            FailureCode.INVALID_VALVE_NUMBER,
            FailureCode.POOL_SPA_SELECTION_NOT_ENABLED,
            FailureCode.INVALID_HEATER,
            FailureCode.INVALID_HEATER_SET_TEMP,
            FailureCode.INVALID_LIGHTING_ZONE,
            FailureCode.LIGHTING_ZONE_NOT_COLOR_ENABLED,
            FailureCode.INVALID_LIGHTING_ZONE_COLOR,
            FailureCode.INVALID_FAVOURITE_NUMBER,
            FailureCode.INVALID_SOLAR_SYSTEM_NUMBER,
            FailureCode.INVALID_SOLAR_SET_TEMP,
            FailureCode.LIGHTING_ZONE_DOES_NOT_SUPPORT_SYNC,
            FailureCode.HEAT_COOL_SELECTION_NOT_SUPPORTED,
        ):
            raise AstraPoolActionError(code, desc)

        raise AstraPoolError(desc)

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    async def async_get_configuration(self) -> PoolConfiguration:
        """Fetch pool configuration from /api/poolconfig."""
        data = await self._request(
            "/api/poolconfig",
            {"pool_api_code": self._api_code},
        )
        return self._parse_configuration(data)

    async def async_get_status(self) -> PoolStatus:
        """Fetch current pool status from /api/poolstatus."""
        data = await self._request(
            "/api/poolstatus",
            {
                "pool_api_code": self._api_code,
                "temperature_scale": TemperatureScale.CELSIUS,
            },
        )
        return self._parse_status(data)

    async def async_execute_action(
        self,
        action_code: int,
        device_number: int | None = None,
        value: str | None = None,
        *,
        wait_for_execution: bool = True,
    ) -> dict[str, Any]:
        """Execute a pool action via /api/poolaction.

        The request field name for the action is ``action_code`` per the
        documented POST body structure.  Some copies of the ConnectMyPool guide
        refer to it as ``action_number`` in the definitions table — this is
        believed to be a documentation inconsistency.
        """
        payload: dict[str, Any] = {
            "pool_api_code": self._api_code,
            "action_code": action_code,
            "temperature_scale": TemperatureScale.CELSIUS,
            "wait_for_execution": wait_for_execution,
        }
        if device_number is not None:
            payload["device_number"] = device_number
        if value is not None:
            payload["value"] = value

        LOGGER.debug(
            "Executing action %s on device %s (value=%s)",
            action_code,
            device_number,
            value,
        )
        return await self._request("/api/poolaction", payload)

    async def async_get_action_status(self, action_number: int) -> int:
        """Check execution status of a previously submitted action."""
        data = await self._request(
            "/api/poolactionstatus",
            {
                "pool_api_code": self._api_code,
                "action_number": action_number,
            },
        )
        return int(data.get("execution_status", ExecutionStatus.FAILED))

    # ------------------------------------------------------------------
    # Parsers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_configuration(data: dict[str, Any]) -> PoolConfiguration:
        heaters = tuple(
            HeaterConfig(heater_number=h["heater_number"])
            for h in data.get("heaters", [])
        )
        solar_systems = tuple(
            SolarConfig(solar_number=s["solar_number"])
            for s in data.get("solar_systems", [])
        )
        channels = tuple(
            ChannelConfig(
                channel_number=c["channel_number"],
                function=c["function"],
                name=c.get("name", f"Channel {c['channel_number']}"),
            )
            for c in data.get("channels", [])
        )
        valves = tuple(
            ValveConfig(
                valve_number=v["valve_number"],
                function=v.get("function", 0),
                name=v.get("name", f"Valve {v['valve_number']}"),
            )
            for v in data.get("valves", [])
        )
        lighting_zones = tuple(
            LightingZoneConfig(
                lighting_zone_number=lz["lighting_zone_number"],
                name=lz.get("name", f"Lighting Zone {lz['lighting_zone_number']}"),
                color_enabled=lz.get("color_enabled", False),
                colors_available=tuple(
                    LightingColorConfig(
                        color_number=c["color_number"],
                        color_name=c["color_name"],
                    )
                    for c in lz.get("colors_available", [])
                ),
            )
            for lz in data.get("lighting_zones", [])
        )
        favourites = tuple(
            FavouriteConfig(
                favourite_number=f["favourite_number"],
                name=f.get("name", f"Favourite {f['favourite_number']}"),
            )
            for f in data.get("favourites", [])
        )

        return PoolConfiguration(
            pool_spa_selection_enabled=data.get("pool_spa_selection_enabled", False),
            heat_cool_selection_enabled=data.get("heat_cool_selection_enabled", False),
            has_heaters=data.get("has_heaters", False),
            has_solar_systems=data.get("has_solar_systems", False),
            has_channels=data.get("has_channels", False),
            has_valves=data.get("has_valves", False),
            has_lighting_zones=data.get("has_lighting_zones", False),
            has_favourites=data.get("has_favourites", False),
            heaters=heaters,
            solar_systems=solar_systems,
            channels=channels,
            valves=valves,
            lighting_zones=lighting_zones,
            favourites=favourites,
        )

    @staticmethod
    def _parse_status(data: dict[str, Any]) -> PoolStatus:
        heaters = tuple(
            HeaterStatus(
                heater_number=h["heater_number"],
                mode=h.get("mode", 0),
                set_temperature=h.get("set_temperature", 0),
                spa_set_temperature=h.get("spa_set_temperature", 0),
            )
            for h in data.get("heaters", [])
        )
        solar_systems = tuple(
            SolarStatus(
                solar_number=s["solar_number"],
                mode=s.get("mode", 0),
                set_temperature=s.get("set_temperature", 0),
            )
            for s in data.get("solar_systems", [])
        )
        channels = tuple(
            ChannelStatus(
                channel_number=c["channel_number"],
                mode=c.get("mode", 0),
            )
            for c in data.get("channels", [])
        )
        valves = tuple(
            ValveStatus(
                valve_number=v["valve_number"],
                mode=v.get("mode", 0),
            )
            for v in data.get("valves", [])
        )
        lighting_zones = tuple(
            LightingZoneStatus(
                lighting_zone_number=lz["lighting_zone_number"],
                mode=lz.get("mode", 0),
                color=lz.get("color"),
            )
            for lz in data.get("lighting_zones", [])
        )

        return PoolStatus(
            pool_spa_selection=data.get("pool_spa_selection", 1),
            heat_cool_selection=data.get("heat_cool_selection", 1),
            temperature=data.get("temperature", 0),
            active_favourite=data.get("active_favourite", 255),
            heaters=heaters,
            solar_systems=solar_systems,
            channels=channels,
            valves=valves,
            lighting_zones=lighting_zones,
        )
