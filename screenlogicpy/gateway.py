"""Describes a ScreenLogicGateway class for interacting with a Pentair ScreenLogic system."""
import asyncio
import logging
from typing import Awaitable, Callable

from .client import ClientManager
from .const import (
    BODY_TYPE,
    CIRCUIT_FUNCTION,
    DATA,
    MESSAGE,
    RANGE,
    SCG,
    ScreenLogicError,
    ScreenLogicRequestError,
)
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
from .validation import (
    DataValidation,
    DataValidationKey as dv_key,
)


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
        self.dv = DataValidation()
        client_id = client_id if self.dv.is_valid(dv_key.CLIENT_ID, client_id) else None
        self._client_manager = ClientManager(self._async_connected_request, client_id)
        self.set_max_retries(
            max_retries
        ) if max_retries is not None else self.set_max_retries()

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
        return self._version

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
            self._version = await async_request_gateway_version(
                self._protocol, self._max_retries
            )
            if self._version:
                _LOGGER.debug("Login successful")
                await self.async_get_config()
                await self._client_manager.attach(
                    self._protocol, self.get_data(), self._max_retries
                )
                self._add_local_limits()
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
            self._last[DATA.KEY_CONFIG] = last_raw

    async def async_get_status(self):
        """Request pool state data."""
        _LOGGER.debug("Requesting pool status")
        if last_raw := await self._async_connected_request(
            async_request_pool_status, self._data, reconnect_delay=1
        ):
            self._last["status"] = last_raw

    async def async_get_pumps(self):
        """Request all pump state data."""
        for pumpID in self._data[DATA.KEY_PUMPS]:
            if self._data[DATA.KEY_PUMPS][pumpID]["data"] != 0:
                _LOGGER.debug("Requesting pump %i data", pumpID)
                last_pumps = self._last.setdefault(DATA.KEY_PUMPS, {})
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
            self._last[DATA.KEY_CHEMISTRY] = last_raw

    async def async_get_scg(self):
        """Request salt chlorine generator state data."""
        _LOGGER.debug("Requesting scg data")
        if last_raw := await self._async_connected_request(
            async_request_scg_config, self._data, reconnect_delay=1
        ):
            self._last[DATA.KEY_SCG] = last_raw

    def get_data(self) -> dict:
        """Return the data."""
        return self._data

    def get_debug(self) -> dict:
        """Return the debug last-received data."""
        return self._last

    def set_max_retries(self, max_retries: int = MESSAGE.COM_MAX_RETRIES) -> None:
        self.dv.validate(dv_key.MAX_RETRIES, max_retries)
        self._max_retries = max_retries

    async def async_set_circuit(self, circuitID: int, circuitState: int):
        """Set the circuit state for the specified circuit."""
        self.dv.validate(dv_key.CIRCUIT, circuitID)
        self.dv.validate(dv_key.ON_OFF, circuitState)

        return await self._async_connected_request(
            async_request_pool_button_press, circuitID, circuitState
        )

    async def async_set_heat_temp(self, body: int, temp: int):
        """Set the target temperature for the specified body."""
        self.dv.validate(dv_key.BODY, body)
        self.dv.validate((dv_key.HEAT_TEMP, body), temp)

        return await self._async_connected_request(
            async_request_set_heat_setpoint, body, temp
        )

    async def async_set_heat_mode(self, body: int, mode: int):
        """Set the heating mode for the specified body."""
        self.dv.validate(dv_key.BODY, body)
        self.dv.validate(dv_key.HEAT_MODE, mode)

        return await self._async_connected_request(
            async_request_set_heat_mode, body, mode
        )

    async def async_set_color_lights(self, light_command: int):
        """Set the light show mode for all capable lights."""
        self.dv.validate(dv_key.COLOR_MODE, light_command)

        return await self._async_connected_request(
            async_request_pool_lights_command, light_command
        )

    async def async_set_scg_config(
        self,
        *,
        pool_output: int = None,
        spa_output: int = None,
        super_chlor: int = None,
        super_time: int = None,
    ):
        """Set the salt-chlorine-generator output for both pool and spa."""
        if pool_output is None and spa_output is None:
            raise ScreenLogicValueRangeError("No SCG values to set")

        def current(k):
            return self._current_data_value(DATA.KEY_SCG, k)

        pool_output = current("scg_level1") if pool_output is None else pool_output
        spa_output = current("scg_level2") if spa_output is None else spa_output
        # TODO: Need to find state values for these
        super_chlor = 0 if super_chlor is None else super_chlor
        super_time = 1 if super_time is None else super_time

        self.dv.validate((dv_key.SCG_SETPOINT, BODY_TYPE.POOL), pool_output)
        self.dv.validate((dv_key.SCG_SETPOINT, BODY_TYPE.SPA), spa_output)
        self.dv.validate(dv_key.ON_OFF, super_chlor)
        self.dv.validate(dv_key.SC_RUNTIME, super_time)

        return await self._async_connected_request(
            async_request_set_scg_config,
            pool_output,
            spa_output,
            super_chlor,
            super_time,
        )

    async def async_set_chem_data(
        self,
        *,
        ph_setpoint: float = None,
        orp_setpoint: int = None,
        calcium_harness: int = None,
        total_alkalinity: int = None,
        cya: int = None,
        salt_tds_ppm: int = None,
    ):
        """Set configurable chemistry values."""
        if not (
            ph_setpoint
            or orp_setpoint
            or calcium_harness
            or total_alkalinity
            or cya
            or salt_tds_ppm
        ):
            raise ScreenLogicValueRangeError("No Chemistry values to set")

        def current(k):
            return self._current_data_value(DATA.KEY_CHEMISTRY, k)

        ph_setpoint = current("ph_setpoint") if ph_setpoint is None else ph_setpoint
        orp_setpoint = current("orp_setpoint") if orp_setpoint is None else orp_setpoint
        calcium_harness = (
            current("calcium_harness") if calcium_harness is None else calcium_harness
        )
        total_alkalinity = (
            current("total_alkalinity")
            if total_alkalinity is None
            else total_alkalinity
        )
        cya = current("cya") if cya is None else cya
        salt_tds_ppm = current("salt_tds_ppm") if salt_tds_ppm is None else salt_tds_ppm

        if not (
            ph_setpoint is not None
            and orp_setpoint is not None
            and calcium_harness is not None
            and total_alkalinity is not None
            and cya is not None
            and salt_tds_ppm is not None
        ):
            raise ScreenLogicKeyError(
                "Unable to reference existing omitted chemistry values."
            )

        self.dv.validate(dv_key.PH_SETPOINT, ph_setpoint)
        ph_setpoint = int(ph_setpoint * 100)
        self.dv.validate(dv_key.ORP_SETPOINT, orp_setpoint)
        self.dv.validate(dv_key.CALCIUM_HARDNESS, calcium_harness)
        self.dv.validate(dv_key.TOTAL_ALKALINITY, total_alkalinity)
        self.dv.validate(dv_key.CYANURIC_ACID, cya)
        self.dv.validate(dv_key.SALT_TDS, salt_tds_ppm)

        return await self._async_connected_request(
            async_request_set_chem_data,
            ph_setpoint,
            orp_setpoint,
            calcium_harness,
            total_alkalinity,
            cya,
            salt_tds_ppm,
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

    def _add_local_limits(self):
        self.dv.update(dv_key.CIRCUIT, set(self._data[DATA.KEY_CIRCUITS].keys()))
        self.dv.update(dv_key.BODY, set(self._data[DATA.KEY_BODIES].keys()))
        (
            self.dv.update(
                (dv_key.HEAT_TEMP, body),
                (
                    body_data["min_set_point"]["value"],
                    body_data["max_set_point"]["value"],
                ),
            )
            for body, body_data in self._data[DATA.KEY_BODIES].items()
        )

    # Promote?
    def _has_color_lights(self):
        """Return if any configured lights support color modes."""
        if circuits := self._data.get(DATA.KEY_CIRCUITS, None):
            for circuit in circuits.values():
                if circuit["function"] in CIRCUIT_FUNCTION.GROUP_LIGHTS_COLOR:
                    return True
        return False

    def _current_data_value(self, sec_key: str, val_key: str):
        """Return current data value."""
        if section := self._data.get(sec_key):
            if sensor := section.get(val_key):
                return sensor.get("value")
        return None
