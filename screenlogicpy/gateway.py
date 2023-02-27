"""Describes a ScreenLogicGateway class for interacting with a Pentair ScreenLogic system."""
import asyncio
import logging
from typing import Awaitable, Callable

from .client import ClientManager
from .const import (
    CIRCUIT_FUNCTION,
    DATA,
    MESSAGE,
    ScreenLogicError,
    ScreenLogicKeyError,
    ScreenLogicValueRangeError,
    ScreenLogicWarning,
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
    BoundsSet,
    BoundsRange,
    DATA_BOUNDS as DB,
    SETTINGS_BOUNDS as SB,
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
        self._client_manager = ClientManager(client_id)
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
            raise ScreenLogicError("IP address never provided for connection.")

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
        """Disconnect from the ScreenLogic protocol adapter"""
        if self.is_client:
            await self._client_manager.async_unsubscribe_gateway()

        if not force:
            while self._protocol.requests_pending():
                await asyncio.sleep(0)

        if self._transport and not self._transport.is_closing():
            self._transport.close()

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
        if not self.is_connected:
            raise ScreenLogicWarning(
                "Not connected to protocol adapter. get_config failed."
            )
        _LOGGER.debug("Requesting config data")
        self._last[DATA.KEY_CONFIG] = await async_request_pool_config(
            self._protocol, self._data, self._max_retries
        )

    async def async_get_status(self):
        """Request pool state data."""
        if not self.is_connected:
            raise ScreenLogicWarning(
                "Not connected to protocol adapter. get_status failed."
            )
        _LOGGER.debug("Requesting pool status")
        self._last["status"] = await async_request_pool_status(
            self._protocol, self._data, self._max_retries
        )

    async def async_get_pumps(self):
        """Request all pump state data."""
        if not self.is_connected:
            raise ScreenLogicWarning(
                "Not connected to protocol adapter. get_pumps failed."
            )
        for pumpID in self._data[DATA.KEY_PUMPS]:
            if self._data[DATA.KEY_PUMPS][pumpID]["data"] != 0:
                _LOGGER.debug("Requesting pump %i data", pumpID)
                last_pumps = self._last.setdefault(DATA.KEY_PUMPS, {})
                last_pumps[pumpID] = await async_request_pump_status(
                    self._protocol, self._data, pumpID, self._max_retries
                )

    async def async_get_chemistry(self):
        """Request IntelliChem controller data."""
        if not self.is_connected:
            raise ScreenLogicWarning(
                "Not connected to protocol adapter. get_chemistry failed."
            )
        _LOGGER.debug("Requesting chemistry data")
        self._last[DATA.KEY_CHEMISTRY] = await async_request_chemistry(
            self._protocol, self._data, self._max_retries
        )

    async def async_get_scg(self):
        """Request salt chlorine generator state data."""
        if not self.is_connected:
            raise ScreenLogicWarning(
                "Not connected to protocol adapter. get_scg failed."
            )
        _LOGGER.debug("Requesting scg data")
        self._last[DATA.KEY_SCG] = await async_request_scg_config(
            self._protocol, self._data, self._max_retries
        )

    def get_data(self) -> dict:
        """Return the data."""
        return self._data

    def get_debug(self) -> dict:
        """Return the debug last-received data."""
        return self._last

    def set_max_retries(self, max_retries: int = MESSAGE.COM_MAX_RETRIES) -> None:
        SB.MAX_RETRIES.validate(max_retries)
        self._max_retries = max_retries

    async def async_set_circuit(self, circuitID: int, circuitState: int):
        """Set the circuit state for the specified circuit."""
        DB.CIRCUIT.validate(circuitID)
        DB.ON_OFF.validate(circuitState)

        if await self.async_connect():
            if await async_request_pool_button_press(
                self._protocol, circuitID, circuitState, self._max_retries
            ):
                return True
        return False

    async def async_set_heat_temp(self, body: int, temp: int):
        """Set the target temperature for the specified body."""
        DB.BODY.validate(body)
        DB.HEAT_TEMP[body].validate(temp)

        if await self.async_connect():
            if await async_request_set_heat_setpoint(
                self._protocol, body, temp, self._max_retries
            ):
                return True
        return False

    async def async_set_heat_mode(self, body: int, mode: int):
        """Set the heating mode for the specified body."""
        DB.BODY.validate(body)
        DB.HEAT_MODE.validate(mode)

        if await self.async_connect():
            if await async_request_set_heat_mode(
                self._protocol, body, mode, self._max_retries
            ):
                return True
        return False

    async def async_set_color_lights(self, light_command: int):
        """Set the light show mode for all capable lights."""
        DB.COLOR_MODE.validate(light_command)

        if await self.async_connect():
            if await async_request_pool_lights_command(
                self._protocol, light_command, self._max_retries
            ):
                return True
        return False

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

        DB.SCG_SETPOINT_POOL.validate(pool_output)
        DB.SCG_SETPOINT_SPA.validate(spa_output)
        DB.ON_OFF.validate(super_chlor)
        DB.SC_RUNTIME.validate(super_time)

        if await self.async_connect():
            return await async_request_set_scg_config(
                self._protocol,
                pool_output,
                spa_output,
                super_chlor,
                super_time,
                self._max_retries,
            )
        return False

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

        DB.CHEM_SETPOINT_PH.validate(ph_setpoint)
        ph_setpoint = int(ph_setpoint * 100)
        DB.CHEM_SETPOINT_ORP.validate(orp_setpoint)
        DB.CHEM_CALCIUM_HARDNESS.validate(calcium_harness)
        DB.CHEM_TOTAL_ALKALINITY.validate(total_alkalinity)
        DB.CHEM_CYANURIC_ACID.validate(cya)
        DB.CHEM_SALT_TDS.validate(salt_tds_ppm)

        if await self.async_connect():
            return await async_request_set_chem_data(
                self._protocol,
                ph_setpoint,
                orp_setpoint,
                calcium_harness,
                total_alkalinity,
                cya,
                salt_tds_ppm,
                self._max_retries,
            )
        return False

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
        if not self.is_connected:
            raise ScreenLogicWarning(
                "Not connected to protocol adapter. send_message failed."
            )
        _LOGGER.debug(f"User requesting {message_code}")
        return await async_make_request(
            self._protocol, message_code, message, self._max_retries
        )

    def _common_connection_closed_callback(self):
        """Perform any needed cleanup."""
        # Future internal cleanup tasks
        if self._custom_connection_closed_callback:
            self._custom_connection_closed_callback()

    def _add_local_limits(self):
        DB.CIRCUIT = BoundsSet(self._data[DATA.KEY_CIRCUITS].keys())
        DB.BODY = BoundsSet(self._data[DATA.KEY_BODIES].keys())
        DB.HEAT_TEMP = {
            body: BoundsRange(
                body_data["min_set_point"]["value"],
                body_data["max_set_point"]["value"],
            )
            for body, body_data in self._data[DATA.KEY_BODIES].items()
        }

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
