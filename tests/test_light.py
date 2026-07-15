"""Tests for the Astra Pool light platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from homeassistant.components.light import ColorMode, LightEntityFeature

from custom_components.astra_pool.entity import derive_pool_id
from custom_components.astra_pool.light import AstraPoolLight
from custom_components.astra_pool.models import (
    LightingColorConfig,
    LightingZoneConfig,
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


def test_color_enabled_light(coordinator_mock, pool_id) -> None:
    """Test a colour-enabled light has effects and valid color modes."""
    zone_cfg = LightingZoneConfig(
        lighting_zone_number=1,
        name="Pool Light",
        color_enabled=True,
        colors_available=(
            LightingColorConfig(color_number=1, color_name="Red"),
            LightingColorConfig(color_number=5, color_name="Blue"),
            LightingColorConfig(color_number=7, color_name="White"),
        ),
    )

    entity = AstraPoolLight(coordinator_mock, pool_id, zone_cfg)

    assert entity.supported_color_modes == {ColorMode.ONOFF}
    assert entity.color_mode == ColorMode.ONOFF
    assert entity.supported_features & LightEntityFeature.EFFECT
    assert entity.effect_list == ["Red", "Blue", "White"]
    assert entity.is_on is True
    assert entity.effect == "Blue"


def test_non_color_light(coordinator_mock, pool_id) -> None:
    """Test a non-colour light has valid color modes and no effects."""
    zone_cfg = LightingZoneConfig(
        lighting_zone_number=2,
        name="Garden Light",
        color_enabled=False,
        colors_available=(),
    )

    entity = AstraPoolLight(coordinator_mock, pool_id, zone_cfg)

    assert entity.supported_color_modes == {ColorMode.ONOFF}
    assert entity.color_mode == ColorMode.ONOFF
    assert entity.effect_list is None
    assert entity.effect is None
    assert entity.is_on is False


def test_supported_color_modes_never_empty(coordinator_mock, pool_id) -> None:
    """Critical: supported_color_modes must never be empty."""
    for color_enabled in (True, False):
        zone_cfg = LightingZoneConfig(
            lighting_zone_number=1,
            name="Test",
            color_enabled=color_enabled,
            colors_available=(
                LightingColorConfig(color_number=1, color_name="Red"),
            )
            if color_enabled
            else (),
        )
        entity = AstraPoolLight(coordinator_mock, pool_id, zone_cfg)
        assert len(entity.supported_color_modes) > 0


def test_light_off_state(coordinator_mock, pool_id) -> None:
    """Test that a light with mode=0 reports is_on=False."""
    zone_cfg = LightingZoneConfig(
        lighting_zone_number=2,
        name="Garden Light",
        color_enabled=False,
    )
    entity = AstraPoolLight(coordinator_mock, pool_id, zone_cfg)
    assert entity.is_on is False
