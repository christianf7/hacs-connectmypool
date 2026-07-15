"""Tests for the Astra Pool coordinator."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

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
    """Create a mock config entry."""
    entry = MagicMock()
    entry.data = {"pool_api_code": TEST_API_CODE}
    entry.entry_id = "test_entry_id"
    return entry


@pytest.mark.asyncio
async def test_coordinator_first_refresh(
    hass: HomeAssistant, mock_api, mock_entry, mock_pool_config, mock_pool_status
) -> None:
    """Test that the coordinator loads config and status on first refresh."""
    coordinator = AstraPoolDataUpdateCoordinator(hass, mock_entry, mock_api)
    await coordinator.async_config_entry_first_refresh()

    assert coordinator.pool_config == mock_pool_config
    assert coordinator.data.status == mock_pool_status
    assert coordinator.last_update_success is True


@pytest.mark.asyncio
async def test_coordinator_auth_failure_setup(
    hass: HomeAssistant, mock_api, mock_entry
) -> None:
    """Test that auth failure during setup raises ConfigEntryAuthFailed."""
    mock_api.async_get_configuration = AsyncMock(
        side_effect=AstraPoolAuthenticationError("bad code")
    )

    coordinator = AstraPoolDataUpdateCoordinator(hass, mock_entry, mock_api)

    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator.async_config_entry_first_refresh()


@pytest.mark.asyncio
async def test_coordinator_connection_failure_update(
    hass: HomeAssistant, mock_api, mock_entry, mock_pool_config
) -> None:
    """Test that connection failures during update raise UpdateFailed."""
    mock_api.async_get_status = AsyncMock(
        side_effect=AstraPoolConnectionError("timeout")
    )

    coordinator = AstraPoolDataUpdateCoordinator(hass, mock_entry, mock_api)

    with pytest.raises(UpdateFailed):
        await coordinator.async_config_entry_first_refresh()


@pytest.mark.asyncio
async def test_coordinator_throttle_recovery(
    hass: HomeAssistant, mock_api, mock_entry, mock_pool_config, mock_pool_status
) -> None:
    """Test that a single throttle hit reuses existing data."""
    coordinator = AstraPoolDataUpdateCoordinator(hass, mock_entry, mock_api)
    await coordinator.async_config_entry_first_refresh()

    first_data = coordinator.data

    mock_api.async_get_status = AsyncMock(
        side_effect=AstraPoolRateLimitError("throttled")
    )

    result = await coordinator._async_update_data()
    assert result == first_data
