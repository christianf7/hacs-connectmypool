"""Tests for the Connect My Pool climate platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from homeassistant.components.climate import HVACMode

from custom_components.connect_my_pool.climate import ConnectMyPoolHeaterClimate
from custom_components.connect_my_pool.entity import derive_pool_id
from custom_components.connect_my_pool.models import (
    ConnectMyPoolData,
    HeaterConfig,
    HeaterStatus,
    PoolConfiguration,
    PoolStatus,
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


def test_heater_off_state(coordinator_mock, pool_id) -> None:
    """Test that a heater with mode=0 reports OFF."""
    heater_cfg = HeaterConfig(heater_number=1)
    entity = ConnectMyPoolHeaterClimate(
        coordinator_mock,
        pool_id,
        heater_cfg,
        heat_cool_enabled=True,
        pool_spa_enabled=True,
    )
    assert entity.hvac_mode == HVACMode.OFF


def test_heater_heat_state(coordinator_mock, pool_id, mock_pool_data) -> None:
    """Test that a heater with mode=1 and heating selection reports HEAT."""
    status = mock_pool_data.status
    new_heaters = (
        HeaterStatus(
            heater_number=1, mode=1, set_temperature=28, spa_set_temperature=36
        ),
    )
    coordinator_mock.data = ConnectMyPoolData(
        config=mock_pool_data.config,
        status=PoolStatus(
            pool_spa_selection=status.pool_spa_selection,
            heat_cool_selection=1,
            temperature=status.temperature,
            active_favourite=status.active_favourite,
            heaters=new_heaters,
            solar_systems=status.solar_systems,
            channels=status.channels,
            valves=status.valves,
            lighting_zones=status.lighting_zones,
        ),
    )

    heater_cfg = HeaterConfig(heater_number=1)
    entity = ConnectMyPoolHeaterClimate(
        coordinator_mock,
        pool_id,
        heater_cfg,
        heat_cool_enabled=True,
        pool_spa_enabled=True,
    )
    assert entity.hvac_mode == HVACMode.HEAT


def test_heater_cool_state(coordinator_mock, pool_id, mock_pool_data) -> None:
    """Test that a heater with mode=1 and cooling selection reports COOL."""
    status = mock_pool_data.status
    new_heaters = (
        HeaterStatus(
            heater_number=1, mode=1, set_temperature=28, spa_set_temperature=36
        ),
    )
    coordinator_mock.data = ConnectMyPoolData(
        config=mock_pool_data.config,
        status=PoolStatus(
            pool_spa_selection=status.pool_spa_selection,
            heat_cool_selection=0,
            temperature=status.temperature,
            active_favourite=status.active_favourite,
            heaters=new_heaters,
            solar_systems=status.solar_systems,
            channels=status.channels,
            valves=status.valves,
            lighting_zones=status.lighting_zones,
        ),
    )

    heater_cfg = HeaterConfig(heater_number=1)
    entity = ConnectMyPoolHeaterClimate(
        coordinator_mock,
        pool_id,
        heater_cfg,
        heat_cool_enabled=True,
        pool_spa_enabled=True,
    )
    assert entity.hvac_mode == HVACMode.COOL


def test_heater_hvac_modes_with_cool(coordinator_mock, pool_id) -> None:
    """Test that COOL is in hvac_modes when heat_cool is enabled."""
    heater_cfg = HeaterConfig(heater_number=1)
    entity = ConnectMyPoolHeaterClimate(
        coordinator_mock,
        pool_id,
        heater_cfg,
        heat_cool_enabled=True,
        pool_spa_enabled=False,
    )
    assert HVACMode.COOL in entity.hvac_modes


def test_heater_hvac_modes_without_cool(coordinator_mock, pool_id) -> None:
    """Test that COOL is NOT in hvac_modes when heat_cool is disabled."""
    heater_cfg = HeaterConfig(heater_number=1)
    entity = ConnectMyPoolHeaterClimate(
        coordinator_mock,
        pool_id,
        heater_cfg,
        heat_cool_enabled=False,
        pool_spa_enabled=False,
    )
    assert HVACMode.COOL not in entity.hvac_modes
    assert HVACMode.OFF in entity.hvac_modes
    assert HVACMode.HEAT in entity.hvac_modes


def test_heater_target_temp_pool_mode(coordinator_mock, pool_id) -> None:
    """Test target temperature in pool mode."""
    heater_cfg = HeaterConfig(heater_number=1)
    entity = ConnectMyPoolHeaterClimate(
        coordinator_mock,
        pool_id,
        heater_cfg,
        heat_cool_enabled=False,
        pool_spa_enabled=True,
    )
    assert entity.target_temperature == 28.0


def test_heater_target_temp_spa_mode(
    coordinator_mock, pool_id, mock_pool_data
) -> None:
    """Test target temperature in spa mode."""
    status = mock_pool_data.status
    coordinator_mock.data = ConnectMyPoolData(
        config=mock_pool_data.config,
        status=PoolStatus(
            pool_spa_selection=0,  # Spa
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

    heater_cfg = HeaterConfig(heater_number=1)
    entity = ConnectMyPoolHeaterClimate(
        coordinator_mock,
        pool_id,
        heater_cfg,
        heat_cool_enabled=False,
        pool_spa_enabled=True,
    )
    assert entity.target_temperature == 36.0


def test_heater_current_temperature(coordinator_mock, pool_id) -> None:
    """Test that the current temperature comes from pool water temp."""
    heater_cfg = HeaterConfig(heater_number=1)
    entity = ConnectMyPoolHeaterClimate(
        coordinator_mock,
        pool_id,
        heater_cfg,
        heat_cool_enabled=False,
        pool_spa_enabled=False,
    )
    assert entity.current_temperature == 26.0
