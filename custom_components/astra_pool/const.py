"""Constants for the Astra Pool integration."""

from __future__ import annotations

import logging
from enum import IntEnum

DOMAIN = "astra_pool"
LOGGER = logging.getLogger(__package__)

API_BASE_URL = "https://www.connectmypool.com.au"
API_TIMEOUT = 30
DEFAULT_SCAN_INTERVAL = 61  # Seconds — just above the 60 s API throttle

CONF_POOL_API_CODE = "pool_api_code"


# ---------------------------------------------------------------------------
# Action codes (§9.0 of the ConnectMyPool Integration Guide)
# ---------------------------------------------------------------------------
class ActionCode(IntEnum):
    """API action codes for /api/poolaction."""

    CYCLE_CHANNEL_MODE = 1
    SET_VALVE_MODE = 2
    SET_POOL_SPA_SELECTION = 3
    SET_HEATER_MODE = 4
    SET_HEATER_SET_TEMPERATURE = 5
    SET_LIGHTING_ZONE_MODE = 6
    SET_LIGHTING_ZONE_COLOR = 7
    SET_ACTIVE_FAVOURITE = 8
    SET_SOLAR_MODE = 9
    SET_SOLAR_SET_TEMPERATURE = 10
    SEND_LIGHTING_ZONE_SYNC = 11
    SET_HEAT_COOL_SELECTION = 12


# ---------------------------------------------------------------------------
# Failure codes (§11.0)
# ---------------------------------------------------------------------------
class FailureCode(IntEnum):
    """API failure codes returned in error responses."""

    GENERAL_ERROR = 1
    INVALID_POOL_SYSTEM = 2
    INVALID_API_CODE = 3
    API_NOT_ENABLED = 4
    INVALID_API_KEY = 5
    TIME_THROTTLE_EXCEEDED = 6
    POOL_NOT_CONNECTED = 7
    INVALID_ACTION_CODE = 8
    INVALID_VALUE = 9
    INVALID_CHANNEL_NUMBER = 10
    INVALID_VALVE_NUMBER = 11
    POOL_SPA_SELECTION_NOT_ENABLED = 12
    INVALID_HEATER = 13
    INVALID_HEATER_SET_TEMP = 14
    INVALID_LIGHTING_ZONE = 15
    LIGHTING_ZONE_NOT_COLOR_ENABLED = 16
    INVALID_LIGHTING_ZONE_COLOR = 17
    INVALID_FAVOURITE_NUMBER = 18
    INVALID_SOLAR_SYSTEM_NUMBER = 19
    INVALID_SOLAR_SET_TEMP = 20
    LIGHTING_ZONE_DOES_NOT_SUPPORT_SYNC = 21
    HEAT_COOL_SELECTION_NOT_SUPPORTED = 22


# ---------------------------------------------------------------------------
# Execution status (§9.0 / §10.0)
# ---------------------------------------------------------------------------
class ExecutionStatus(IntEnum):
    """Action execution status values."""

    WAITING = 0
    SUCCESS = 1
    FAILED = 2
    TIMEOUT = 3


# ---------------------------------------------------------------------------
# Channel functions (§4.4 / §7.0)
# ---------------------------------------------------------------------------
class ChannelFunction(IntEnum):
    """Channel function types."""

    FILTER_PUMP = 1
    CLEANING_PUMP = 2
    HEATER_PUMP = 3
    BOOSTER_PUMP = 4
    WATERFALL_PUMP = 5
    FOUNTAIN_PUMP = 6
    SPA_PUMP = 7
    SOLAR_PUMP = 8
    BLOWER = 9
    SWIMJET = 10
    JETS = 11
    SPA_JETS = 12
    OVERFLOW = 13
    SPILLWAY = 14
    AUDIO = 15
    HOT_SEAT = 16
    HEATER_POWER = 17
    CUSTOM_NAME = 18


CHANNEL_FUNCTION_NAMES: dict[int, str] = {
    1: "Filter Pump",
    2: "Cleaning Pump",
    3: "Heater Pump",
    4: "Booster Pump",
    5: "Waterfall Pump",
    6: "Fountain Pump",
    7: "Spa Pump",
    8: "Solar Pump",
    9: "Blower",
    10: "Swimjet",
    11: "Jets",
    12: "Spa Jets",
    13: "Overflow",
    14: "Spillway",
    15: "Audio",
    16: "Hot Seat",
    17: "Heater Power",
    18: "Custom Name",
}


# ---------------------------------------------------------------------------
# Channel modes (§8.0)
# ---------------------------------------------------------------------------
class ChannelMode(IntEnum):
    """Channel operating modes."""

    OFF = 0
    AUTO = 1
    ON = 2
    LOW_SPEED = 3
    MEDIUM_SPEED = 4
    HIGH_SPEED = 5


CHANNEL_MODE_NAMES: dict[int, str] = {
    0: "Off",
    1: "Auto",
    2: "On",
    3: "Low Speed",
    4: "Medium Speed",
    5: "High Speed",
}

# Functions that support Off / Auto / On → modelled as select entities.
MULTI_MODE_CHANNEL_FUNCTIONS: frozenset[int] = frozenset({1, 2, 3, 8, 14, 18})

# Documented channel cycle sequences (mode list in cycle order).
# Cycling advances to the next element, wrapping around.
# Filter Pump (documented): On(2) → Auto(1) → Off(0) → On(2)…
# Fountain (documented):    On(2) → Off(0) → On(2)…
CHANNEL_CYCLE_SEQUENCES: dict[int, list[int]] = {
    ChannelFunction.FILTER_PUMP: [2, 1, 0],
    ChannelFunction.FOUNTAIN_PUMP: [2, 0],
}

DEFAULT_MULTI_MODE_CYCLE: list[int] = [2, 1, 0]
DEFAULT_TWO_MODE_CYCLE: list[int] = [2, 0]

MAX_CHANNEL_CYCLES = 6


# ---------------------------------------------------------------------------
# Other mode enums
# ---------------------------------------------------------------------------
class HeaterMode(IntEnum):
    OFF = 0
    ON = 1


class SolarMode(IntEnum):
    OFF = 0
    AUTO = 1
    ON = 2


SOLAR_MODE_NAMES: dict[int, str] = {0: "Off", 1: "Auto", 2: "On"}


class ValveMode(IntEnum):
    OFF = 0
    AUTO = 1
    ON = 2


VALVE_MODE_NAMES: dict[int, str] = {0: "Off", 1: "Auto", 2: "On"}


class LightingMode(IntEnum):
    OFF = 0
    AUTO = 1
    ON = 2


LIGHTING_MODE_NAMES: dict[int, str] = {0: "Off", 1: "Auto", 2: "On"}


class PoolSpaSelection(IntEnum):
    SPA = 0
    POOL = 1


class HeatCoolSelection(IntEnum):
    COOLING = 0
    HEATING = 1


class TemperatureScale(IntEnum):
    CELSIUS = 0
    FAHRENHEIT = 1
