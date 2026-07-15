"""Select platform for the Astra Pool integration."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import AstraPoolConfigEntry
from .const import (
    ActionCode,
    CHANNEL_CYCLE_SEQUENCES,
    CHANNEL_MODE_NAMES,
    CONF_POOL_API_CODE,
    DEFAULT_MULTI_MODE_CYCLE,
    LOGGER,
    MAX_CHANNEL_CYCLES,
    MULTI_MODE_CHANNEL_FUNCTIONS,
    SOLAR_MODE_NAMES,
    VALVE_MODE_NAMES,
    PoolSpaSelection,
    SolarMode,
    ValveMode,
)
from .entity import AstraPoolEntity, derive_pool_id
from .models import ChannelConfig, SolarConfig, ValveConfig


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AstraPoolConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Astra Pool select entities."""
    coordinator = entry.runtime_data
    pool_id = derive_pool_id(entry.data[CONF_POOL_API_CODE])
    config = coordinator.pool_config

    entities: list[SelectEntity] = []

    # Pool / Spa selection
    if config.pool_spa_selection_enabled:
        entities.append(AstraPoolSpaSelect(coordinator, pool_id))

    # Favourites
    if config.has_favourites and config.favourites:
        entities.append(AstraPoolFavouriteSelect(coordinator, pool_id, config.favourites))

    # Valves
    if config.has_valves:
        for valve in config.valves:
            entities.append(AstraPoolValveSelect(coordinator, pool_id, valve))

    # Solar systems (mode selector)
    if config.has_solar_systems:
        for solar in config.solar_systems:
            entities.append(AstraPoolSolarModeSelect(coordinator, pool_id, solar))

    # Multi-mode channels (Off / Auto / On)
    if config.has_channels:
        for channel in config.channels:
            if channel.function in MULTI_MODE_CHANNEL_FUNCTIONS:
                entities.append(
                    AstraPoolChannelSelect(coordinator, pool_id, channel)
                )

    async_add_entities(entities)


# ---------------------------------------------------------------------------
# Pool / Spa
# ---------------------------------------------------------------------------
class AstraPoolSpaSelect(AstraPoolEntity, SelectEntity):
    """Pool / Spa mode selector."""

    _attr_options = ["Pool", "Spa"]
    _attr_name = "Pool / Spa Mode"

    def __init__(self, coordinator, pool_id: str) -> None:
        super().__init__(coordinator, pool_id, "pool_spa_mode")

    @property
    def current_option(self) -> str | None:
        sel = self.coordinator.data.status.pool_spa_selection
        return "Pool" if sel == PoolSpaSelection.POOL else "Spa"

    async def async_select_option(self, option: str) -> None:
        value = (
            str(PoolSpaSelection.POOL)
            if option == "Pool"
            else str(PoolSpaSelection.SPA)
        )
        await self.coordinator.api.async_execute_action(
            ActionCode.SET_POOL_SPA_SELECTION, value=value
        )
        await self.coordinator.async_request_refresh()


# ---------------------------------------------------------------------------
# Favourites
# ---------------------------------------------------------------------------
class AstraPoolFavouriteSelect(AstraPoolEntity, SelectEntity):
    """Active favourite selector."""

    _attr_name = "Favourite"

    def __init__(self, coordinator, pool_id: str, favourites) -> None:
        super().__init__(coordinator, pool_id, "favourite")
        self._fav_map: dict[str, int] = {f.name: f.favourite_number for f in favourites}
        self._num_map: dict[int, str] = {f.favourite_number: f.name for f in favourites}
        self._attr_options = [f.name for f in favourites]

    @property
    def current_option(self) -> str | None:
        active = self.coordinator.data.status.active_favourite
        if active == 255:
            return None
        return self._num_map.get(active)

    async def async_select_option(self, option: str) -> None:
        fav_num = self._fav_map.get(option)
        if fav_num is None:
            LOGGER.warning("Unknown favourite selected: %s", option)
            return
        await self.coordinator.api.async_execute_action(
            ActionCode.SET_ACTIVE_FAVOURITE, device_number=fav_num
        )
        await self.coordinator.async_request_refresh()


# ---------------------------------------------------------------------------
# Valves
# ---------------------------------------------------------------------------
class AstraPoolValveSelect(AstraPoolEntity, SelectEntity):
    """Valve mode selector (Off / Auto / On)."""

    _attr_options = ["Off", "Auto", "On"]

    def __init__(self, coordinator, pool_id: str, valve_cfg: ValveConfig) -> None:
        super().__init__(coordinator, pool_id, f"valve_{valve_cfg.valve_number}")
        self._valve_number = valve_cfg.valve_number
        self._attr_name = valve_cfg.name

    @property
    def current_option(self) -> str | None:
        vs = self._valve_status(self._valve_number)
        if vs is None:
            return None
        return VALVE_MODE_NAMES.get(vs.mode, str(vs.mode))

    async def async_select_option(self, option: str) -> None:
        mode_val = {v: k for k, v in VALVE_MODE_NAMES.items()}.get(option)
        if mode_val is None:
            return
        await self.coordinator.api.async_execute_action(
            ActionCode.SET_VALVE_MODE,
            device_number=self._valve_number,
            value=str(mode_val),
        )
        await self.coordinator.async_request_refresh()


# ---------------------------------------------------------------------------
# Solar mode
# ---------------------------------------------------------------------------
class AstraPoolSolarModeSelect(AstraPoolEntity, SelectEntity):
    """Solar heater mode selector (Off / Auto / On)."""

    _attr_options = ["Off", "Auto", "On"]

    def __init__(self, coordinator, pool_id: str, solar_cfg: SolarConfig) -> None:
        super().__init__(coordinator, pool_id, f"solar_{solar_cfg.solar_number}_mode")
        self._solar_number = solar_cfg.solar_number
        self._attr_name = f"Solar {solar_cfg.solar_number} Mode"

    @property
    def current_option(self) -> str | None:
        ss = self._solar_status(self._solar_number)
        if ss is None:
            return None
        return SOLAR_MODE_NAMES.get(ss.mode, str(ss.mode))

    async def async_select_option(self, option: str) -> None:
        mode_val = {v: k for k, v in SOLAR_MODE_NAMES.items()}.get(option)
        if mode_val is None:
            return
        await self.coordinator.api.async_execute_action(
            ActionCode.SET_SOLAR_MODE,
            device_number=self._solar_number,
            value=str(mode_val),
        )
        await self.coordinator.async_request_refresh()


# ---------------------------------------------------------------------------
# Multi-mode channels
# ---------------------------------------------------------------------------
class AstraPoolChannelSelect(AstraPoolEntity, SelectEntity):
    """Multi-mode channel selector using Cycle Channel Mode action.

    The ConnectMyPool API does not expose a direct "set mode" action for
    channels — it only provides "Cycle Channel Mode" (action 1).  This entity
    calculates how many cycle commands are needed to reach the desired mode
    based on the known cycle sequence for the channel's function type, then
    verifies the actual state after cycling.
    """

    def __init__(
        self, coordinator, pool_id: str, channel_cfg: ChannelConfig
    ) -> None:
        super().__init__(
            coordinator, pool_id, f"channel_{channel_cfg.channel_number}"
        )
        self._channel_number = channel_cfg.channel_number
        self._function = channel_cfg.function
        self._attr_name = channel_cfg.name

        cycle_seq = CHANNEL_CYCLE_SEQUENCES.get(
            channel_cfg.function, DEFAULT_MULTI_MODE_CYCLE
        )
        self._cycle_sequence = cycle_seq

        self._attr_options = [
            CHANNEL_MODE_NAMES[m] for m in cycle_seq if m in CHANNEL_MODE_NAMES
        ]

    @property
    def current_option(self) -> str | None:
        cs = self._channel_status(self._channel_number)
        if cs is None:
            return None
        return CHANNEL_MODE_NAMES.get(cs.mode, str(cs.mode))

    async def async_select_option(self, option: str) -> None:
        name_to_mode = {v: k for k, v in CHANNEL_MODE_NAMES.items()}
        target_mode = name_to_mode.get(option)
        if target_mode is None:
            LOGGER.warning("Unknown channel mode requested: %s", option)
            return

        cs = self._channel_status(self._channel_number)
        if cs is None:
            LOGGER.warning("No status available for channel %d", self._channel_number)
            return

        current_mode = cs.mode
        if current_mode == target_mode:
            return

        cycles_needed = self._calculate_cycles(current_mode, target_mode)
        if cycles_needed == 0:
            return

        cycles_needed = min(cycles_needed, MAX_CHANNEL_CYCLES)

        api = self.coordinator.api
        for i in range(cycles_needed):
            wait = i == cycles_needed - 1
            await api.async_execute_action(
                ActionCode.CYCLE_CHANNEL_MODE,
                device_number=self._channel_number,
                wait_for_execution=wait,
            )

        await self.coordinator.async_request_refresh()

        cs_after = self._channel_status(self._channel_number)
        if cs_after and cs_after.mode != target_mode:
            LOGGER.warning(
                "Channel %d: expected mode %d after cycling but got %d",
                self._channel_number,
                target_mode,
                cs_after.mode,
            )

    def _calculate_cycles(self, current: int, target: int) -> int:
        """Calculate cycles needed within the known sequence."""
        seq = self._cycle_sequence
        if current not in seq or target not in seq:
            LOGGER.warning(
                "Channel %d: mode %d or %d not in cycle sequence %s — "
                "falling back to single cycle",
                self._channel_number,
                current,
                target,
                seq,
            )
            return 1

        idx_current = seq.index(current)
        idx_target = seq.index(target)
        return (idx_target - idx_current) % len(seq)
