"""Button platform for Velolink."""

from __future__ import annotations

import logging
from typing import Final

from homeassistant.core import HomeAssistant
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo, EntityCategory

from .const import DOMAIN
from .hub import VelolinkHub

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES: Final[int] = 0


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Set up buttons."""
    hub: VelolinkHub = hass.data[DOMAIN][entry.entry_id]

    entities = [
        VelolinkDiscoveryButton(hub, entry.entry_id, "bus1", "Skanuj Bus 1"),
        VelolinkDiscoveryButton(hub, entry.entry_id, "bus2", "Skanuj Bus 2"),
        VelolinkDiscoveryButton(hub, entry.entry_id, "all", "Skanuj wszystkie"),
    ]

    async_add_entities(entities)


class VelolinkDiscoveryButton(ButtonEntity):
    """Button to trigger discovery."""

    # pylint: disable=abstract-method

    _attr_should_poll = False
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self, hub: VelolinkHub, entry_id: str, target: str, name: str
    ) -> None:
        """Initialize button."""
        self._hub = hub
        self._entry_id = entry_id
        self._target = target
        self._attr_name = name
        self._attr_unique_id = f"{entry_id}-discovery-{target}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name="Velolink Hub",
            manufacturer="Velolink",
            model="RS485 Gateway",
        )

    async def async_press(self) -> None:
        """Handle button press."""
        _LOGGER.info("Discovery triggered for: %s", self._target)

        if self._target == "bus1":
            await self._hub.async_discovery_bus("bus1")
        elif self._target == "bus2":
            await self._hub.async_discovery_bus("bus2")
        elif self._target == "all":
            await self._hub.async_discovery_all()
