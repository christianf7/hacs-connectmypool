"""Data models for the Astra Pool integration."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class HeaterConfig:
    """Configuration for a single heater."""

    heater_number: int


@dataclass(frozen=True)
class SolarConfig:
    """Configuration for a single solar heater."""

    solar_number: int


@dataclass(frozen=True)
class ChannelConfig:
    """Configuration for a single channel device."""

    channel_number: int
    function: int
    name: str


@dataclass(frozen=True)
class ValveConfig:
    """Configuration for a single valve."""

    valve_number: int
    function: int
    name: str


@dataclass(frozen=True)
class LightingColorConfig:
    """A single available lighting colour/program."""

    color_number: int
    color_name: str


@dataclass(frozen=True)
class LightingZoneConfig:
    """Configuration for a single lighting zone."""

    lighting_zone_number: int
    name: str
    color_enabled: bool
    colors_available: tuple[LightingColorConfig, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class FavouriteConfig:
    """Configuration for a single favourite."""

    favourite_number: int
    name: str


@dataclass(frozen=True)
class PoolConfiguration:
    """Complete pool configuration from /api/poolconfig."""

    pool_spa_selection_enabled: bool
    heat_cool_selection_enabled: bool
    has_heaters: bool
    has_solar_systems: bool
    has_channels: bool
    has_valves: bool
    has_lighting_zones: bool
    has_favourites: bool
    heaters: tuple[HeaterConfig, ...] = field(default_factory=tuple)
    solar_systems: tuple[SolarConfig, ...] = field(default_factory=tuple)
    channels: tuple[ChannelConfig, ...] = field(default_factory=tuple)
    valves: tuple[ValveConfig, ...] = field(default_factory=tuple)
    lighting_zones: tuple[LightingZoneConfig, ...] = field(default_factory=tuple)
    favourites: tuple[FavouriteConfig, ...] = field(default_factory=tuple)


# ---------------------------------------------------------------------------
# Status models
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class HeaterStatus:
    """Runtime status of a single heater."""

    heater_number: int
    mode: int
    set_temperature: int
    spa_set_temperature: int


@dataclass(frozen=True)
class SolarStatus:
    """Runtime status of a single solar heater."""

    solar_number: int
    mode: int
    set_temperature: int


@dataclass(frozen=True)
class ChannelStatus:
    """Runtime status of a single channel."""

    channel_number: int
    mode: int


@dataclass(frozen=True)
class ValveStatus:
    """Runtime status of a single valve."""

    valve_number: int
    mode: int


@dataclass(frozen=True)
class LightingZoneStatus:
    """Runtime status of a single lighting zone."""

    lighting_zone_number: int
    mode: int
    color: int | None = None


@dataclass(frozen=True)
class PoolStatus:
    """Complete pool status from /api/poolstatus."""

    pool_spa_selection: int
    heat_cool_selection: int
    temperature: int
    active_favourite: int
    heaters: tuple[HeaterStatus, ...] = field(default_factory=tuple)
    solar_systems: tuple[SolarStatus, ...] = field(default_factory=tuple)
    channels: tuple[ChannelStatus, ...] = field(default_factory=tuple)
    valves: tuple[ValveStatus, ...] = field(default_factory=tuple)
    lighting_zones: tuple[LightingZoneStatus, ...] = field(default_factory=tuple)


@dataclass
class AstraPoolData:
    """Combined config + status held by the coordinator."""

    config: PoolConfiguration
    status: PoolStatus
