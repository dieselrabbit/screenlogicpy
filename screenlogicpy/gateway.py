import asyncio
import logging
import time
from typing import Awaitable, Callable

from .const import (
    BODY_TYPE,
    CLIENT_MIN_COMM,
    CHEMISTRY,
    DATA,
    RANGE,
    CODE,
    SCG,
    ScreenLogicError,
    ScreenLogicWarning,
)
from .requests.client import async_request_add_client, async_request_remove_client

from .requests import (
    async_connect_to_gateway,
    async_request_gateway_version,
    async_request_ping,
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
from .requests.chemistry import decode_chemistry
from .requests.color import decode_color_update
from .requests.status import decode_pool_status
from .requests.protocol import ScreenLogicProtocol


_LOGGER = logging.getLogger(__name__)


class ScreenLogicGateway:
    """Class for interacting and communicating with a ScreenLogic protocol adapter."""

    def __init__(
        self, ip, port=80, gtype=0, gsubtype=0, name="Unnamed-Screenlogic-Gateway"
    ):
        self.__ip = ip
        self.__port = port
        self.__type = gtype
        self.__subtype = gsubtype
        self.__name = name
        self.__mac = ""
        self.__version = ""
        self.__transport: asyncio.Transport = None
        self.__protocol: ScreenLogicProtocol = None
        self.__is_client = False
        self.__client_desired = False
        self.__async_data_updated_callback = None
        self.__data = {}
        self.__last = {}

    @property
    def ip(self) -> str:
        return self.__ip

    @property
    def port(self) -> int:
        return self.__port

    @property
    def name(self) -> str:
        return self.__name

    @property
    def mac(self) -> str:
        return self.__mac

    @property
    def version(self) -> str:
        return self.__version

    @property
    def is_connected(self) -> bool:
        return self.__protocol.connected if self.__protocol else False

    @property
    def is_client(self) -> bool:
        return self.__is_client

    async def async_connect(self, connection_closed_callback: Callable = None) -> bool:
        """Connects to the ScreenLogic protocol adapter"""
        if self.is_connected:
            return True

        _LOGGER.debug("Beginning connection and login sequence")
        connectPkg = await async_connect_to_gateway(
            self.__ip, self.__port, connection_closed_callback
        )
        if connectPkg:
            self.__transport, self.__protocol, self.__mac = connectPkg
            self.__version = await async_request_gateway_version(self.__protocol)
            if self.__version:
                _LOGGER.debug("Login successful")
                await self._async_get_config()
                if not self.__is_client and self.__client_desired:
                    self.__is_client = await self._async_add_client()
                return True
        _LOGGER.debug("Login failed")
        return False

    async def async_disconnect(self, force=False):
        """Disconnects from the ScreenLogic protocol adapter"""
        if self.__is_client:
            self.__is_client = not await self._async_remove_client()

        if not force:
            while self.__protocol.requests_pending():
                await asyncio.sleep(1)

        if self.__transport and not self.__transport.is_closing():
            self.__transport.close()

    async def async_subscribe_client(
        self, async_data_updated_callback: Callable[..., Awaitable[None]] = None
    ) -> bool:
        self.__client_desired = True
        if await self._async_add_client():
            self.__is_client = True
            self.__async_data_updated_callback = async_data_updated_callback
            return await self._async_setup_push()
        else:
            return False

    async def async_unsubscribe_client(self) -> bool:
        self.__client_desired = False
        self.__is_client = False
        self.__async_data_updated_callback = None
        self.__protocol.remove_all_async_message_callbacks()
        return await self._async_remove_client()

    async def async_update(self) -> bool:
        """Updates all ScreenLogic data if already connected. Tries to connect if not."""
        if not await self.async_connect() or not self.__data:
            return False

        _LOGGER.debug("Beginning update of all data")
        await self._async_get_status()
        await self._async_get_pumps()
        await self._async_get_chemistry()
        await self._async_get_scg()
        await self.async_data_updated()
        _LOGGER.debug("Update complete")
        return True

    def get_data(self) -> dict:
        """Returns the data."""
        return self.__data

    def get_debug(self) -> dict:
        """Returns the debug last-received data."""
        return self.__last

    async def async_set_circuit(self, circuitID: int, circuitState: int):
        """Sets the circuit state for the specified circuit."""
        if not self._is_valid_circuit(circuitID):
            raise ValueError(f"Invalid circuitID: {circuitID}")
        if not self._is_valid_circuit_state(circuitState):
            raise ValueError(f"Invalid circuitState: {circuitState}")

        if await self.async_connect():
            if await async_request_pool_button_press(
                self.__protocol, circuitID, circuitState
            ):
                return True
        return False

    async def async_set_heat_temp(self, body: int, temp: int):
        """Sets the target temperature for the specified body."""
        if not self._is_valid_body(body):
            raise ValueError(f"Invalid body: {body}")
        if not self._is_valid_heattemp(body, temp):
            raise ValueError(f"Invalid temp ({temp}) for body ({body})")

        if await self.async_connect():
            if await async_request_set_heat_setpoint(self.__protocol, body, temp):
                return True
        return False

    async def async_set_heat_mode(self, body: int, mode: int):
        """Sets the heating mode for the specified body."""
        if not self._is_valid_body(body):
            raise ValueError(f"Invalid body: {body}")
        if not self._is_valid_heatmode(mode):
            raise ValueError(f"Invalid mode: {mode}")

        if await self.async_connect():
            if await async_request_set_heat_mode(self.__protocol, body, mode):
                return True
        return False

    async def async_set_color_lights(self, light_command: int):
        """Sets the light show mode for all capable lights."""
        if not self._is_valid_color_mode(light_command):
            raise ValueError(f"Invalid light_command: {light_command}")

        if await self.async_connect():
            if await async_request_pool_lights_command(self.__protocol, light_command):
                return True
        return False

    async def async_set_scg_config(self, pool_output: int, spa_output: int):
        """Sets the salt-chlorine-generator output for both pool and spa."""
        if not self._is_valid_scg_value(pool_output, BODY_TYPE.POOL):
            raise ValueError(f"Invalid pool_output: {pool_output}")
        if not self._is_valid_scg_value(spa_output, BODY_TYPE.SPA):
            raise ValueError(f"Invalid spa_output: {spa_output}")

        if await self.async_connect():
            if await async_request_set_scg_config(
                self.__protocol, pool_output, spa_output
            ):
                return True
        return False

    async def async_set_chem_data(
        self,
        ph_setpoint: float,
        orp_setpoint: int,
        calcium: int,
        alkalinity: int,
        cyanuric: int,
        salt: int,
    ):
        """Sets the setable chemistry values."""
        if self._is_valid_ph_setpoint(ph_setpoint):
            ph_setpoint = int(ph_setpoint * 100)
        else:
            raise ValueError(f"Invalid PH Set point: {ph_setpoint}")
        if not self._is_valid_orp_setpoint(orp_setpoint):
            raise ValueError(f"Invalid ORP Set point: {orp_setpoint}")
        if calcium < 0 or alkalinity < 0 or cyanuric < 0 or salt < 0:
            raise ValueError("Invalid Chemistry setting.")

        if await self.async_connect():
            if await async_request_set_chem_data(
                self.__protocol,
                ph_setpoint,
                orp_setpoint,
                calcium,
                alkalinity,
                cyanuric,
                salt,
            ):
                return True
        return False

    def register_message_handler(
        self, message_code: int, handler: Callable[[bytes, any], Awaitable[None]], *argv
    ):
        """Registers a function to call when a message with the specified message_code is received.
        Only one handler can be registered per message_code. Subsequent registrations will override
        the previous registration."""
        if not self.__protocol:
            raise ScreenLogicError(
                "Not connected to ScreenLogic gateway. Must connect to gateway before registering handler."
            )
        self.__protocol.register_async_message_callback(message_code, handler, *argv)

    async def async_send_message(self, message_code: int, message: bytes = b""):
        """Sends a message to the protocol adapter."""
        if not self.is_connected:
            raise ScreenLogicWarning(
                "Not connected to protocol adapter. send_message failed."
            )
        _LOGGER.debug(f"User requesting {message_code}")
        return await async_make_request(self.__protocol, message_code, message)

    async def _async_get_config(self):
        if not self.is_connected:
            raise ScreenLogicWarning(
                "Not connected to protocol adapter. get_config failed."
            )
        _LOGGER.debug("Requesting config data")
        self.__last[DATA.KEY_CONFIG] = await async_request_pool_config(
            self.__protocol, self.__data
        )

    async def _async_get_status(self):
        if not self.is_connected:
            raise ScreenLogicWarning(
                "Not connected to protocol adapter. get_status failed."
            )
        _LOGGER.debug("Requesting pool status")
        self.__last["status"] = await async_request_pool_status(
            self.__protocol, self.__data
        )

    async def _async_get_pumps(self):
        if not self.is_connected:
            raise ScreenLogicWarning(
                "Not connected to protocol adapter. get_pumps failed."
            )
        for pumpID in self.__data[DATA.KEY_PUMPS]:
            if self.__data[DATA.KEY_PUMPS][pumpID]["data"] != 0:
                _LOGGER.debug("Requesting pump %i data", pumpID)
                last_pumps = self.__last.setdefault(DATA.KEY_PUMPS, {})
                last_pumps[pumpID] = await async_request_pump_status(
                    self.__protocol, self.__data, pumpID
                )

    async def _async_get_chemistry(self):
        if not self.is_connected:
            raise ScreenLogicWarning(
                "Not connected to protocol adapter. get_chemistry failed."
            )
        _LOGGER.debug("Requesting chemistry data")
        self.__last[DATA.KEY_CHEMISTRY] = await async_request_chemistry(
            self.__protocol, self.__data
        )

    async def _async_get_scg(self):
        if not self.is_connected:
            raise ScreenLogicWarning(
                "Not connected to protocol adapter. get_scg failed."
            )
        _LOGGER.debug("Requesting scg data")
        self.__last[DATA.KEY_SCG] = await async_request_scg_config(
            self.__protocol, self.__data
        )

    async def _async_add_client(self):
        if not self.is_connected:
            raise ScreenLogicWarning(
                "Not connected to protocol adapter. add_client failed."
            )
        _LOGGER.debug("Requesting add client")
        return await async_request_add_client(self.__protocol)

    async def _async_remove_client(self):
        if not self.is_connected:
            raise ScreenLogicWarning(
                "Not connected to protocol adapter. remove_client failed."
            )
        _LOGGER.debug("Requesting remove client")
        return await async_request_remove_client(self.__protocol)

    async def _async_setup_push(self) -> bool:
        if self.is_connected and self.__is_client:
            self.__protocol.register_async_message_callback(
                CODE.STATUS_CHANGED, self._async_status_updated, self.__data
            )
            self.__protocol.register_async_message_callback(
                CODE.CHEMISTRY_CHANGED, self._async_chemistry_updated, self.__data
            )
            self.__protocol.register_async_message_callback(
                CODE.COLOR_UPDATE, self._async_color_updated, self.__data
            )
            return True
        return False

    async def async_data_updated(self):
        if self.__is_client:
            await self.ping_debounce()
            if self.__async_data_updated_callback:
                await self.__async_data_updated_callback()

    async def _async_status_updated(self, message: bytes, data: dict):
        decode_pool_status(message, data)
        await self.async_data_updated()

    async def _async_chemistry_updated(self, message: bytes, data: dict):
        decode_chemistry(message, data)
        await self.async_data_updated()

    async def _async_color_updated(self, message: bytes, data: dict):
        decode_color_update(message, data)
        _LOGGER.debug(data[DATA.KEY_CONFIG]["color_state"])
        await self.async_data_updated()

    async def ping_debounce(self):
        if (
            not self.__protocol.last_request
            or (delta := time.monotonic() - self.__protocol.last_request)
            > CLIENT_MIN_COMM
        ):
            _LOGGER.debug(
                f"Last communication was longer than {CLIENT_MIN_COMM} seconds ago by {delta} seconds. Pinging."
            )
            if await async_request_ping(self.__protocol):
                _LOGGER.debug("Ping successful.")

    def _is_valid_circuit(self, circuit):
        return circuit in self.__data[DATA.KEY_CIRCUITS]

    def _is_valid_circuit_state(self, state):
        return state == 0 or state == 1

    def _is_valid_body(self, body):
        return body in self.__data[DATA.KEY_BODIES]

    def _is_valid_heatmode(self, heatmode):
        return 0 <= heatmode < 5

    def _is_valid_heattemp(self, body, temp):
        min_temp = self.__data[DATA.KEY_BODIES][int(body)]["min_set_point"]["value"]
        max_temp = self.__data[DATA.KEY_BODIES][int(body)]["max_set_point"]["value"]
        return min_temp <= temp <= max_temp

    def _is_valid_color_mode(self, mode):
        return 0 <= mode <= 21

    def _is_valid_scg_value(self, scg_value, body_type):
        return 0 <= scg_value <= SCG.LIMIT_FOR_BODY[body_type]

    def _is_valid_ph_setpoint(self, ph_setpoint: float):
        return (
            CHEMISTRY.RANGE_PH_SETPOINT[RANGE.MIN]
            <= ph_setpoint
            <= CHEMISTRY.RANGE_PH_SETPOINT[RANGE.MAX]
        )

    def _is_valid_orp_setpoint(self, orp_setpoint: int):
        return (
            CHEMISTRY.RANGE_ORP_SETPOINT[RANGE.MIN]
            <= orp_setpoint
            <= CHEMISTRY.RANGE_ORP_SETPOINT[RANGE.MAX]
        )
