"""Tests for the Connect My Pool sensor platform."""

from __future__ import annotations

import pytest

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import UnitOfTemperature

from custom_components.connect_my_pool.sensor import ConnectMyPoolWaterTemperatureSensor

from .conftest import TEST_API_CODE


def test_sensor_attributes(mock_pool_data) -> None:
    """Test that the water temperature sensor has correct attributes."""
    from unittest.mock import MagicMock

    from custom_components.connect_my_pool.entity import derive_pool_id

    pool_id = derive_pool_id(TEST_API_CODE)

    coordinator = MagicMock()
    coordinator.data = mock_pool_data

    sensor = ConnectMyPoolWaterTemperatureSensor(coordinator, pool_id)

    assert sensor.native_value == 26
    assert sensor.device_class == SensorDeviceClass.TEMPERATURE
    assert sensor.native_unit_of_measurement == UnitOfTemperature.CELSIUS
    assert sensor.unique_id == f"{pool_id}_water_temperature"
    assert sensor.name == "Water Temperature"
