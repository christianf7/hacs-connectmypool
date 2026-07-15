"""Tests for the Astra Pool coordinator."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.astra_pool.coordinator import AstraPoolDataUpdateCoordinator
from custom_components.astra_pool.exceptions import (
    AstraPoolAuthenticationError,
    AstraPoolConnectionError,
    AstraPoolRateLimitError,
)
from custom_components.astra_pool.models import AstraPoolData

from .conftest import TEST_API_CODE


@pytest.fixture
def mock_api(mock_pool_config, mock_pool_status):
    """Create a mock API client."""
    api = AsyncMock()
    api.async_get_configuration = AsyncMock(return_value=mock_pool_config)
    api.async_get_status = AsyncMock(return_value=mock_pool_status)
    api.async_execute_action = AsyncMock(
        return_value={"action_number": 1, "execution_status": 1}
    )
    return api


@pytest.fixture
def mock_entry():
    """Create a mock config entry with required attributes."""
    entry = MagicMock()
    entry.data = {"pool_api_code": TEST_API_CODE}
    entry.entry_id = "test_entry_id"
    return entry


async def test_coordinator_setup_and_update(
    hass: HomeAssistant, mock_api, mock_entry, mock_pool_config, mock_pool_status
) -> None:
    """Test that _async_setup loads config and _async_update_data returns status."""
    coordinator = AstraPoolDataUpdateCoordinator(hass, mock_entry, mock_api)

    await coordinator._async_setup()
    assert coordinator.pool_config == mock_pool_config
    mock_api.async_get_configuration.assert_awaited_once()

    result = await coordinator._async_update_data()
    assert isinstance(result, AstraPoolData)
    assert result.config == mock_pool_config
    assert result.status == mock_pool_status


async def test_coordinator_auth_failure_setup(
    hass: HomeAssistant, mock_api, mock_entry
) -> None:
    """Test that auth failure during setup raises ConfigEntryAuthFailed."""
    mock_api.async_get_configuration = AsyncMock(
        side_effect=AstraPoolAuthenticationError("bad code")
    )

    coordinator = AstraPoolDataUpdateCoordinator(hass, mock_entry, mock_api)

    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator._async_setup()


async def test_coordinator_connection_failure_setup(
    hass: HomeAssistant, mock_api, mock_entry
) -> None:
    """Test that connection failure during setup raises UpdateFailed."""
    mock_api.async_get_configuration = AsyncMock(
        side_effect=AstraPoolConnectionError("timeout")
    )

    coordinator = AstraPoolDataUpdateCoordinator(hass, mock_entry, mock_api)

    with pytest.raises(UpdateFailed):
        await coordinator._async_setup()


async def test_coordinator_connection_failure_update(
    hass: HomeAssistant, mock_api, mock_entry, mock_pool_config
) -> None:
    """Test that connection failures during update raise UpdateFailed."""
    coordinator = AstraPoolDataUpdateCoordinator(hass, mock_entry, mock_api)
    await coordinator._async_setup()

    mock_api.async_get_status = AsyncMock(
        side_effect=AstraPoolConnectionError("timeout")
    )

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


async def test_coordinator_auth_failure_update(
    hass: HomeAssistant, mock_api, mock_entry, mock_pool_config
) -> None:
    """Test that auth failure during update raises ConfigEntryAuthFailed."""
    coordinator = AstraPoolDataUpdateCoordinator(hass, mock_entry, mock_api)
    await coordinator._async_setup()

    mock_api.async_get_status = AsyncMock(
        side_effect=AstraPoolAuthenticationError("expired")
    )

    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator._async_update_data()


async def test_coordinator_throttle_recovery(
    hass: HomeAssistant, mock_api, mock_entry, mock_pool_config, mock_pool_status
) -> None:
    """Test that a single throttle hit reuses existing data."""
    coordinator = AstraPoolDataUpdateCoordinator(hass, mock_entry, mock_api)
    await coordinator._async_setup()

    first_data = await coordinator._async_update_data()
    coordinator.data = first_data

    mock_api.async_get_status = AsyncMock(
        side_effect=AstraPoolRateLimitError("throttled")
    )

    result = await coordinator._async_update_data()
    assert result == first_data
    assert coordinator._consecutive_throttles == 1


async def test_coordinator_throttle_repeated_fails(
    hass: HomeAssistant, mock_api, mock_entry, mock_pool_config
) -> None:
    """Test that repeated throttle hits eventually raise UpdateFailed."""
    coordinator = AstraPoolDataUpdateCoordinator(hass, mock_entry, mock_api)
    await coordinator._async_setup()

    coordinator.data = None
    coordinator._consecutive_throttles = 3

    mock_api.async_get_status = AsyncMock(
        side_effect=AstraPoolRateLimitError("throttled")
    )

    with pytest.raises(UpdateFailed, match="rate-limit"):
        await coordinator._async_update_data()
