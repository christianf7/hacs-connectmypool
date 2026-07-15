"""Climate platform for the Astra Pool integration (heaters)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import AstraPoolConfigEntry
from .const import (
    ActionCode,
    CONF_POOL_API_CODE,
    HeatCoolSelection,
    HeaterMode,
    PoolSpaSelection,
)
from .entity import AstraPoolEntity, derive_pool_id
from .models import HeaterConfig


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AstraPoolConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Astra Pool climate entities for each heater."""
    coordinator = entry.runtime_data
    pool_id = derive_pool_id(entry.data[CONF_POOL_API_CODE])
    config = coordinator.pool_config

    if not config.has_heaters:
        return

    entities: list[AstraPoolHeaterClimate] = []
    for heater in config.heaters:
        entities.append(
            AstraPoolHeaterClimate(
                coordinator,
                pool_id,
                heater,
                heat_cool_enabled=config.heat_cool_selection_enabled,
                pool_spa_enabled=config.pool_spa_selection_enabled,
            )
        )

    async_add_entities(entities)


class AstraPoolHeaterClimate(AstraPoolEntity, ClimateEntity):
    """Representation of an AstralPool heater as a climate entity."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = 1
    _attr_min_temp = 10
    _attr_max_temp = 40
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )

    def __init__(
        self,
        coordinator,
        pool_id: str,
        heater_cfg: HeaterConfig,
        *,
        heat_cool_enabled: bool,
        pool_spa_enabled: bool,
    ) -> None:
        super().__init__(
            coordinator, pool_id, f"heater_{heater_cfg.heater_number}"
        )
        self._heater_number = heater_cfg.heater_number
        self._heat_cool_enabled = heat_cool_enabled
        self._pool_spa_enabled = pool_spa_enabled
        self._attr_name = f"Heater {heater_cfg.heater_number}"

    @property
    def hvac_modes(self) -> list[HVACMode]:
        modes = [HVACMode.OFF, HVACMode.HEAT]
        if self._heat_cool_enabled:
            modes.append(HVACMode.COOL)
        return modes

    @property
    def hvac_mode(self) -> HVACMode:
        hs = self._heater_status(self._heater_number)
        if hs is None or hs.mode == HeaterMode.OFF:
            return HVACMode.OFF
        if self._heat_cool_enabled:
            if (
                self.coordinator.data.status.heat_cool_selection
                == HeatCoolSelection.COOLING
            ):
                return HVACMode.COOL
        return HVACMode.HEAT

    @property
    def current_temperature(self) -> float | None:
        if self.coordinator.data is None:
            return None
        return float(self.coordinator.data.status.temperature)

    @property
    def target_temperature(self) -> float | None:
        hs = self._heater_status(self._heater_number)
        if hs is None:
            return None
        if (
            self._pool_spa_enabled
            and self.coordinator.data.status.pool_spa_selection
            == PoolSpaSelection.SPA
        ):
            return float(hs.spa_set_temperature)
        return float(hs.set_temperature)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        api = self.coordinator.api
        if hvac_mode == HVACMode.OFF:
            await api.async_execute_action(
                ActionCode.SET_HEATER_MODE,
                device_number=self._heater_number,
                value=str(HeaterMode.OFF),
            )
        elif hvac_mode == HVACMode.HEAT:
            await api.async_execute_action(
                ActionCode.SET_HEATER_MODE,
                device_number=self._heater_number,
                value=str(HeaterMode.ON),
            )
            if self._heat_cool_enabled:
                await api.async_execute_action(
                    ActionCode.SET_HEAT_COOL_SELECTION,
                    value=str(HeatCoolSelection.HEATING),
                )
        elif hvac_mode == HVACMode.COOL:
            await api.async_execute_action(
                ActionCode.SET_HEATER_MODE,
                device_number=self._heater_number,
                value=str(HeaterMode.ON),
            )
            await api.async_execute_action(
                ActionCode.SET_HEAT_COOL_SELECTION,
                value=str(HeatCoolSelection.COOLING),
            )

        await self.coordinator.async_request_refresh()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        temp = kwargs.get("temperature")
        if temp is None:
            return
        await self.coordinator.api.async_execute_action(
            ActionCode.SET_HEATER_SET_TEMPERATURE,
            device_number=self._heater_number,
            value=str(int(temp)),
        )
        await self.coordinator.async_request_refresh()
