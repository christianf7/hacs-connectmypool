"""Tests for the Astra Pool config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.astra_pool.const import CONF_POOL_API_CODE, DOMAIN
from custom_components.astra_pool.exceptions import (
    AstraPoolApiNotEnabledError,
    AstraPoolAuthenticationError,
    AstraPoolConnectionError,
    AstraPoolNotConnectedError,
    AstraPoolRateLimitError,
)
from custom_components.astra_pool.models import PoolConfiguration

from .conftest import TEST_API_CODE

MOCK_SETUP_ENTRY = "custom_components.astra_pool.async_setup_entry"


def _minimal_config() -> PoolConfiguration:
    return PoolConfiguration(
        pool_spa_selection_enabled=False,
        heat_cool_selection_enabled=False,
        has_heaters=False,
        has_solar_systems=False,
        has_channels=False,
        has_valves=False,
        has_lighting_zones=False,
        has_favourites=False,
    )


async def test_successful_flow(hass: HomeAssistant) -> None:
    """Test a successful config flow from start to finish."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    with (
        patch(
            "custom_components.astra_pool.config_flow.AstraPoolApiClient"
        ) as mock_client_cls,
        patch(MOCK_SETUP_ENTRY, return_value=True),
    ):
        mock_client = mock_client_cls.return_value
        mock_client.async_get_configuration = AsyncMock(return_value=_minimal_config())

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_POOL_API_CODE: TEST_API_CODE},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Astra Pool"
    assert result["data"][CONF_POOL_API_CODE] == TEST_API_CODE


async def test_successful_flow_pool_spa(hass: HomeAssistant) -> None:
    """Test that a pool with spa selection gets an appropriate title."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    spa_config = PoolConfiguration(
        pool_spa_selection_enabled=True,
        heat_cool_selection_enabled=False,
        has_heaters=False,
        has_solar_systems=False,
        has_channels=False,
        has_valves=False,
        has_lighting_zones=False,
        has_favourites=False,
    )

    with (
        patch(
            "custom_components.astra_pool.config_flow.AstraPoolApiClient"
        ) as mock_client_cls,
        patch(MOCK_SETUP_ENTRY, return_value=True),
    ):
        mock_client = mock_client_cls.return_value
        mock_client.async_get_configuration = AsyncMock(return_value=spa_config)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_POOL_API_CODE: TEST_API_CODE},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Astra Pool & Spa"


async def test_invalid_auth(hass: HomeAssistant) -> None:
    """Test that an invalid API code shows the right error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.astra_pool.config_flow.AstraPoolApiClient"
    ) as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.async_get_configuration = AsyncMock(
            side_effect=AstraPoolAuthenticationError("Invalid")
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_POOL_API_CODE: "bad-code"},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_api_not_enabled(hass: HomeAssistant) -> None:
    """Test that API-not-enabled produces the right error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.astra_pool.config_flow.AstraPoolApiClient"
    ) as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.async_get_configuration = AsyncMock(
            side_effect=AstraPoolApiNotEnabledError("Not enabled")
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_POOL_API_CODE: "code"},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "api_not_enabled"}


async def test_cannot_connect(hass: HomeAssistant) -> None:
    """Test that connection failures produce the right error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.astra_pool.config_flow.AstraPoolApiClient"
    ) as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.async_get_configuration = AsyncMock(
            side_effect=AstraPoolConnectionError("timeout")
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_POOL_API_CODE: "code"},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_pool_not_connected(hass: HomeAssistant) -> None:
    """Test that an offline pool produces the right error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.astra_pool.config_flow.AstraPoolApiClient"
    ) as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.async_get_configuration = AsyncMock(
            side_effect=AstraPoolNotConnectedError("offline")
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_POOL_API_CODE: "code"},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "pool_not_connected"}


async def test_rate_limited(hass: HomeAssistant) -> None:
    """Test that a rate-limit during setup produces the right error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.astra_pool.config_flow.AstraPoolApiClient"
    ) as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.async_get_configuration = AsyncMock(
            side_effect=AstraPoolRateLimitError("throttled")
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_POOL_API_CODE: "code"},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "rate_limited"}
