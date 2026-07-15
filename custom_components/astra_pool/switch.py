"""Switch platform for the Astra Pool integration (simple on/off channels)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import AstraPoolConfigEntry
from .const import (
    ActionCode,
    CONF_POOL_API_CODE,
    LOGGER,
    MAX_CHANNEL_CYCLES,
    MULTI_MODE_CHANNEL_FUNCTIONS,
)
from .entity import AstraPoolEntity, derive_pool_id
from .models import ChannelConfig


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AstraPoolConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Astra Pool switch entities for simple on/off channels."""
    coordinator = entry.runtime_data
    pool_id = derive_pool_id(entry.data[CONF_POOL_API_CODE])
    config = coordinator.pool_config

    if not config.has_channels:
        return

    entities: list[AstraPoolChannelSwitch] = []
    for channel in config.channels:
        if channel.function not in MULTI_MODE_CHANNEL_FUNCTIONS:
            entities.append(
                AstraPoolChannelSwitch(coordinator, pool_id, channel)
            )

    async_add_entities(entities)


class AstraPoolChannelSwitch(AstraPoolEntity, SwitchEntity):
    """Simple on/off channel modelled as a switch.

    For two-mode channels (On / Off), a single cycle toggles between the two
    states.  A small safety loop verifies the resulting state.
    """

    def __init__(
        self, coordinator, pool_id: str, channel_cfg: ChannelConfig
    ) -> None:
        super().__init__(
            coordinator, pool_id, f"channel_{channel_cfg.channel_number}"
        )
        self._channel_number = channel_cfg.channel_number
        self._attr_name = channel_cfg.name

    @property
    def is_on(self) -> bool:
        cs = self._channel_status(self._channel_number)
        if cs is None:
            return False
        return cs.mode > 0

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._cycle_to(target_on=True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._cycle_to(target_on=False)

    async def _cycle_to(self, *, target_on: bool) -> None:
        """Cycle the channel until it reaches the desired on/off state."""
        cs = self._channel_status(self._channel_number)
        if cs is None:
            LOGGER.warning("No status for channel %d", self._channel_number)
            return

        is_currently_on = cs.mode > 0
        if is_currently_on == target_on:
            return

        api = self.coordinator.api
        for attempt in range(MAX_CHANNEL_CYCLES):
            await api.async_execute_action(
                ActionCode.CYCLE_CHANNEL_MODE,
                device_number=self._channel_number,
                wait_for_execution=True,
            )
            await self.coordinator.async_request_refresh()

            cs_after = self._channel_status(self._channel_number)
            if cs_after is not None:
                is_now_on = cs_after.mode > 0
                if is_now_on == target_on:
                    return

            LOGGER.debug(
                "Channel %d: attempt %d — not yet at target state",
                self._channel_number,
                attempt + 1,
            )

        LOGGER.warning(
            "Channel %d: could not reach target state after %d cycles",
            self._channel_number,
            MAX_CHANNEL_CYCLES,
        )
