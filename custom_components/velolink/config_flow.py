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

# Stałe dla nowego wyboru
CONN_CHOICE_RPI_HAT = "rpi_hat"
CONN_CHOICE_USB = "usb"
CONN_CHOICE_TCP = "tcp"


def _list_serial_ports() -> dict[str, str]:
    """List and categorize available serial ports."""
    # pylint: disable=import-outside-toplevel,import-error
    ports = {}
    try:
        from serial.tools import list_ports

        for port in list_ports.comports():
            device_path = port.device
            description = f"{port.description} ({device_path})"
            if "ttyAMA" in device_path or "serial" in device_path:
                # To prawdopodobnie RPi HAT
                ports[device_path] = f"Raspberry Pi HAT ({device_path})"
            else:
                # To prawdopodobnie adapter USB
                ports[device_path] = description
    except Exception:  # pylint: disable=broad-exception-caught
        # Fallback dla środowisk bez pyserial
        ports["/dev/ttyAMA0"] = "Raspberry Pi HAT (/dev/ttyAMA0)"
        ports["/dev/ttyUSB0"] = "USB Adapter (/dev/ttyUSB0)"
    return ports


class VelolinkConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle config flow for Velolink."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""
        self._connection_type: str | None = None

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step where the user chooses the connection type."""
        if user_input is not None:
            self._connection_type = user_input["connection_choice"]
            if self._connection_type == CONN_CHOICE_RPI_HAT:
                return await self.async_step_serial_hat()
            if self._connection_type == CONN_CHOICE_USB:
                return await self.async_step_serial_usb()
            if self._connection_type == CONN_CHOICE_TCP:
                return await self.async_step_tcp()

        # Sprawdź, czy są porty charakterystyczne dla RPi HAT
        all_ports = await self.hass.async_add_executor_job(_list_serial_ports)
        has_rpi_hat_port = any("ttyAMA" in p or "serial" in p for p in all_ports)

        options = {CONN_CHOICE_TCP: "TCP (VeloGateway)"}
        if has_rpi_hat_port:
            options[CONN_CHOICE_RPI_HAT] = "Raspberry Pi HAT"

        # Zawsze pokazuj opcję USB, jeśli są jakiekolwiek porty
        if all_ports:
            options[CONN_CHOICE_USB] = "Adapter USB-RS485"

        schema = vol.Schema({vol.Required("connection_choice"): vol.In(options)})

        return self.async_show_form(step_id="user", data_schema=schema)

    async def _create_serial_entry(
        self, user_input: dict[str, Any], title: str
    ) -> FlowResult:
        """Helper to create a serial connection entry."""
        if user_input.get(CONF_PORT2) == "":
            user_input.pop(CONF_PORT2, None)

        port1 = user_input.get(CONF_PORT1)
        port2 = user_input.get(CONF_PORT2)

        if port2 and port1 == port2:
            return self.async_show_form(
                step_id="serial_usb",  # lub serial_hat
                data_schema=self.data_schema,
                errors={"base": "ports_identical"},
            )

        user_input[CONF_CONNECTION_TYPE] = CONN_TYPE_SERIAL
        uid = f"serial-{port1}-{port2 or ''}"
        await self.async_set_unique_id(uid)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(title=title, data=user_input)

    async def async_step_serial_hat(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle RPi HAT serial connection setup."""
        all_ports = await self.hass.async_add_executor_job(_list_serial_ports)
        hat_ports = {
            p: d for p, d in all_ports.items() if "ttyAMA" in p or "serial" in p
        }

        if not hat_ports:
            return self.async_abort(reason="no_hat_ports_found")

        if user_input is not None:
            user_input[CONF_PORT1] = hat_ports.popitem()[
                0
            ]  # Zawsze bierz pierwszy znaleziony port HAT
            return await self._create_serial_entry(user_input, "Velolink RPi HAT")

        # Dla HAT nie pytamy o port, zakładamy że jest jeden
        schema = vol.Schema(
            {
                vol.Required(CONF_BAUDRATE, default=DEFAULT_BAUDRATE): cv.positive_int,
                vol.Required(CONF_RTS_TOGGLE, default=DEFAULT_RTS_TOGGLE): bool,
                vol.Required(
                    CONF_SCAN_ON_STARTUP, default=DEFAULT_SCAN_ON_STARTUP
                ): bool,
            }
        )

        return self.async_show_form(step_id="serial_hat", data_schema=schema)

    async def async_step_serial_usb(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle USB adapter serial connection setup."""
        all_ports = await self.hass.async_add_executor_job(_list_serial_ports)
        usb_ports = {
            p: d for p, d in all_ports.items() if "ttyUSB" in p or "ttyACM" in p
        }

        if not usb_ports:
            return self.async_abort(reason="no_usb_ports_found")

        if user_input is not None:
            return await self._create_serial_entry(
                user_input, f"Velolink USB ({user_input[CONF_PORT1]})"
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_PORT1): vol.In(usb_ports),
                vol.Optional(CONF_PORT2): vol.In({"": "(brak)"} | usb_ports),
                vol.Required(CONF_BAUDRATE, default=DEFAULT_BAUDRATE): cv.positive_int,
                vol.Required(CONF_RTS_TOGGLE, default=DEFAULT_RTS_TOGGLE): bool,
                vol.Required(
                    CONF_SCAN_ON_STARTUP, default=DEFAULT_SCAN_ON_STARTUP
                ): bool,
            }
        )

        return self.async_show_form(step_id="serial_usb", data_schema=schema)

    async def async_step_tcp(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle TCP connection setup."""
        if user_input is not None:
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

        return self.async_show_form(step_id="tcp", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get options flow handler."""
        return VelolinkOptionsFlow(config_entry)


# ... reszta pliku (VelolinkOptionsFlow) pozostaje bez zmian ...
