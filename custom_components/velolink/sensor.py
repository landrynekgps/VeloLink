"""Sensor platform for Velolink."""
from __future__ import annotations

import logging
from typing import Callable, Final

from homeassistant.core import HomeAssistant, callback
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo

from .const import (
    DOMAIN,
    NODE_KIND_ANALOG,
    NODE_KIND_VELOSENSOR,
    signal_new_node,
)
from .hub import VelolinkHub, VelolinkNode
from .storage import VelolinkStorage

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES: Final[int] = 0


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Set up sensors."""
    hub: VelolinkHub = hass.data[DOMAIN][entry.entry_id]
    storage: VelolinkStorage = hass.data[DOMAIN][f"{entry.entry_id}_storage"]
    created: set[str] = set()

    @callback
    def _handle_new_node(node: VelolinkNode) -> None:
        if node.kind not in (NODE_KIND_ANALOG, NODE_KIND_VELOSENSOR):
            return
        
        entities = []
        for ch in range(node.channels):
            uid = f"{node.bus_id}-{node.address}-ain-{ch}"
            if uid in created:
                continue
            created.add(uid)
            entities.append(VelolinkAnalogEntity(hub, storage, node, ch))
        
        if entities:
            async_add_entities(entities)

    unsub = async_dispatcher_connect(
        hass, signal_new_node(entry.entry_id), _handle_new_node
    )
    entry.async_on_unload(unsub)


class VelolinkAnalogEntity(SensorEntity):
    """Sensor for Velolink analog input."""
    
    _attr_should_poll = False

    def __init__(
        self,
        hub: VelolinkHub,
        storage: VelolinkStorage,
        node: VelolinkNode,
        ch: int
    ) -> None:
        """Initialize entity."""
        self._hub = hub
        self._storage = storage
        self._node = node
        self._ch = ch
        self._value: float | None = None
        self._unsub: Callable[[], None] | None = None

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._node.bus_id}-{self._node.address}-ain-{self._ch}"

    @property
    def name(self) -> str:
        """Return name."""
        custom_name = self._storage.get_device_name(
            self._node.bus_id, self._node.address
        )
        if custom_name:
            return f"{custom_name} AIN {self._ch}"
        
        if self._node.kind == NODE_KIND_VELOSENSOR:
            return f"VeloSensor {self._node.address}:{self._ch}"
        else:
            return f"Velolink AIN {self._node.address}:{self._ch}"

    @property
    def native_value(self) -> float | None:
        """Return value."""
        return self._value

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return unit."""
        return "V"

    @property
    def device_class(self) -> SensorDeviceClass | None:
        """Return device class."""
        return SensorDeviceClass.VOLTAGE

    @property
    def state_class(self) -> SensorStateClass | str | None:
        """Return state class."""
        return SensorStateClass.MEASUREMENT

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        custom_name = self._storage.get_device_name(
            self._node.bus_id, self._node.address
        )
        
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self._node.bus_id}-{self._node.address}")},
            name=custom_name or f"Velolink {self._node.kind.title()} {self._node.address}",
            manufacturer=self._node.manufacturer,
            model=self._node.model or "IO-ANALOG",
            sw_version=self._node.sw_version,
            hw_version=self._node.hw_version,
            suggested_area=self._node.suggested_area,
        )

    async def async_added_to_hass(self) -> None:
        """Handle entity added."""
        @callback
        def _on_change(val: float) -> None:
            self._value = val
            self.async_write_ha_state()
        
        self._unsub = self._hub.subscribe_analog(
            self._node.bus_id, self._node.address, self._ch, _on_change
        )

    async def async_will_remove_from_hass(self) -> None:
        """Handle entity removal."""
        if self._unsub:
            self._unsub()
            self._unsub = None
