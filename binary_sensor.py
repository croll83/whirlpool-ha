"""Binary sensors for the Whirlpool Appliances integration."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta

from whirlpool.appliance import Appliance

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import WhirlpoolConfigEntry
from .entity import WhirlpoolEntity

PARALLEL_UPDATES = 1
SCAN_INTERVAL = timedelta(minutes=5)


@dataclass(frozen=True, kw_only=True)
class WhirlpoolBinarySensorEntityDescription(BinarySensorEntityDescription):
    value_fn: Callable[[Appliance], bool | None]


WASHER_DRYER_SENSORS: list[WhirlpoolBinarySensorEntityDescription] = [
    WhirlpoolBinarySensorEntityDescription(
        key="door",
        device_class=BinarySensorDeviceClass.DOOR,
        value_fn=lambda appliance: appliance.get_door_open(),
    )
]

OVEN_SENSORS: list[WhirlpoolBinarySensorEntityDescription] = [
    WhirlpoolBinarySensorEntityDescription(
        key="door",
        device_class=BinarySensorDeviceClass.DOOR,
        value_fn=lambda appliance: appliance.get_door_opened(),
    ),
    WhirlpoolBinarySensorEntityDescription(
        key="light",
        translation_key="light",
        device_class=BinarySensorDeviceClass.LIGHT,
        value_fn=lambda appliance: appliance.get_light(),
    ),
]

MICROWAVE_SENSORS: list[WhirlpoolBinarySensorEntityDescription] = [
    WhirlpoolBinarySensorEntityDescription(
        key="door",
        device_class=BinarySensorDeviceClass.DOOR,
        value_fn=lambda appliance: appliance.get_door_opened(),
    ),
    WhirlpoolBinarySensorEntityDescription(
        key="light",
        translation_key="light",
        device_class=BinarySensorDeviceClass.LIGHT,
        value_fn=lambda appliance: appliance.get_light(),
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: WhirlpoolConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    appliances_manager = config_entry.runtime_data

    washer_binary_sensors = [
        WhirlpoolBinarySensor(washer, description)
        for washer in appliances_manager.washers
        for description in WASHER_DRYER_SENSORS
    ]

    dryer_binary_sensors = [
        WhirlpoolBinarySensor(dryer, description)
        for dryer in appliances_manager.dryers
        for description in WASHER_DRYER_SENSORS
    ]

    oven_binary_sensors = [
        WhirlpoolBinarySensor(oven, description)
        for oven in appliances_manager.ovens
        for description in OVEN_SENSORS
    ]

    microwave_binary_sensors = []
    if hasattr(appliances_manager, 'microwaves'):
        microwave_binary_sensors = [
            WhirlpoolBinarySensor(mwo, description)
            for mwo in appliances_manager.microwaves
            for description in MICROWAVE_SENSORS
        ]

    async_add_entities(
        [*washer_binary_sensors, *dryer_binary_sensors, *oven_binary_sensors, *microwave_binary_sensors]
    )


class WhirlpoolBinarySensor(WhirlpoolEntity, BinarySensorEntity):
    def __init__(
        self, appliance: Appliance, description: WhirlpoolBinarySensorEntityDescription
    ) -> None:
        super().__init__(appliance, unique_id_suffix=f"-{description.key}")
        self.entity_description: WhirlpoolBinarySensorEntityDescription = description

    @property
    def is_on(self) -> bool | None:
        return self.entity_description.value_fn(self._appliance)
