"""Sensor platform for the Astra Pool integration."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import AstraPoolConfigEntry
from .const import CONF_POOL_API_CODE
from .entity import AstraPoolEntity, derive_pool_id


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AstraPoolConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Astra Pool sensors."""
    coordinator = entry.runtime_data
    pool_id = derive_pool_id(entry.data[CONF_POOL_API_CODE])

    async_add_entities([AstraPoolWaterTemperatureSensor(coordinator, pool_id)])


class AstraPoolWaterTemperatureSensor(AstraPoolEntity, SensorEntity):
    """Water temperature sensor."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_name = "Water Temperature"

    def __init__(self, coordinator, pool_id: str) -> None:
        super().__init__(coordinator, pool_id, "water_temperature")

    @property
    def native_value(self) -> int | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.status.temperature
