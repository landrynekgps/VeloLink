"""Velolink integration for Home Assistant."""

from __future__ import annotations

import logging
from typing import Any
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.const import Platform
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    CONF_PORT1,
    CONF_PORT2,
    CONF_BAUDRATE,
    CONF_RTS_TOGGLE,
    CONF_SCAN_ON_STARTUP,
    CONF_GATEWAY_HOST,
    CONF_GATEWAY_PORT,
    CONF_CONNECTION_TYPE,
    CONN_TYPE_SERIAL,
    CONN_TYPE_TCP,
    CONN_TYPE_DEMO,
    SERVICE_DISCOVERY_BUS1,
    SERVICE_DISCOVERY_BUS2,
    SERVICE_DISCOVERY_ALL,
    SERVICE_SET_CHANNEL_CONFIG,
    SERVICE_SET_DEVICE_NAME,
    ATTR_BUS_ID,
    ATTR_ADDRESS,
    ATTR_CHANNEL,
    ATTR_DEVICE_CLASS,
    ATTR_POLARITY,
    ATTR_DEVICE_NAME,
    DEVICE_CLASS_INPUT_MAP,
    DEVICE_CLASS_OUTPUT_MAP,
    POLARITY_NO,
    POLARITY_NC,
    DEFAULT_BAUDRATE,
)
from .hub import VelolinkHub, VelolinkBusConfig
from .storage import VelolinkStorage

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.LIGHT,
    Platform.SENSOR,
    Platform.BUTTON,
]

# Service schemas
SERVICE_SET_CHANNEL_CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_BUS_ID): cv.string,
        vol.Required(ATTR_ADDRESS): cv.positive_int,
        vol.Required(ATTR_CHANNEL): cv.positive_int,
        vol.Optional(ATTR_DEVICE_CLASS): vol.In(
            list(DEVICE_CLASS_INPUT_MAP.keys()) + list(DEVICE_CLASS_OUTPUT_MAP.keys())
        ),
        vol.Optional(ATTR_POLARITY): vol.In([POLARITY_NO, POLARITY_NC]),
    }
)

SERVICE_SET_DEVICE_NAME_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_BUS_ID): cv.string,
        vol.Required(ATTR_ADDRESS): cv.positive_int,
        vol.Required(ATTR_DEVICE_NAME): cv.string,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Velolink from a config entry."""
    try:
        # pylint: disable=too-many-locals,too-many-statements
        connection_type = entry.data.get(CONF_CONNECTION_TYPE, CONN_TYPE_SERIAL)
        buses = {}

        if connection_type == CONN_TYPE_SERIAL:
            # Serial connection
            port1 = entry.data.get(CONF_PORT1)
            port2 = entry.data.get(CONF_PORT2)
            baudrate = entry.data.get(CONF_BAUDRATE, DEFAULT_BAUDRATE)
            rts_toggle = entry.data.get(CONF_RTS_TOGGLE, False)

            if port1:
                buses["bus1"] = VelolinkBusConfig(
                    port=port1,
                    baudrate=baudrate,
                    rts_toggle=rts_toggle,
                    name="Rozdzielnica",
                    transport="serial",
                )

            if port2:
                buses["bus2"] = VelolinkBusConfig(
                    port=port2,
                    baudrate=baudrate,
                    rts_toggle=rts_toggle,
                    name="Dom",
                    transport="serial",
                )

        elif connection_type == CONN_TYPE_TCP:
            # TCP connection (VeloGateway)
            host = entry.data.get(CONF_GATEWAY_HOST)
            port = entry.data.get(CONF_GATEWAY_PORT, 5485)

            buses["bus1"] = VelolinkBusConfig(
                host=host,
                tcp_port=port,
                name="VeloGateway Bus1",
                transport="tcp",
            )
            buses["bus2"] = VelolinkBusConfig(
                host=host,
                tcp_port=port,
                name="VeloGateway Bus2",
                transport="tcp",
            )

        elif connection_type == CONN_TYPE_DEMO:
            # Demo connection
            buses["bus1"] = VelolinkBusConfig(
                name="Demo Bus 1",
                transport="demo",
            )
            buses["bus2"] = VelolinkBusConfig(
                name="Demo Bus 2",
                transport="demo",
            )

        if not buses:
            _LOGGER.error("No buses configured for Velolink")
            return False

        # Initialize storage
        storage = VelolinkStorage(hass)
        await storage.async_load()

        # Initialize hub
        hub = VelolinkHub(hass, entry.entry_id, buses)

        scan_on_startup = entry.data.get(CONF_SCAN_ON_STARTUP, True)
        await hub.async_start(scan_on_startup=scan_on_startup)

        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = hub
        hass.data[DOMAIN][f"{entry.entry_id}_storage"] = storage

        # Setup platforms
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

        # Register services
        async def handle_discovery_bus1(_call: ServiceCall) -> None:
            """Handle discovery for bus1."""
            await hub.async_discovery_bus("bus1")

        async def handle_discovery_bus2(_call: ServiceCall) -> None:
            """Handle discovery for bus2."""
            await hub.async_discovery_bus("bus2")

        async def handle_discovery_all(_call: ServiceCall) -> None:
            """Handle discovery for all buses."""
            await hub.async_discovery_all()

        async def handle_set_channel_config(call: ServiceCall) -> None:
            """Handle set channel config service."""
            bus_id = call.data[ATTR_BUS_ID]
            addr = call.data[ATTR_ADDRESS]
            ch = call.data[ATTR_CHANNEL]
            device_class = call.data.get(ATTR_DEVICE_CLASS)
            polarity = call.data.get(ATTR_POLARITY)

            # Determine channel type (simplified)
            ch_type = "in"

            await storage.async_set_channel_config(
                bus_id, addr, ch_type, ch, device_class, polarity
            )

            # Fire event to update entities
            hass.bus.async_fire(
                f"{DOMAIN}_config_updated",
                {"bus_id": bus_id, "address": addr, "channel": ch},
            )

        async def handle_set_device_name(call: ServiceCall) -> None:
            """Handle set device name service."""
            bus_id = call.data[ATTR_BUS_ID]
            addr = call.data[ATTR_ADDRESS]
            name = call.data[ATTR_DEVICE_NAME]

            await storage.async_set_device_name(bus_id, addr, name)

        # Register all services
        hass.services.async_register(DOMAIN, SERVICE_DISCOVERY_BUS1, handle_discovery_bus1)
        hass.services.async_register(DOMAIN, SERVICE_DISCOVERY_BUS2, handle_discovery_bus2)
        hass.services.async_register(DOMAIN, SERVICE_DISCOVERY_ALL, handle_discovery_all)
        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_CHANNEL_CONFIG,
            handle_set_channel_config,
            schema=SERVICE_SET_CHANNEL_CONFIG_SCHEMA,
        )
        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_DEVICE_NAME,
            handle_set_device_name,
            schema=SERVICE_SET_DEVICE_NAME_SCHEMA,
        )

        entry.async_on_unload(entry.add_update_listener(_options_updated))
        return True

    except Exception as ex:  # pylint: disable=broad-except
        _LOGGER.exception("Unexpected exception during Velolink setup: %s", ex)
        return False


async def _options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    hub: VelolinkHub = hass.data[DOMAIN].pop(entry.entry_id)
    hass.data[DOMAIN].pop(f"{entry.entry_id}_storage")

    await hub.async_stop()

    # Remove services if this was the last instance
    if not hass.data[DOMAIN]:
        hass.services.async_remove(DOMAIN, SERVICE_DISCOVERY_BUS1)
        hass.services.async_remove(DOMAIN, SERVICE_DISCOVERY_BUS2)
        hass.services.async_remove(DOMAIN, SERVICE_DISCOVERY_ALL)
        hass.services.async_remove(DOMAIN, SERVICE_SET_CHANNEL_CONFIG)
        hass.services.async_remove(DOMAIN, SERVICE_SET_DEVICE_NAME)

    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)