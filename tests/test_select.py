"""Tests for the Connect My Pool select platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.connect_my_pool.entity import derive_pool_id
from custom_components.connect_my_pool.models import (
    ConnectMyPoolData,
    ChannelConfig,
    ChannelStatus,
    FavouriteConfig,
    PoolStatus,
    ValveConfig,
    ValveStatus,
)
from custom_components.connect_my_pool.select import (
    ConnectMyPoolChannelSelect,
    ConnectMyPoolFavouriteSelect,
    ConnectMyPoolSpaSelect,
    ConnectMyPoolValveSelect,
)

from .conftest import TEST_API_CODE


@pytest.fixture
def pool_id() -> str:
    return derive_pool_id(TEST_API_CODE)


@pytest.fixture
def coordinator_mock(mock_pool_data):
    coordinator = MagicMock()
    coordinator.data = mock_pool_data
    coordinator.api = AsyncMock()
    coordinator.api.async_execute_action = AsyncMock(
        return_value={"action_number": 1, "execution_status": 1}
    )
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


def test_pool_spa_select_pool_mode(coordinator_mock, pool_id) -> None:
    """Test pool/spa select shows Pool when selection=1."""
    entity = ConnectMyPoolSpaSelect(coordinator_mock, pool_id)
    assert entity.current_option == "Pool"
    assert entity.options == ["Pool", "Spa"]


def test_pool_spa_select_spa_mode(
    coordinator_mock, pool_id, mock_pool_data
) -> None:
    """Test pool/spa select shows Spa when selection=0."""
    status = mock_pool_data.status
    coordinator_mock.data = ConnectMyPoolData(
        config=mock_pool_data.config,
        status=PoolStatus(
            pool_spa_selection=0,
            heat_cool_selection=status.heat_cool_selection,
            temperature=status.temperature,
            active_favourite=status.active_favourite,
            heaters=status.heaters,
            solar_systems=status.solar_systems,
            channels=status.channels,
            valves=status.valves,
            lighting_zones=status.lighting_zones,
        ),
    )
    entity = ConnectMyPoolSpaSelect(coordinator_mock, pool_id)
    assert entity.current_option == "Spa"


def test_favourite_select_none_active(coordinator_mock, pool_id) -> None:
    """Test favourite select returns None when active_favourite=255."""
    favourites = (
        FavouriteConfig(favourite_number=1, name="All On"),
        FavouriteConfig(favourite_number=2, name="All Off"),
    )
    entity = ConnectMyPoolFavouriteSelect(coordinator_mock, pool_id, favourites)
    assert entity.current_option is None
    assert "All On" in entity.options
    assert "All Off" in entity.options


def test_favourite_select_active(
    coordinator_mock, pool_id, mock_pool_data
) -> None:
    """Test favourite select shows correct name when a favourite is active."""
    status = mock_pool_data.status
    coordinator_mock.data = ConnectMyPoolData(
        config=mock_pool_data.config,
        status=PoolStatus(
            pool_spa_selection=status.pool_spa_selection,
            heat_cool_selection=status.heat_cool_selection,
            temperature=status.temperature,
            active_favourite=10,
            heaters=status.heaters,
            solar_systems=status.solar_systems,
            channels=status.channels,
            valves=status.valves,
            lighting_zones=status.lighting_zones,
        ),
    )
    favourites = (
        FavouriteConfig(favourite_number=1, name="All On"),
        FavouriteConfig(favourite_number=10, name="Spa Night"),
    )
    entity = ConnectMyPoolFavouriteSelect(coordinator_mock, pool_id, favourites)
    assert entity.current_option == "Spa Night"


def test_valve_select(coordinator_mock, pool_id) -> None:
    """Test valve select shows correct mode."""
    valve_cfg = ValveConfig(valve_number=1, function=1, name="Pool/Spa Valve")
    entity = ConnectMyPoolValveSelect(coordinator_mock, pool_id, valve_cfg)
    assert entity.current_option == "Off"
    assert entity.options == ["Off", "Auto", "On"]


def test_channel_select_options(coordinator_mock, pool_id) -> None:
    """Test channel select has correct options based on function type."""
    channel_cfg = ChannelConfig(channel_number=1, function=1, name="Filter Pump")
    entity = ConnectMyPoolChannelSelect(coordinator_mock, pool_id, channel_cfg)
    assert "On" in entity.options
    assert "Auto" in entity.options
    assert "Off" in entity.options


def test_channel_select_current_option(coordinator_mock, pool_id) -> None:
    """Test channel select current option from status."""
    channel_cfg = ChannelConfig(channel_number=1, function=1, name="Filter Pump")
    entity = ConnectMyPoolChannelSelect(coordinator_mock, pool_id, channel_cfg)
    assert entity.current_option == "Auto"


def test_channel_cycle_calculation(coordinator_mock, pool_id) -> None:
    """Test the cycle calculation for filter pump."""
    channel_cfg = ChannelConfig(channel_number=1, function=1, name="Filter Pump")
    entity = ConnectMyPoolChannelSelect(coordinator_mock, pool_id, channel_cfg)

    # Filter Pump cycle: [2, 1, 0]  (On -> Auto -> Off -> On...)
    assert entity._calculate_cycles(0, 2) == 1  # Off -> On (1 cycle)
    assert entity._calculate_cycles(2, 1) == 1  # On -> Auto (1 cycle)
    assert entity._calculate_cycles(1, 0) == 1  # Auto -> Off (1 cycle)
    assert entity._calculate_cycles(0, 1) == 2  # Off -> On -> Auto (2 cycles)
    assert entity._calculate_cycles(2, 0) == 2  # On -> Auto -> Off (2 cycles)
    assert entity._calculate_cycles(1, 1) == 0  # Same mode — no cycles
