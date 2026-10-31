"""Light platform for the Whirlpool Appliances integration."""

from typing import Any, override

from .wp.oven import Cavity as OvenCavity, Oven

from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import WhirlpoolConfigEntry
from .entity import WhirlpoolEntity, WhirlpoolOvenEntity
from .wp.microwave import Microwave

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: WhirlpoolConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the light platform."""
    appliances_manager = config_entry.runtime_data
    async_add_entities(
        [
            *(
                WhirlpoolOvenLight(oven, cavity)
                for oven in appliances_manager.ovens
                for cavity in (OvenCavity.Upper, OvenCavity.Lower)
                if oven.get_oven_cavity_exists(cavity)
            ),
            *(WhirlpoolMicrowaveLight(mwo) for mwo in appliances_manager.microwaves),
        ]
    )


class WhirlpoolOvenLight(WhirlpoolOvenEntity, LightEntity):
    """Light for an oven cavity."""

    _appliance: Oven

    _attr_color_mode = ColorMode.ONOFF
    _attr_supported_color_modes = {ColorMode.ONOFF}

    def __init__(self, appliance: Oven, cavity: OvenCavity) -> None:
        """Initialize the oven light."""
        super().__init__(appliance, cavity, "oven_light", "-light")

    @property
    @override
    def is_on(self) -> bool | None:
        """Return whether the light is on."""
        return self._appliance.get_light(self.cavity)

    @override
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        WhirlpoolOvenLight._check_service_request(
            await self._appliance.set_light(True, self.cavity)
        )

    @override
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        WhirlpoolOvenLight._check_service_request(
            await self._appliance.set_light(False, self.cavity)
        )


class WhirlpoolMicrowaveLight(WhirlpoolEntity, LightEntity):
    """Cavity light of a microwave."""

    _appliance: Microwave
    _attr_color_mode = ColorMode.ONOFF
    _attr_supported_color_modes = {ColorMode.ONOFF}
    _attr_translation_key = "microwave_light"

    def __init__(self, appliance: Microwave) -> None:
        """Initialize the microwave light."""
        super().__init__(appliance, unique_id_suffix="-cavity_light")

    @property
    @override
    def is_on(self) -> bool | None:
        """Return whether the light is on."""
        return self._appliance.get_cavity_light()

    @override
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        self._check_service_request(await self._appliance.set_cavity_light(True))

    @override
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        self._check_service_request(await self._appliance.set_cavity_light(False))
