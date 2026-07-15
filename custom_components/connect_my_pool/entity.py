"""Base entity for the Connect My Pool integration."""

from __future__ import annotations

import hashlib

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ConnectMyPoolDataUpdateCoordinator
from .models import (
    ChannelStatus,
    HeaterStatus,
    LightingZoneStatus,
    SolarStatus,
    ValveStatus,
)


def derive_pool_id(api_code: str) -> str:
    """Derive a stable, non-reversible identifier from the Pool API Code."""
    return hashlib.sha256(api_code.encode()).hexdigest()[:12]


class ConnectMyPoolEntity(CoordinatorEntity[ConnectMyPoolDataUpdateCoordinator]):
    """Shared base for all Connect My Pool entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ConnectMyPoolDataUpdateCoordinator,
        pool_id: str,
        unique_suffix: str,
    ) -> None:
        super().__init__(coordinator)
        self._pool_id = pool_id
        self._attr_unique_id = f"{pool_id}_{unique_suffix}"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._pool_id)},
            name="Connect My Pool",
            manufacturer="AstralPool",
            model="ConnectMyPool",
            configuration_url="https://www.connectmypool.com.au",
        )

    def _heater_status(self, heater_number: int) -> HeaterStatus | None:
        for h in self.coordinator.data.status.heaters:
            if h.heater_number == heater_number:
                return h
        return None

    def _solar_status(self, solar_number: int) -> SolarStatus | None:
        for s in self.coordinator.data.status.solar_systems:
            if s.solar_number == solar_number:
                return s
        return None

    def _channel_status(self, channel_number: int) -> ChannelStatus | None:
        for c in self.coordinator.data.status.channels:
            if c.channel_number == channel_number:
                return c
        return None

    def _valve_status(self, valve_number: int) -> ValveStatus | None:
        for v in self.coordinator.data.status.valves:
            if v.valve_number == valve_number:
                return v
        return None

    def _lighting_zone_status(
        self, zone_number: int
    ) -> LightingZoneStatus | None:
        for lz in self.coordinator.data.status.lighting_zones:
            if lz.lighting_zone_number == zone_number:
                return lz
        return None
