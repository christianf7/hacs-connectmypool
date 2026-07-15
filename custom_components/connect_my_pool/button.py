"""Button platform for the Connect My Pool integration (lighting sync)."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ConnectMyPoolConfigEntry
from .const import ActionCode, CONF_POOL_API_CODE, LOGGER
from .entity import ConnectMyPoolEntity, derive_pool_id
from .exceptions import ConnectMyPoolActionError
from .models import LightingZoneConfig


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConnectMyPoolConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Connect My Pool button entities for lighting zone sync."""
    coordinator = entry.runtime_data
    pool_id = derive_pool_id(entry.data[CONF_POOL_API_CODE])
    config = coordinator.pool_config

    if not config.has_lighting_zones:
        return

    entities: list[ConnectMyPoolLightingSyncButton] = []
    for zone in config.lighting_zones:
        if zone.color_enabled:
            entities.append(
                ConnectMyPoolLightingSyncButton(coordinator, pool_id, zone)
            )

    async_add_entities(entities)


class ConnectMyPoolLightingSyncButton(ConnectMyPoolEntity, ButtonEntity):
    """Button to re-sync a colour lighting zone's colour.

    After a power cycle, the physical lights may have lost track of their
    programmed colour.  Pressing this button sends action code 11 to
    re-synchronise the colour to the last selected value.
    """

    def __init__(
        self, coordinator, pool_id: str, zone_cfg: LightingZoneConfig
    ) -> None:
        super().__init__(
            coordinator,
            pool_id,
            f"lighting_zone_{zone_cfg.lighting_zone_number}_sync",
        )
        self._zone_number = zone_cfg.lighting_zone_number
        self._attr_name = f"{zone_cfg.name} Sync"

    async def async_press(self) -> None:
        try:
            await self.coordinator.api.async_execute_action(
                ActionCode.SEND_LIGHTING_ZONE_SYNC,
                device_number=self._zone_number,
            )
        except ConnectMyPoolActionError as err:
            LOGGER.warning(
                "Lighting zone %d sync failed (code %d): %s",
                self._zone_number,
                err.failure_code,
                err,
            )
