"""Light platform for the Astra Pool integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import (
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import AstraPoolConfigEntry
from .const import (
    ActionCode,
    CONF_POOL_API_CODE,
    LIGHTING_MODE_NAMES,
    LightingMode,
)
from .entity import AstraPoolEntity, derive_pool_id
from .models import LightingZoneConfig


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AstraPoolConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Astra Pool light entities for each lighting zone."""
    coordinator = entry.runtime_data
    pool_id = derive_pool_id(entry.data[CONF_POOL_API_CODE])
    config = coordinator.pool_config

    if not config.has_lighting_zones:
        return

    entities: list[AstraPoolLight] = []
    for zone in config.lighting_zones:
        entities.append(AstraPoolLight(coordinator, pool_id, zone))

    async_add_entities(entities)


class AstraPoolLight(AstraPoolEntity, LightEntity):
    """Representation of an AstralPool lighting zone."""

    _attr_color_mode = ColorMode.ONOFF
    _attr_supported_color_modes = {ColorMode.ONOFF}

    def __init__(
        self,
        coordinator,
        pool_id: str,
        zone_cfg: LightingZoneConfig,
    ) -> None:
        super().__init__(
            coordinator,
            pool_id,
            f"lighting_zone_{zone_cfg.lighting_zone_number}",
        )
        self._zone_number = zone_cfg.lighting_zone_number
        self._color_enabled = zone_cfg.color_enabled
        self._attr_name = zone_cfg.name

        if zone_cfg.color_enabled and zone_cfg.colors_available:
            self._attr_supported_features = LightEntityFeature.EFFECT
            self._color_map: dict[int, str] = {
                c.color_number: c.color_name for c in zone_cfg.colors_available
            }
            self._name_to_number: dict[str, int] = {
                c.color_name: c.color_number for c in zone_cfg.colors_available
            }
            self._attr_effect_list = [
                c.color_name for c in zone_cfg.colors_available
            ]
        else:
            self._color_map = {}
            self._name_to_number = {}
            self._attr_effect_list = None

    @property
    def is_on(self) -> bool:
        lz = self._lighting_zone_status(self._zone_number)
        if lz is None:
            return False
        return lz.mode != LightingMode.OFF

    @property
    def effect(self) -> str | None:
        if not self._color_enabled:
            return None
        lz = self._lighting_zone_status(self._zone_number)
        if lz is None or lz.color is None:
            return None
        return self._color_map.get(lz.color)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        lz = self._lighting_zone_status(self._zone_number)
        attrs: dict[str, Any] = {}
        if lz is not None:
            attrs["lighting_mode"] = LIGHTING_MODE_NAMES.get(lz.mode, str(lz.mode))
        return attrs

    async def async_turn_on(self, **kwargs: Any) -> None:
        api = self.coordinator.api
        await api.async_execute_action(
            ActionCode.SET_LIGHTING_ZONE_MODE,
            device_number=self._zone_number,
            value=str(LightingMode.ON),
        )

        effect = kwargs.get("effect")
        if effect and effect in self._name_to_number:
            color_num = self._name_to_number[effect]
            await api.async_execute_action(
                ActionCode.SET_LIGHTING_ZONE_COLOR,
                device_number=self._zone_number,
                value=str(color_num),
            )

        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.api.async_execute_action(
            ActionCode.SET_LIGHTING_ZONE_MODE,
            device_number=self._zone_number,
            value=str(LightingMode.OFF),
        )
        await self.coordinator.async_request_refresh()
