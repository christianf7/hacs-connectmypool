"""Frontend module registration for the Connect My Pool custom card."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_call_later

_LOGGER = logging.getLogger(__name__)

URL_BASE = "/connect-my-pool"
CARD_FILENAME = "connect-my-pool-card.js"


class ConnectMyPoolCardRegistration:
    """Registers the Connect My Pool Lovelace card in Home Assistant."""

    def __init__(self, hass: HomeAssistant, version: str) -> None:
        self.hass = hass
        self.version = version
        self.lovelace = self.hass.data.get("lovelace")

    async def async_register(self) -> None:
        """Register the static path and Lovelace resource."""
        await self._async_register_path()
        if self.lovelace and self.lovelace.mode == "storage":
            await self._async_wait_for_lovelace_resources()

    async def _async_register_path(self) -> None:
        frontend_dir = Path(__file__).parent
        try:
            await self.hass.http.async_register_static_paths(
                [StaticPathConfig(URL_BASE, str(frontend_dir), False)]
            )
            _LOGGER.debug("Registered static path: %s -> %s", URL_BASE, frontend_dir)
        except RuntimeError:
            _LOGGER.debug("Static path already registered: %s", URL_BASE)

    async def _async_wait_for_lovelace_resources(self) -> None:
        async def _check_loaded(_now: Any) -> None:
            if self.lovelace.resources.loaded:
                await self._async_register_module()
            else:
                _LOGGER.debug("Lovelace resources not yet loaded, retrying in 5s")
                async_call_later(self.hass, 5, _check_loaded)

        await _check_loaded(0)

    async def _async_register_module(self) -> None:
        url = f"{URL_BASE}/{CARD_FILENAME}"
        versioned_url = f"{url}?v={self.version}"

        existing = [
            r
            for r in self.lovelace.resources.async_items()
            if r["url"].startswith(URL_BASE)
        ]

        for resource in existing:
            resource_path = resource["url"].split("?")[0]
            if resource_path == url:
                current_version = self._extract_version(resource["url"])
                if current_version != self.version:
                    _LOGGER.info(
                        "Updating card resource %s -> v%s",
                        CARD_FILENAME,
                        self.version,
                    )
                    await self.lovelace.resources.async_update_item(
                        resource["id"],
                        {"url": versioned_url},
                    )
                else:
                    _LOGGER.debug("Card resource already up to date: %s", url)
                return

        _LOGGER.info("Registering card resource: %s", versioned_url)
        await self.lovelace.resources.async_create_item(
            {"res_type": "module", "url": versioned_url}
        )

    @staticmethod
    def _extract_version(url: str) -> str | None:
        if "?v=" in url:
            return url.split("?v=")[-1]
        return None
