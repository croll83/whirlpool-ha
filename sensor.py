"""The Washer/Dryer/Oven/Microwave Sensor for Whirlpool Appliances."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import override

from whirlpool.appliance import Appliance
from whirlpool.dryer import Dryer, MachineState as DryerMachineState
from whirlpool.oven import CavityState, CookMode, Oven
from whirlpool.washer import MachineState as WasherMachineState, Washer

try:
    from whirlpool.microwave import Microwave, MicrowaveState
    HAS_MICROWAVE = True
except ImportError:
    HAS_MICROWAVE = False
    Microwave = None
    MicrowaveState = None

from homeassistant.components.sensor import (
    RestoreSensor,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.util.dt import utcnow

from . import WhirlpoolConfigEntry
from .entity import WhirlpoolEntity

PARALLEL_UPDATES = 1
SCAN_INTERVAL = timedelta(minutes=5)

# Traduzioni dirette per gli stati
OVEN_STATE_NAMES = {
    CavityState.Standby: "Standby",
    CavityState.Preheating: "Preheating",
    CavityState.Cooking: "Cooking",
    CavityState.NotPresent: "Not present",
}

COOK_MODE_NAMES = {
    CookMode.Standby: "Standby",
    CookMode.Bake: "Bake",
    CookMode.ConvectBake: "Convect bake",
    CookMode.Broil: "Broil",
    CookMode.ConvectBroil: "Convect broil",
    CookMode.ConvectRoast: "Convect roast",
    CookMode.KeepWarm: "Keep warm",
    CookMode.AirFry: "Air fry",
}

if HAS_MICROWAVE:
    MICROWAVE_STATE_NAMES = {
        MicrowaveState.Standby: "Standby",
        MicrowaveState.Running: "Running",
        MicrowaveState.Paused: "Paused",
        MicrowaveState.Complete: "Complete",
    }

WASHER_TANK_FILL = {
    0: None,
    1: "empty",
    2: "25",
    3: "50",
    4: "100",
    5: "active",
}

WASHER_MACHINE_STATE = {
    WasherMachineState.Standby: "standby",
    WasherMachineState.Setting: "setting",
    WasherMachineState.DelayCountdownMode: "delay_countdown",
    WasherMachineState.DelayPause: "delay_paused",
    WasherMachineState.SmartDelay: "smart_delay",
    WasherMachineState.SmartGridPause: "smart_grid_pause",
    WasherMachineState.Pause: "pause",
    WasherMachineState.RunningMainCycle: "running_maincycle",
    WasherMachineState.RunningPostCycle: "running_postcycle",
    WasherMachineState.Exceptions: "exception",
    WasherMachineState.Complete: "complete",
    WasherMachineState.PowerFailure: "power_failure",
    WasherMachineState.ServiceDiagnostic: "service_diagnostic_mode",
    WasherMachineState.FactoryDiagnostic: "factory_diagnostic_mode",
    WasherMachineState.LifeTest: "life_test",
    WasherMachineState.CustomerFocusMode: "customer_focus_mode",
    WasherMachineState.DemoMode: "demo_mode",
    WasherMachineState.HardStopOrError: "hard_stop_or_error",
    WasherMachineState.SystemInit: "system_initialize",
}

DRYER_MACHINE_STATE = {
    DryerMachineState.Standby: "standby",
    DryerMachineState.Setting: "setting",
    DryerMachineState.DelayCountdownMode: "delay_countdown",
    DryerMachineState.DelayPause: "delay_paused",
    DryerMachineState.SmartDelay: "smart_delay",
    DryerMachineState.SmartGridPause: "smart_grid_pause",
    DryerMachineState.Pause: "pause",
    DryerMachineState.RunningMainCycle: "running_maincycle",
    DryerMachineState.RunningPostCycle: "running_postcycle",
    DryerMachineState.Exceptions: "exception",
    DryerMachineState.Complete: "complete",
    DryerMachineState.PowerFailure: "power_failure",
    DryerMachineState.ServiceDiagnostic: "service_diagnostic_mode",
    DryerMachineState.FactoryDiagnostic: "factory_diagnostic_mode",
    DryerMachineState.LifeTest: "life_test",
    DryerMachineState.CustomerFocusMode: "customer_focus_mode",
    DryerMachineState.DemoMode: "demo_mode",
    DryerMachineState.HardStopOrError: "hard_stop_or_error",
    DryerMachineState.SystemInit: "system_initialize",
    DryerMachineState.Cancelled: "cancelled",
}

STATE_CYCLE_FILLING = "cycle_filling"
STATE_CYCLE_RINSING = "cycle_rinsing"
STATE_CYCLE_SENSING = "cycle_sensing"
STATE_CYCLE_SOAKING = "cycle_soaking"
STATE_CYCLE_SPINNING = "cycle_spinning"
STATE_CYCLE_WASHING = "cycle_washing"


def washer_state(washer: Washer) -> str | None:
    machine_state = washer.get_machine_state()
    if machine_state == WasherMachineState.RunningMainCycle:
        if washer.get_cycle_status_filling():
            return STATE_CYCLE_FILLING
        if washer.get_cycle_status_rinsing():
            return STATE_CYCLE_RINSING
        if washer.get_cycle_status_sensing():
            return STATE_CYCLE_SENSING
        if washer.get_cycle_status_soaking():
            return STATE_CYCLE_SOAKING
        if washer.get_cycle_status_spinning():
            return STATE_CYCLE_SPINNING
        if washer.get_cycle_status_washing():
            return STATE_CYCLE_WASHING
    return WASHER_MACHINE_STATE.get(machine_state)


def dryer_state(dryer: Dryer) -> str | None:
    machine_state = dryer.get_machine_state()
    if machine_state == DryerMachineState.RunningMainCycle:
        if dryer.get_cycle_status_sensing():
            return STATE_CYCLE_SENSING
    return DRYER_MACHINE_STATE.get(machine_state)


def oven_state(machine: Oven) -> str | None:
    cavity_state = machine.get_cavity_state()
    if cavity_state is None:
        return None
    return OVEN_STATE_NAMES.get(cavity_state, str(cavity_state))


def cook_mode(machine: Oven) -> str | None:
    mode = machine.get_cook_mode()
    if mode is None:
        return None
    return COOK_MODE_NAMES.get(mode, str(mode))


def microwave_state(machine) -> str | None:
    if not HAS_MICROWAVE:
        return None
    state = machine.get_state()
    if state is None:
        return None
    return MICROWAVE_STATE_NAMES.get(state, str(state))


@dataclass(frozen=True, kw_only=True)
class WhirlpoolSensorEntityDescription(SensorEntityDescription):
    value_fn: Callable[[Appliance], str | float | int | None]


WASHER_STATE_OPTIONS = [
    *WASHER_MACHINE_STATE.values(),
    STATE_CYCLE_FILLING,
    STATE_CYCLE_RINSING,
    STATE_CYCLE_SENSING,
    STATE_CYCLE_SOAKING,
    STATE_CYCLE_SPINNING,
    STATE_CYCLE_WASHING,
]

DRYER_STATE_OPTIONS = [
    *DRYER_MACHINE_STATE.values(),
    STATE_CYCLE_SENSING,
]

WASHER_SENSORS: tuple[WhirlpoolSensorEntityDescription, ...] = (
    WhirlpoolSensorEntityDescription(
        key="state",
        translation_key="washer_state",
        device_class=SensorDeviceClass.ENUM,
        options=WASHER_STATE_OPTIONS,
        value_fn=washer_state,
    ),
    WhirlpoolSensorEntityDescription(
        key="DispenseLevel",
        translation_key="whirlpool_tank",
        entity_registry_enabled_default=False,
        device_class=SensorDeviceClass.ENUM,
        options=[value for value in WASHER_TANK_FILL.values() if value],
        value_fn=lambda washer: WASHER_TANK_FILL.get(washer.get_dispense_1_level()),
    ),
)

DRYER_SENSORS: tuple[WhirlpoolSensorEntityDescription, ...] = (
    WhirlpoolSensorEntityDescription(
        key="state",
        translation_key="dryer_state",
        device_class=SensorDeviceClass.ENUM,
        options=DRYER_STATE_OPTIONS,
        value_fn=dryer_state,
    ),
)

OVEN_SENSORS: tuple[WhirlpoolSensorEntityDescription, ...] = (
    WhirlpoolSensorEntityDescription(
        key="oven_state",
        name="State",
        icon="mdi:stove",
        value_fn=oven_state,
    ),
    WhirlpoolSensorEntityDescription(
        key="cook_mode",
        name="Cook mode",
        icon="mdi:chef-hat",
        value_fn=cook_mode,
    ),
    WhirlpoolSensorEntityDescription(
        key="current_temp",
        name="Temperature",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda oven: oven.get_temp(),
    ),
    WhirlpoolSensorEntityDescription(
        key="target_temp",
        name="Target temperature",
        icon="mdi:thermometer-check",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda oven: oven.get_target_temp(),
    ),
    WhirlpoolSensorEntityDescription(
        key="cycle_count",
        name="Total cycles",
        icon="mdi:counter",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda oven: oven.get_cook_time(),
    ),
)

MICROWAVE_SENSORS: tuple[WhirlpoolSensorEntityDescription, ...] = (
    WhirlpoolSensorEntityDescription(
        key="microwave_state",
        name="State",
        icon="mdi:microwave",
        value_fn=microwave_state,
    ),
    WhirlpoolSensorEntityDescription(
        key="current_temp",
        name="Temperature",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda mwo: mwo.get_temp(),
    ),
    WhirlpoolSensorEntityDescription(
        key="target_temp",
        name="Target temperature",
        icon="mdi:thermometer-check",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda mwo: mwo.get_target_temp(),
    ),
    WhirlpoolSensorEntityDescription(
        key="cook_power",
        name="Power level",
        icon="mdi:lightning-bolt",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda mwo: mwo.get_cook_power(),
    ),
    WhirlpoolSensorEntityDescription(
        key="cycle_count",
        name="Total cycles",
        icon="mdi:counter",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda mwo: mwo.get_cycle_count(),
    ),
) if HAS_MICROWAVE else ()

WASHER_DRYER_OVEN_TIME_SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="timeremaining",
        name="Time remaining",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:progress-clock",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: WhirlpoolConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    appliances_manager = config_entry.runtime_data

    washer_sensors = [
        WhirlpoolSensor(washer, description)
        for washer in appliances_manager.washers
        for description in WASHER_SENSORS
    ]

    washer_time_sensors = [
        WasherTimeSensor(washer, description)
        for washer in appliances_manager.washers
        for description in WASHER_DRYER_OVEN_TIME_SENSORS
    ]

    dryer_sensors = [
        WhirlpoolSensor(dryer, description)
        for dryer in appliances_manager.dryers
        for description in DRYER_SENSORS
    ]

    dryer_time_sensors = [
        DryerTimeSensor(dryer, description)
        for dryer in appliances_manager.dryers
        for description in WASHER_DRYER_OVEN_TIME_SENSORS
    ]

    oven_sensors = [
        WhirlpoolSensor(oven, description)
        for oven in appliances_manager.ovens
        for description in OVEN_SENSORS
    ]

    oven_time_sensors = [
        OvenTimeSensor(oven, description)
        for oven in appliances_manager.ovens
        for description in WASHER_DRYER_OVEN_TIME_SENSORS
    ]

    microwave_sensors = []
    microwave_time_sensors = []
    if HAS_MICROWAVE and hasattr(appliances_manager, 'microwaves'):
        microwave_sensors = [
            WhirlpoolSensor(mwo, description)
            for mwo in appliances_manager.microwaves
            for description in MICROWAVE_SENSORS
        ]
        microwave_time_sensors = [
            MicrowaveTimeSensor(mwo, description)
            for mwo in appliances_manager.microwaves
            for description in WASHER_DRYER_OVEN_TIME_SENSORS
        ]

    async_add_entities(
        [
            *washer_sensors,
            *washer_time_sensors,
            *dryer_sensors,
            *dryer_time_sensors,
            *oven_sensors,
            *oven_time_sensors,
            *microwave_sensors,
            *microwave_time_sensors,
        ]
    )


class WhirlpoolSensor(WhirlpoolEntity, SensorEntity):
    def __init__(
        self, appliance: Appliance, description: WhirlpoolSensorEntityDescription
    ) -> None:
        super().__init__(appliance, unique_id_suffix=f"-{description.key}")
        self.entity_description: WhirlpoolSensorEntityDescription = description

    @property
    def native_value(self) -> StateType | str:
        return self.entity_description.value_fn(self._appliance)


class WasherDryerTimeSensorBase(WhirlpoolEntity, RestoreSensor, ABC):
    _attr_should_poll = True
    _appliance: Washer | Dryer

    def __init__(
        self, appliance: Washer | Dryer, description: SensorEntityDescription
    ) -> None:
        super().__init__(appliance, unique_id_suffix=f"-{description.key}")
        self.entity_description = description
        self._running: bool | None = None
        self._value: datetime | None = None

    @abstractmethod
    def _is_machine_state_finished(self) -> bool:
        pass

    @abstractmethod
    def _is_machine_state_running(self) -> bool:
        pass

    async def async_added_to_hass(self) -> None:
        if restored_data := await self.async_get_last_sensor_data():
            if isinstance(restored_data.native_value, datetime):
                self._value = restored_data.native_value
        await super().async_added_to_hass()

    async def async_update(self) -> None:
        await self._appliance.fetch_data()

    @override
    @property
    def native_value(self) -> datetime | None:
        now = utcnow()
        if self._is_machine_state_finished() and self._running:
            self._running = False
            self._value = now
        if self._is_machine_state_running():
            self._running = True
            new_timestamp = now + timedelta(seconds=self._appliance.get_time_remaining())
            if self._value is None or (
                isinstance(self._value, datetime)
                and abs(new_timestamp - self._value) > timedelta(seconds=60)
            ):
                self._value = new_timestamp
        return self._value


class WasherTimeSensor(WasherDryerTimeSensorBase):
    _appliance: Washer

    def _is_machine_state_finished(self) -> bool:
        return self._appliance.get_machine_state() in {
            WasherMachineState.Complete,
            WasherMachineState.Standby,
        }

    def _is_machine_state_running(self) -> bool:
        return self._appliance.get_machine_state() is WasherMachineState.RunningMainCycle


class DryerTimeSensor(WasherDryerTimeSensorBase):
    _appliance: Dryer

    def _is_machine_state_finished(self) -> bool:
        return self._appliance.get_machine_state() in {
            DryerMachineState.Complete,
            DryerMachineState.Standby,
        }

    def _is_machine_state_running(self) -> bool:
        return self._appliance.get_machine_state() is DryerMachineState.RunningMainCycle


class OvenTimeSensor(WhirlpoolEntity, RestoreSensor):
    _attr_should_poll = True
    _appliance: Oven

    def __init__(self, appliance: Oven, description: SensorEntityDescription) -> None:
        super().__init__(appliance, unique_id_suffix=f"-{description.key}")
        self.entity_description = description
        self._running: bool | None = None
        self._value: datetime | None = None

    async def async_added_to_hass(self) -> None:
        if restored_data := await self.async_get_last_sensor_data():
            if isinstance(restored_data.native_value, datetime):
                self._value = restored_data.native_value
        await super().async_added_to_hass()

    async def async_update(self) -> None:
        await self._appliance.fetch_data()

    @override
    @property
    def native_value(self) -> datetime | None:
        machine_state = self._appliance.get_cavity_state()
        now = utcnow()
        if machine_state is CavityState.Standby and self._running:
            self._running = False
            self._value = now
        if machine_state is CavityState.Cooking:
            self._running = True
            cook_time = self._appliance.get_cook_time() or 0
            new_timestamp = now + timedelta(seconds=cook_time)
            if self._value is None or (
                isinstance(self._value, datetime)
                and abs(new_timestamp - self._value) > timedelta(seconds=60)
            ):
                self._value = new_timestamp
        return self._value


class MicrowaveTimeSensor(WhirlpoolEntity, RestoreSensor):
    _attr_should_poll = True

    def __init__(self, appliance, description: SensorEntityDescription) -> None:
        super().__init__(appliance, unique_id_suffix=f"-{description.key}")
        self.entity_description = description
        self._running: bool | None = None
        self._value: datetime | None = None

    async def async_added_to_hass(self) -> None:
        if restored_data := await self.async_get_last_sensor_data():
            if isinstance(restored_data.native_value, datetime):
                self._value = restored_data.native_value
        await super().async_added_to_hass()

    async def async_update(self) -> None:
        await self._appliance.fetch_data()

    @override
    @property
    def native_value(self) -> datetime | None:
        if not HAS_MICROWAVE:
            return None
        machine_state = self._appliance.get_state()
        now = utcnow()
        if machine_state is MicrowaveState.Standby and self._running:
            self._running = False
            self._value = now
        if machine_state is MicrowaveState.Running:
            self._running = True
            remaining = self._appliance.get_cook_time_remaining() or 0
            new_timestamp = now + timedelta(seconds=remaining)
            if self._value is None or (
                isinstance(self._value, datetime)
                and abs(new_timestamp - self._value) > timedelta(seconds=60)
            ):
                self._value = new_timestamp
        return self._value
