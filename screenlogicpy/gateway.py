"""Describes a ScreenLogicGateway class for interacting with a Pentair ScreenLogic system."""
import asyncio
import logging
from typing import Awaitable, Callable

from .client import ClientManager
from .const.common import (
    DATA_REQUEST,
    RANGE,
    ScreenLogicError,
    ScreenLogicRequestError,
)
from .const.msg import COM_MAX_RETRIES
from .device_const.chemistry import RANGE_PH_SETPOINT, RANGE_ORP_SETPOINT
from .device_const.system import BODY_TYPE, EQUIPMENT_FLAG
from .device_const.scg import LIMIT_FOR_BODY
from .const.data import ATTR, DEVICE, GROUP, VALUE
from .requests import (
    async_connect_to_gateway,
    async_request_gateway_version,
    async_request_pool_button_press,
    async_request_pool_config,
    async_request_pool_lights_command,
    async_request_pool_status,
    async_request_pump_status,
    async_request_set_heat_mode,
    async_request_set_heat_setpoint,
    async_request_chemistry,
    async_request_scg_config,
    async_request_set_scg_config,
    async_request_set_chem_data,
    async_make_request,
)
from .requests.protocol import ScreenLogicProtocol
from .requests.utility import getTemperatureUnit


_LOGGER = logging.getLogger(__name__)


class ScreenLogicGateway:
    """Class for interacting and communicating with a ScreenLogic protocol adapter."""

    def __init__(self, client_id: int = None, max_retries: int = None):
        self._ip = None
        self._port = 80
        self._type = 0
        self._subtype = 0
        self._name = "Unnamed-Screenlogic-Gateway"
        self._mac = ""
        self._version = ""
        self._transport: asyncio.Transport = None
        self._protocol: ScreenLogicProtocol = None
        self._is_client = False
        self._data = {}
        self._last = {}
        self.set_max_retries(
            max_retries
        ) if max_retries is not None else self.set_max_retries()
        self._client_manager = ClientManager(self._async_connected_request, client_id)

    @property
    def ip(self) -> str:
        return self._ip

    @property
    def port(self) -> int:
        return self._port

    @property
    def name(self) -> str:
        return self._name

    @property
    def mac(self) -> str:
        return self._mac

    @property
    def version(self) -> str:
        return self.get_value(DEVICE.ADAPTER, VALUE.FIRMWARE)

    @property
    def controller_model(self) -> str:
        return self.get_value(DEVICE.CONTROLLER, VALUE.MODEL)

    @property
    def equipment_flags(self) -> EQUIPMENT_FLAG:
        return EQUIPMENT_FLAG(
            self.get_data(DEVICE.CONTROLLER, GROUP.EQUIPMENT, VALUE.FLAGS)
        )

    @property
    def temperature_unit(self) -> str:
        return getTemperatureUnit(self._data)

    @property
    def is_connected(self) -> bool:
        return self._protocol._connected if self._protocol else False

    @property
    def is_client(self) -> bool:
        return self._client_manager.is_client

    @property
    def client_id(self) -> int:
        return self._client_manager.client_id

    @property
    def max_retries(self) -> int:
        return self._max_retries

    async def async_connect(
        self,
        ip=None,
        port=None,
        gtype=None,
        gsubtype=None,
        name=None,
        connection_closed_callback: Callable = None,
    ) -> bool:
        """Connect to the ScreenLogic protocol adapter"""
        if self.is_connected:
            return True

        self._ip = ip if ip is not None else self._ip
        self._port = port if port is not None else self._port
        self._type = gtype if gtype is not None else self._type
        self._subtype = gsubtype if gsubtype is not None else self._subtype
        self._name = name if name is not None else self._name
        self._custom_connection_closed_callback = connection_closed_callback

        if not self._ip:
            raise ScreenLogicError(
                "Attempted to connect when no IP address has been provided for connection."
            )

        _LOGGER.debug("Beginning connection and login sequence")
        connectPkg = await async_connect_to_gateway(
            self._ip,
            self._port,
            self._common_connection_closed_callback,
            self._max_retries,
        )
        if connectPkg:
            self._transport, self._protocol, self._mac = connectPkg
            await async_request_gateway_version(
                self._protocol, self._data, self._max_retries
            )
            if self.version:
                _LOGGER.debug("Login successful")
                await self.async_get_config()
                await self._client_manager.attach(
                    self._protocol, self.get_data(), self._max_retries
                )
                return True
        _LOGGER.debug("Login failed")
        return False

    async def async_disconnect(self, force=False):
        """Shutdown the connection to the ScreenLogic protocol adapter"""
        _LOGGER.debug("Disconnecting from protocol adapter")
        if self.is_client:
            await self._client_manager.async_unsubscribe_gateway()

        await self._protocol.async_close(force)

    async def async_update(self) -> bool:
        """
        Update all ScreenLogic data.

        Try to reconnect to the ScreenLogic protocol adapter if needed.
        """
        if not await self.async_connect() or not self._data:
            return False

        _LOGGER.debug("Beginning update of all data")
        await self.async_get_status()
        await self.async_get_pumps()
        await self.async_get_chemistry()
        await self.async_get_scg()
        _LOGGER.debug("Update complete")
        return True

    async def async_get_config(self):
        """Request pool configuration data."""
        _LOGGER.debug("Requesting config data")
        if last_raw := await self._async_connected_request(
            async_request_pool_config, self._data, reconnect_delay=1
        ):
            self._last[DATA_REQUEST.CONFIG] = last_raw

    async def async_get_status(self):
        """Request pool state data."""
        _LOGGER.debug("Requesting pool status")
        if last_raw := await self._async_connected_request(
            async_request_pool_status, self._data, reconnect_delay=1
        ):
            self._last[DATA_REQUEST.STATUS] = last_raw

    async def async_get_pumps(self):
        """Request all pump state data."""
        for pumpID in self._data[DEVICE.PUMP]:
            if self._data[DEVICE.PUMP][pumpID][VALUE.DATA] != 0:
                _LOGGER.debug("Requesting pump %i data", pumpID)
                last_pumps = self._last.setdefault(DATA_REQUEST.PUMPS, {})
                if last_raw := await self._async_connected_request(
                    async_request_pump_status, self._data, pumpID, reconnect_delay=1
                ):
                    last_pumps[pumpID] = last_raw

    async def async_get_chemistry(self):
        """Request IntelliChem controller data."""
        _LOGGER.debug("Requesting chemistry data")
        if last_raw := await self._async_connected_request(
            async_request_chemistry, self._data, reconnect_delay=1
        ):
            self._last[DATA_REQUEST.CHEMISTRY] = last_raw

    async def async_get_scg(self):
        """Request salt chlorine generator state data."""
        _LOGGER.debug("Requesting scg data")
        if last_raw := await self._async_connected_request(
            async_request_scg_config, self._data, reconnect_delay=1
        ):
            self._last[DATA_REQUEST.SCG] = last_raw

    # def get_data(self) -> dict:
    #    """Return the data."""
    #    return self._data

    def get_data(self, *keypath, strict: bool = False):
        """
        Return a data value from a key path.

        Returns the value of the key at the end of the keypath. Returns None if any key along the path is not found, or
        raises a KeyError if 'strict' == True.
        Returns the entire data dict if no 'keypath' is specified.
        """

        if not keypath:
            return self._data

        next = self._data

        def get_next(key):
            if current is None:
                return None
            if isinstance(current, dict):
                return current.get(key)
            if isinstance(current, list) and key in range(len(current)):
                return current[key]
            return None

        for key in keypath:
            current = next
            next = get_next(key)
            if next is None:
                if strict:
                    raise KeyError(f"'{key}' not found in '{keypath}'")
                break
        return next

    def get_value(self, *keypath, strict: bool = False):
        """
        Returns the 'value' key of the dict at the end of the key path.

        Shortcut to 'get_data(*keypath, "value")'.
        """
        data = self.get_data(*keypath, strict=strict)
        if isinstance(data, dict) and (val := data.get(ATTR.VALUE)) is not None:
            return val
        else:
            if strict:
                raise KeyError(f"Value for {keypath} not found")
            return None

    def get_name(self, *keypath, strict: bool = False):
        """
        Returns the 'name' key of the dict at the end of the key path.

        Shortcut to 'get_data(*keypath, "name")'.
        """
        data = self.get_data(*keypath, strict=strict)
        if isinstance(data, dict) and (val := data.get(ATTR.NAME)) is not None:
            return val
        else:
            if strict:
                raise KeyError(f"Value for {keypath} not found")
            return None

    def get_debug(self) -> dict:
        """Return the debug last-received data."""
        return self._last

    def set_max_retries(self, max_retries: int = COM_MAX_RETRIES) -> None:
        if 0 < max_retries < 6:
            self._max_retries = max_retries
        else:
            raise ValueError(f"Invalid max_retries: {max_retries}")

    async def async_set_circuit(self, circuitID: int, circuitState: int):
        """Set the circuit state for the specified circuit."""
        if not self._is_valid_circuit(circuitID):
            raise ValueError(f"Invalid circuitID: {circuitID}")
        if not self._is_valid_circuit_state(circuitState):
            raise ValueError(f"Invalid circuitState: {circuitState}")

        return await self._async_connected_request(
            async_request_pool_button_press, circuitID, circuitState
        )

    async def async_set_heat_temp(self, body: int, temp: int):
        """Set the target temperature for the specified body."""
        if not self._is_valid_body(body):
            raise ValueError(f"Invalid body: {body}")
        if not self._is_valid_heattemp(body, temp):
            raise ValueError(f"Invalid temp ({temp}) for body ({body})")

        return await self._async_connected_request(
            async_request_set_heat_setpoint, body, temp
        )

    async def async_set_heat_mode(self, body: int, mode: int):
        """Set the heating mode for the specified body."""
        if not self._is_valid_body(body):
            raise ValueError(f"Invalid body: {body}")
        if not self._is_valid_heatmode(mode):
            raise ValueError(f"Invalid mode: {mode}")

        return await self._async_connected_request(
            async_request_set_heat_mode, body, mode
        )

    async def async_set_color_lights(self, light_command: int):
        """Set the light show mode for all capable lights."""
        if not self._is_valid_color_mode(light_command):
            raise ValueError(f"Invalid light_command: {light_command}")

        return await self._async_connected_request(
            async_request_pool_lights_command, light_command
        )

    async def async_set_scg_config(self, pool_output: int, spa_output: int):
        """Set the salt-chlorine-generator output for both pool and spa."""
        if not self._is_valid_scg_value(pool_output, BODY_TYPE.POOL):
            raise ValueError(f"Invalid pool_output: {pool_output}")
        if not self._is_valid_scg_value(spa_output, BODY_TYPE.SPA):
            raise ValueError(f"Invalid spa_output: {spa_output}")

        return await self._async_connected_request(
            async_request_set_scg_config, pool_output, spa_output
        )

    async def async_set_chem_data(
        self,
        ph_setpoint: float,
        orp_setpoint: int,
        calcium: int,
        alkalinity: int,
        cyanuric: int,
        salt: int,
    ):
        """Set configurable chemistry values."""
        if self._is_valid_ph_setpoint(ph_setpoint):
            ph_setpoint = int(ph_setpoint * 100)
        else:
            raise ValueError(f"Invalid PH Set point: {ph_setpoint}")
        if not self._is_valid_orp_setpoint(orp_setpoint):
            raise ValueError(f"Invalid ORP Set point: {orp_setpoint}")
        if calcium < 0 or alkalinity < 0 or cyanuric < 0 or salt < 0:
            raise ValueError("Invalid Chemistry setting.")

        return await self._async_connected_request(
            async_request_set_chem_data,
            ph_setpoint,
            orp_setpoint,
            calcium,
            alkalinity,
            cyanuric,
            salt,
        )

    async def async_subscribe_client(
        self, callback: Callable[..., any], code: int
    ) -> Callable:
        """
        Subscribe client listener to message code.

        Subscribe to push messaging from the ScreenLogic protocol adapter and register a
        callback method to call when a message with the specified message code is received.

        Messages with known codes will be processed to update gateway data before
        callback method is called.
        """
        return await self._client_manager.async_subscribe(callback, code)

    def register_async_message_handler(
        self, message_code: int, handler: Callable[[bytes, any], Awaitable[None]], *argv
    ):
        """
        Register handler for message code.

        Registers an async function to call when a message with the specified message_code is received.
        Only one handler can be registered per message_code. Subsequent registrations will override
        the previous registration.
        """
        if not self._protocol:
            raise ScreenLogicError(
                "Not connected to ScreenLogic gateway. Must connect to gateway before registering handler."
            )
        self._protocol.register_async_message_callback(message_code, handler, *argv)

    def remove_async_message_handler(self, message_code: int):
        """Remove handler for message code."""
        if self._protocol:
            self._protocol.remove_async_message_callback(message_code)

    async def async_send_message(self, message_code: int, message: bytes = b""):
        """Send a message to the ScreenLogic protocol adapter."""
        _LOGGER.debug(f"User requesting {message_code}")
        return await self._async_connected_request(
            async_make_request, message_code, message
        )

    async def _async_connected_request(
        self, async_method, *args, reconnect_delay: int = 0, **kwargs
    ):
        """
        Ensure a connection to the ScreenLogic protocol adapter prior to sending the request.

        Will attempt to reconnect once if the connected request fails.
        """
        if kwargs.get("max_retries") is None:
            kwargs["max_retries"] = self._max_retries

        async def attempt_request():
            if await self.async_connect():
                return await async_method(self._protocol, *args, **kwargs)

            raise ScreenLogicError(
                f"Not connected and unable to connect to protocol adapter to complete request: {async_method.func_name}"
            )

        try:
            return await attempt_request()
        except ScreenLogicRequestError as re:
            _LOGGER.debug("%s. Attempting to reconnect", re.msg)
            await self.async_disconnect(True)
            await asyncio.sleep(reconnect_delay)
            try:
                return await attempt_request()
            except ScreenLogicRequestError as re2:
                raise ScreenLogicError(re2.msg) from re2

    def _common_connection_closed_callback(self):
        """Perform any needed cleanup."""
        if self._custom_connection_closed_callback:
            self._custom_connection_closed_callback()

    def _is_valid_circuit(self, circuit):
        """Validate circuit number."""
        return circuit in self._data[DEVICE.CIRCUIT]

    def _is_valid_circuit_state(self, state):
        """Validate circuit state number."""
        return state == 0 or state == 1

    def _is_valid_body(self, body):
        """Validate body of water number."""
        return body in self._data[DEVICE.BODY]

    def _is_valid_heatmode(self, heatmode):
        """Validate heat mode number."""
        return 0 <= heatmode < 5

    def _is_valid_heattemp(self, body, temp):
        """Validate heat tem for body."""
        min_temp = self.get_data(DEVICE.BODY, int(body), ATTR.MIN_SETPOINT)
        max_temp = self.get_data(DEVICE.BODY, int(body), ATTR.MAX_SETPOINT)
        return min_temp <= temp <= max_temp

    def _is_valid_color_mode(self, mode):
        """Validate color mode number."""
        return 0 <= mode <= 21

    def _is_valid_scg_value(self, scg_value, body_type):
        """Validate chlorinator value for body."""
        return 0 <= scg_value <= LIMIT_FOR_BODY[body_type]

    def _is_valid_ph_setpoint(self, ph_setpoint: float):
        """Validate pH setpoint."""
        return (
            RANGE_PH_SETPOINT[RANGE.MIN] <= ph_setpoint <= RANGE_PH_SETPOINT[RANGE.MAX]
        )

    def _is_valid_orp_setpoint(self, orp_setpoint: int):
        """Validate ORP setpoint."""
        return (
            RANGE_ORP_SETPOINT[RANGE.MIN]
            <= orp_setpoint
            <= RANGE_ORP_SETPOINT[RANGE.MAX]
        )
