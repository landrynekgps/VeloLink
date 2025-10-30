"""Config flow for Velolink."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

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
    DEFAULT_BAUDRATE,
    DEFAULT_RTS_TOGGLE,
    DEFAULT_SCAN_ON_STARTUP,
    DEFAULT_GATEWAY_PORT,
    DEVICE_CLASS_INPUT_MAP,
    DEVICE_CLASS_OUTPUT_MAP,
    POLARITY_NO,
    POLARITY_NC,
)

_LOGGER = logging.getLogger(__name__)


def _list_serial_ports() -> list[str]:
    """List available serial ports."""
    # pylint: disable=import-outside-toplevel,import-error
    try:
        from serial.tools import list_ports

        return [p.device for p in list_ports.comports()]
    except Exception:  # pylint: disable=broad-exception-caught
        return ["/dev/ttyAMA0", "/dev/ttyUSB0", "/dev/ttyUSB1"]


class VelolinkConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle config flow for Velolink."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""
        self._connection_type: str | None = None
        self._data: Dict[str, Any] = {}

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle initial step."""
        if user_input is not None:
            self._connection_type = user_input[CONF_CONNECTION_TYPE]

            if self._connection_type == CONN_TYPE_SERIAL:
                return await self.async_step_serial()

            if self._connection_type == CONN_TYPE_TCP:
                return await self.async_step_tcp()

        schema = vol.Schema(
            {
                vol.Required(CONF_CONNECTION_TYPE, default=CONN_TYPE_SERIAL): vol.In(
                    {
                        CONN_TYPE_SERIAL: "Serial (RPi HAT / USB)",
                        CONN_TYPE_TCP: "TCP (VeloGateway)",
                    }
                ),
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_serial(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle serial connection setup."""
        errors = {}
        ports = await self.hass.async_add_executor_job(_list_serial_ports)

        if user_input is not None:
            if user_input.get(CONF_PORT2) == "":
                user_input.pop(CONF_PORT2, None)

            port1 = user_input.get(CONF_PORT1)
            port2 = user_input.get(CONF_PORT2)

            if port2 and port1 == port2:
                errors["base"] = "ports_identical"

            if not errors:
                user_input[CONF_CONNECTION_TYPE] = CONN_TYPE_SERIAL
                uid = f"serial-{port1}-{port2 or ''}"
                await self.async_set_unique_id(uid)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"Velolink Serial ({port1})",
                    data=user_input,
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_PORT1): vol.In(ports if ports else ["/dev/ttyAMA0"]),
                vol.Optional(CONF_PORT2): vol.In([""] + ports),
                vol.Required(CONF_BAUDRATE, default=DEFAULT_BAUDRATE): cv.positive_int,
                vol.Required(CONF_RTS_TOGGLE, default=DEFAULT_RTS_TOGGLE): bool,
                vol.Required(
                    CONF_SCAN_ON_STARTUP, default=DEFAULT_SCAN_ON_STARTUP
                ): bool,
            }
        )

        return self.async_show_form(step_id="serial", data_schema=schema, errors=errors)

    async def async_step_tcp(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle TCP connection setup."""
        # pylint: disable=import-outside-toplevel
        errors = {}

        if user_input is not None:
            # Test connection
            try:
                import socket

                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                result = sock.connect_ex(
                    (user_input[CONF_GATEWAY_HOST], user_input[CONF_GATEWAY_PORT])
                )
                sock.close()

                if result != 0:
                    errors["base"] = "cannot_connect"
            except Exception as err:  # pylint: disable=broad-exception-caught
                _LOGGER.exception("TCP test failed: %s", err)
                errors["base"] = "cannot_connect"

            if not errors:
                user_input[CONF_CONNECTION_TYPE] = CONN_TYPE_TCP
                host = user_input[CONF_GATEWAY_HOST]
                port = user_input[CONF_GATEWAY_PORT]
                uid = f"tcp-{host}-{port}"
                await self.async_set_unique_id(uid)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"Velolink Gateway ({host})",
                    data=user_input,
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_GATEWAY_HOST): str,
                vol.Required(CONF_GATEWAY_PORT, default=DEFAULT_GATEWAY_PORT): cv.port,
                vol.Required(
                    CONF_SCAN_ON_STARTUP, default=DEFAULT_SCAN_ON_STARTUP
                ): bool,
            }
        )

        return self.async_show_form(step_id="tcp", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get options flow handler."""
        return VelolinkOptionsFlow(config_entry)


class VelolinkOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self._bus_id: str | None = None
        self._address: int | None = None
        self._channel: int | None = None
        self._ch_type: str | None = None

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle options initial step."""
        # pylint: disable=unused-argument
        return self.async_show_menu(
            step_id="init",
            menu_options=["edit_channel", "edit_device_name"],
        )

    async def async_step_edit_channel(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Select channel to edit."""
        # pylint: disable=import-outside-toplevel
        from .hub import VelolinkHub

        hub: VelolinkHub = self.hass.data[DOMAIN][self.config_entry.entry_id]

        channels = []
        # pylint: disable=protected-access
        for (bus_id, addr), node in hub._nodes.items():
            if node.kind in ["input", "veloswitch", "velomotion"]:
                for ch in range(node.channels):
                    channels.append(
                        f"{bus_id}:{addr}:in:{ch} " f"({node.model or node.kind})"
                    )
            elif node.kind == "output":
                for ch in range(node.channels):
                    channels.append(
                        f"{bus_id}:{addr}:out:{ch} " f"({node.model or node.kind})"
                    )

        if not channels:
            return self.async_abort(reason="no_channels")

        if user_input is not None:
            selected = user_input["channel"]
            parts = selected.split(" ")[0].split(":")
            self._bus_id = parts[0]
            self._address = int(parts[1])
            self._ch_type = parts[2]
            self._channel = int(parts[3])
            return await self.async_step_configure_channel()

        schema = vol.Schema(
            {
                vol.Required("channel"): vol.In(channels),
            }
        )

        return self.async_show_form(step_id="edit_channel", data_schema=schema)

    async def async_step_configure_channel(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Configure channel settings."""
        # pylint: disable=import-outside-toplevel
        from .storage import VelolinkStorage
        from .const import signal_channel_config_updated
        from homeassistant.helpers.dispatcher import async_dispatcher_send

        storage: VelolinkStorage = self.hass.data[DOMAIN][
            f"{self.config_entry.entry_id}_storage"
        ]

        if user_input is not None:
            await storage.async_set_channel_config(
                self._bus_id,
                self._address,
                self._ch_type,
                self._channel,
                device_class=user_input.get("device_class"),
                polarity=user_input.get("polarity"),
            )

            async_dispatcher_send(
                self.hass,
                signal_channel_config_updated(self.config_entry.entry_id),
                {
                    "bus_id": self._bus_id,
                    "address": self._address,
                    "channel": self._channel,
                },
            )

            return self.async_create_entry(title="", data={})

        current = storage.get_channel_config(
            self._bus_id, self._address, self._ch_type, self._channel
        )

        if self._ch_type == "in":
            dc_map = DEVICE_CLASS_INPUT_MAP
        else:
            dc_map = DEVICE_CLASS_OUTPUT_MAP

        schema = vol.Schema(
            {
                vol.Required(
                    "device_class", default=current.get("device_class", "none")
                ): vol.In(dc_map.keys()),
                vol.Required(
                    "polarity", default=current.get("polarity", POLARITY_NO)
                ): vol.In([POLARITY_NO, POLARITY_NC]),
            }
        )

        return self.async_show_form(
            step_id="configure_channel",
            data_schema=schema,
            description_placeholders={
                "bus_id": self._bus_id,
                "address": str(self._address),
                "channel": str(self._channel),
            },
        )

    async def async_step_edit_device_name(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Edit device name."""
        # pylint: disable=import-outside-toplevel
        from .hub import VelolinkHub
        from .storage import VelolinkStorage

        hub: VelolinkHub = self.hass.data[DOMAIN][self.config_entry.entry_id]
        storage: VelolinkStorage = self.hass.data[DOMAIN][
            f"{self.config_entry.entry_id}_storage"
        ]

        # pylint: disable=protected-access
        devices = [
            f"{bus_id}:{addr} ({node.model or node.kind})"
            for (bus_id, addr), node in hub._nodes.items()
        ]

        if not devices:
            return self.async_abort(reason="no_devices")

        if user_input is not None:
            selected = user_input["device"].split(" ")[0].split(":")
            bus_id, addr = selected[0], int(selected[1])

            await storage.async_set_device_name(bus_id, addr, user_input["name"])
            return self.async_create_entry(title="", data={})

        schema = vol.Schema(
            {
                vol.Required("device"): vol.In(devices),
                vol.Required("name"): str,
            }
        )

        return self.async_show_form(step_id="edit_device_name", data_schema=schema)
