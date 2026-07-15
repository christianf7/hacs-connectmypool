"""Shared test fixtures for the Astra Pool integration tests."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from custom_components.astra_pool.const import CONF_POOL_API_CODE, DOMAIN
from custom_components.astra_pool.models import (
    AstraPoolData,
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

TEST_API_CODE = "test-api-code-abc123"


@pytest.fixture
def mock_pool_config() -> PoolConfiguration:
    """Return a typical pool configuration for testing."""
    return PoolConfiguration(
        pool_spa_selection_enabled=True,
        heat_cool_selection_enabled=True,
        has_heaters=True,
        has_solar_systems=True,
        has_channels=True,
        has_valves=True,
        has_lighting_zones=True,
        has_favourites=True,
        heaters=(HeaterConfig(heater_number=1),),
        solar_systems=(SolarConfig(solar_number=1),),
        channels=(
            ChannelConfig(channel_number=1, function=1, name="Filter Pump"),
            ChannelConfig(channel_number=2, function=12, name="Spa Jets"),
        ),
        valves=(ValveConfig(valve_number=1, function=1, name="Pool/Spa Valve"),),
        lighting_zones=(
            LightingZoneConfig(
                lighting_zone_number=1,
                name="Pool Light",
                color_enabled=True,
                colors_available=(
                    LightingColorConfig(color_number=1, color_name="Red"),
                    LightingColorConfig(color_number=5, color_name="Blue"),
                    LightingColorConfig(color_number=7, color_name="White"),
                ),
            ),
            LightingZoneConfig(
                lighting_zone_number=2,
                name="Garden Light",
                color_enabled=False,
                colors_available=(),
            ),
        ),
        favourites=(
            FavouriteConfig(favourite_number=1, name="All On"),
            FavouriteConfig(favourite_number=2, name="All Off"),
            FavouriteConfig(favourite_number=3, name="All Auto"),
            FavouriteConfig(favourite_number=10, name="Spa Night"),
        ),
    )


@pytest.fixture
def mock_pool_status() -> PoolStatus:
    """Return a typical pool status for testing."""
    return PoolStatus(
        pool_spa_selection=1,
        heat_cool_selection=1,
        temperature=26,
        active_favourite=255,
        heaters=(
            HeaterStatus(
                heater_number=1,
                mode=0,
                set_temperature=28,
                spa_set_temperature=36,
            ),
        ),
        solar_systems=(
            SolarStatus(solar_number=1, mode=1, set_temperature=30),
        ),
        channels=(
            ChannelStatus(channel_number=1, mode=1),
            ChannelStatus(channel_number=2, mode=0),
        ),
        valves=(ValveStatus(valve_number=1, mode=0),),
        lighting_zones=(
            LightingZoneStatus(lighting_zone_number=1, mode=2, color=5),
            LightingZoneStatus(lighting_zone_number=2, mode=0, color=None),
        ),
    )


@pytest.fixture
def mock_pool_data(
    mock_pool_config: PoolConfiguration, mock_pool_status: PoolStatus
) -> AstraPoolData:
    """Return combined pool data for testing."""
    return AstraPoolData(config=mock_pool_config, status=mock_pool_status)


def make_config_raw() -> dict[str, Any]:
    """Return a raw API /api/poolconfig response dict."""
    return {
        "pool_spa_selection_enabled": True,
        "heat_cool_selection_enabled": True,
        "has_heaters": True,
        "has_solar_systems": True,
        "has_channels": True,
        "has_valves": True,
        "has_lighting_zones": True,
        "has_favourites": True,
        "heaters": [{"heater_number": 1}],
        "solar_systems": [{"solar_number": 1}],
        "channels": [
            {"channel_number": 1, "function": 1, "name": "Filter Pump"},
            {"channel_number": 2, "function": 12, "name": "Spa Jets"},
        ],
        "valves": [{"valve_number": 1, "function": 1, "name": "Pool/Spa Valve"}],
        "lighting_zones": [
            {
                "lighting_zone_number": 1,
                "name": "Pool Light",
                "color_enabled": True,
                "colors_available": [
                    {"color_number": 1, "color_name": "Red"},
                    {"color_number": 5, "color_name": "Blue"},
                    {"color_number": 7, "color_name": "White"},
                ],
            },
            {
                "lighting_zone_number": 2,
                "name": "Garden Light",
                "color_enabled": False,
                "colors_available": [],
            },
        ],
        "favourites": [
            {"favourite_number": 1, "name": "All On"},
            {"favourite_number": 2, "name": "All Off"},
            {"favourite_number": 3, "name": "All Auto"},
            {"favourite_number": 10, "name": "Spa Night"},
        ],
    }


def make_status_raw() -> dict[str, Any]:
    """Return a raw API /api/poolstatus response dict."""
    return {
        "pool_spa_selection": 1,
        "heat_cool_selection": 1,
        "temperature": 26,
        "active_favourite": 255,
        "heaters": [
            {
                "heater_number": 1,
                "mode": 0,
                "set_temperature": 28,
                "spa_set_temperature": 36,
            }
        ],
        "solar_systems": [
            {"solar_number": 1, "mode": 1, "set_temperature": 30}
        ],
        "channels": [
            {"channel_number": 1, "mode": 1},
            {"channel_number": 2, "mode": 0},
        ],
        "valves": [{"valve_number": 1, "mode": 0}],
        "lighting_zones": [
            {"lighting_zone_number": 1, "mode": 2, "color": 5},
            {"lighting_zone_number": 2, "mode": 0},
        ],
    }


def make_action_response(
    action_number: int = 1, execution_status: int = 1
) -> dict[str, Any]:
    """Return a raw API /api/poolaction success response."""
    return {
        "action_number": action_number,
        "execution_status": execution_status,
    }


def make_error_response(
    failure_code: int, failure_description: str = "Error"
) -> dict[str, Any]:
    """Return a raw API error response."""
    return {
        "failure_code": failure_code,
        "failure_description": failure_description,
    }
