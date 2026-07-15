"""Tests for the Connect My Pool API client."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from custom_components.connect_my_pool.api import ConnectMyPoolApiClient, _mask_api_code
from custom_components.connect_my_pool.exceptions import (
    ConnectMyPoolActionError,
    ConnectMyPoolApiNotEnabledError,
    ConnectMyPoolAuthenticationError,
    ConnectMyPoolConnectionError,
    ConnectMyPoolNotConnectedError,
    ConnectMyPoolRateLimitError,
)
from custom_components.connect_my_pool.models import PoolConfiguration, PoolStatus

from .conftest import make_config_raw, make_error_response, make_status_raw


def test_mask_api_code() -> None:
    """Test that the API code masking works correctly."""
    assert _mask_api_code("abcdef123456") == "****3456"
    assert _mask_api_code("abc") == "****"
    assert _mask_api_code("") == "****"
    assert _mask_api_code("12345") == "****2345"


@pytest.fixture
def mock_session() -> MagicMock:
    """Create a mock aiohttp ClientSession."""
    return MagicMock(spec=aiohttp.ClientSession)


def _setup_response(session: MagicMock, json_data: dict, status: int = 200):
    """Configure the mock session to return a given JSON response."""
    response = AsyncMock()
    response.status = status
    response.raise_for_status = MagicMock()
    if status >= 400:
        response.raise_for_status.side_effect = aiohttp.ClientResponseError(
            request_info=MagicMock(), history=(), status=status
        )
    response.json = AsyncMock(return_value=json_data)
    session.post = AsyncMock(return_value=response)


async def test_get_configuration_success(mock_session: MagicMock) -> None:
    """Test successful configuration fetch."""
    raw = make_config_raw()
    _setup_response(mock_session, raw)

    client = ConnectMyPoolApiClient(mock_session, "test-code", base_url="https://example.com")
    config = await client.async_get_configuration()

    assert isinstance(config, PoolConfiguration)
    assert config.has_heaters is True
    assert len(config.heaters) == 1
    assert config.heaters[0].heater_number == 1
    assert len(config.channels) == 2
    assert config.lighting_zones[0].color_enabled is True
    assert len(config.lighting_zones[0].colors_available) == 3


async def test_get_status_success(mock_session: MagicMock) -> None:
    """Test successful status fetch."""
    raw = make_status_raw()
    _setup_response(mock_session, raw)

    client = ConnectMyPoolApiClient(mock_session, "test-code", base_url="https://example.com")
    status = await client.async_get_status()

    assert isinstance(status, PoolStatus)
    assert status.temperature == 26
    assert status.pool_spa_selection == 1
    assert len(status.heaters) == 1
    assert status.heaters[0].mode == 0
    assert status.active_favourite == 255


async def test_invalid_api_code_raises(mock_session: MagicMock) -> None:
    """Test that invalid API code returns ConnectMyPoolAuthenticationError."""
    _setup_response(mock_session, make_error_response(3, "Invalid API Code"))

    client = ConnectMyPoolApiClient(mock_session, "bad-code", base_url="https://example.com")

    with pytest.raises(ConnectMyPoolAuthenticationError, match="Invalid API Code"):
        await client.async_get_configuration()


async def test_api_not_enabled_raises(mock_session: MagicMock) -> None:
    """Test that API not enabled returns ConnectMyPoolApiNotEnabledError."""
    _setup_response(mock_session, make_error_response(4, "API Not Enabled"))

    client = ConnectMyPoolApiClient(mock_session, "code", base_url="https://example.com")

    with pytest.raises(ConnectMyPoolApiNotEnabledError):
        await client.async_get_configuration()


async def test_pool_not_connected_raises(mock_session: MagicMock) -> None:
    """Test that pool not connected returns ConnectMyPoolNotConnectedError."""
    _setup_response(mock_session, make_error_response(7, "Pool Not Connected"))

    client = ConnectMyPoolApiClient(mock_session, "code", base_url="https://example.com")

    with pytest.raises(ConnectMyPoolNotConnectedError):
        await client.async_get_status()


async def test_rate_limit_raises(mock_session: MagicMock) -> None:
    """Test that throttle exceeded returns ConnectMyPoolRateLimitError."""
    _setup_response(mock_session, make_error_response(6, "Throttle"))

    client = ConnectMyPoolApiClient(mock_session, "code", base_url="https://example.com")

    with pytest.raises(ConnectMyPoolRateLimitError):
        await client.async_get_status()


async def test_action_error_raises(mock_session: MagicMock) -> None:
    """Test that action-specific errors return ConnectMyPoolActionError."""
    _setup_response(mock_session, make_error_response(10, "Invalid Channel Number"))

    client = ConnectMyPoolApiClient(mock_session, "code", base_url="https://example.com")

    with pytest.raises(ConnectMyPoolActionError) as exc_info:
        await client.async_execute_action(1, device_number=99)

    assert exc_info.value.failure_code == 10


async def test_connection_error_on_timeout(mock_session: MagicMock) -> None:
    """Test that a timeout raises ConnectMyPoolConnectionError."""
    mock_session.post = AsyncMock(side_effect=asyncio.TimeoutError)

    client = ConnectMyPoolApiClient(mock_session, "code", base_url="https://example.com")

    with pytest.raises(ConnectMyPoolConnectionError, match="Timeout"):
        await client.async_get_configuration()


async def test_connection_error_on_client_error(mock_session: MagicMock) -> None:
    """Test that aiohttp errors raise ConnectMyPoolConnectionError."""
    mock_session.post = AsyncMock(
        side_effect=aiohttp.ClientError("Connection refused")
    )

    client = ConnectMyPoolApiClient(mock_session, "code", base_url="https://example.com")

    with pytest.raises(ConnectMyPoolConnectionError):
        await client.async_get_status()


async def test_execute_action_success(mock_session: MagicMock) -> None:
    """Test successful action execution."""
    _setup_response(
        mock_session, {"action_number": 42, "execution_status": 1}
    )

    client = ConnectMyPoolApiClient(mock_session, "code", base_url="https://example.com")
    result = await client.async_execute_action(4, device_number=1, value="1")

    assert result["execution_status"] == 1
    assert result["action_number"] == 42
