"""Number platform for the Connect My Pool integration (solar set temperature)."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ConnectMyPoolConfigEntry
from .const import ActionCode, CONF_POOL_API_CODE
from .entity import ConnectMyPoolEntity, derive_pool_id
from .models import SolarConfig


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConnectMyPoolConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Connect My Pool number entities for solar set temperatures."""
    coordinator = entry.runtime_data
    pool_id = derive_pool_id(entry.data[CONF_POOL_API_CODE])
    config = coordinator.pool_config

    if not config.has_solar_systems:
        return

    entities: list[ConnectMyPoolSolarTemperature] = []
    for solar in config.solar_systems:
        entities.append(ConnectMyPoolSolarTemperature(coordinator, pool_id, solar))

    async_add_entities(entities)


class ConnectMyPoolSolarTemperature(ConnectMyPoolEntity, NumberEntity):
    """Solar heater target temperature."""

    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_native_min_value = 10
    _attr_native_max_value = 40
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER

    def __init__(
        self, coordinator, pool_id: str, solar_cfg: SolarConfig
    ) -> None:
        super().__init__(
            coordinator,
            pool_id,
            f"solar_{solar_cfg.solar_number}_temperature",
        )
        self._solar_number = solar_cfg.solar_number
        self._attr_name = f"Solar {solar_cfg.solar_number} Temperature"

    @property
    def native_value(self) -> float | None:
        ss = self._solar_status(self._solar_number)
        if ss is None:
            return None
        return float(ss.set_temperature)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.api.async_execute_action(
            ActionCode.SET_SOLAR_SET_TEMPERATURE,
            device_number=self._solar_number,
            value=str(int(value)),
        )
        await self.coordinator.async_request_refresh()
