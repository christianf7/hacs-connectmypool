"""Config flow for the Astra Pool integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import AstraPoolApiClient
from .const import CONF_POOL_API_CODE, DOMAIN, LOGGER
from .entity import derive_pool_id
from .exceptions import (
    AstraPoolApiNotEnabledError,
    AstraPoolAuthenticationError,
    AstraPoolConnectionError,
    AstraPoolNotConnectedError,
    AstraPoolRateLimitError,
)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_POOL_API_CODE): str,
    }
)


class AstraPoolConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Astra Pool."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step where the user enters their Pool API Code."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_code = user_input[CONF_POOL_API_CODE].strip()

            pool_id = derive_pool_id(api_code)
            await self.async_set_unique_id(pool_id)
            self._abort_if_unique_id_configured()

            session = async_get_clientsession(self.hass)
            client = AstraPoolApiClient(session, api_code)

            try:
                config = await client.async_get_configuration()
            except AstraPoolAuthenticationError:
                errors["base"] = "invalid_auth"
            except AstraPoolApiNotEnabledError:
                errors["base"] = "api_not_enabled"
            except AstraPoolNotConnectedError:
                errors["base"] = "pool_not_connected"
            except AstraPoolRateLimitError:
                errors["base"] = "rate_limited"
            except AstraPoolConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                LOGGER.exception("Unexpected error during config validation")
                errors["base"] = "unknown"
            else:
                title = "Astra Pool"
                if config.pool_spa_selection_enabled:
                    title = "Astra Pool & Spa"

                return self.async_create_entry(
                    title=title,
                    data={CONF_POOL_API_CODE: api_code},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
