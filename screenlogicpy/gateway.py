from .const import BODY_TYPE, DATA, SCG, ScreenLogicWarning
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
)


class ScreenLogicGateway:
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
        self.__connected = False
        self.__data = {}

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
        return self.__connected

    async def async_connect(self) -> bool:
        """Connects to the ScreenLogic protocol adapter"""
        if self.__connected:
            return True

        connectPkg = await async_connect_to_gateway(
            self.__ip, self.__port, self._set_disconnected, self.__data
        )
        if connectPkg:
            self.__transport, self.__protocol, self.__mac = connectPkg
            self.__version = await async_request_gateway_version(self.__protocol)
            if self.__version:
                self.__connected = True
                await self._async_get_config()
                return True
        return False

    async def async_disconnect(self):
        """Disconnects from the ScreenLogic protocol adapter"""
        self.__connected = False
        if self.__transport and not self.__transport.is_closing():
            self.__transport.close()

    async def async_update(self) -> bool:
        """Updates all ScreenLogic data if already connected. Tries to connect if not."""
        if (
            not self.is_connected and not await self.async_connect()
        ) or not self.__data:
            return False

        try:
            await self._async_get_status()
            await self._async_get_pumps()
            await self._async_get_chemistry()
            await self._async_get_scg()
            return True
        except ScreenLogicWarning as warn:
            self.__connected = False
            raise warn

    def get_data(self) -> dict:
        return self.__data

    async def async_set_circuit(self, circuitID, circuitState):
        if not self._is_valid_circuit(circuitID):
            raise ValueError(f"Invalid circuitID: {circuitID}")
        if not self._is_valid_circuit_state(circuitState):
            raise ValueError(f"Invalid circuitState: {circuitState}")

        if self.__connected or await self.async_connect():
            if await async_request_pool_button_press(
                self.__protocol, circuitID, circuitState
            ):
                return True
        return False

    async def async_set_heat_temp(self, body, temp):
        if not self._is_valid_body(body):
            raise ValueError(f"Invalid body: {body}")
        if not self._is_valid_heattemp(body, temp):
            raise ValueError(f"Invalid temp ({temp}) for body ({body})")

        if self.__connected or await self.async_connect():
            if await async_request_set_heat_setpoint(self.__protocol, body, temp):
                return True
        return False

    async def async_set_heat_mode(self, body, mode):
        if not self._is_valid_body(body):
            raise ValueError(f"Invalid body: {body}")
        if not self._is_valid_heatmode(mode):
            raise ValueError(f"Invalid mode: {mode}")

        if self.__connected or await self.async_connect():
            if await async_request_set_heat_mode(self.__protocol, body, mode):
                return True
        return False

    async def async_set_color_lights(self, light_command):
        if not self._is_valid_color_mode(light_command):
            raise ValueError(f"Invalid light_command: {light_command}")

        if self.__connected or await self.async_connect():
            if await async_request_pool_lights_command(self.__protocol, light_command):
                return True
        return False

    async def async_set_scg_config(self, pool_output, spa_output):
        if not self._is_valid_scg_value(pool_output, BODY_TYPE.POOL):
            raise ValueError(f"Invalid pool_output: {pool_output}")
        if not self._is_valid_scg_value(spa_output, BODY_TYPE.SPA):
            raise ValueError(f"Invalid spa_output: {spa_output}")

        if self.__connected or await self.async_connect():
            if await async_request_set_scg_config(
                self.__protocol, pool_output, spa_output
            ):
                return True
        return False

    def _set_disconnected(self):
        self.__connected = False

    async def _async_get_config(self):
        if not self.__connected:
            raise ScreenLogicWarning(
                "Not connected to protocol adapter. get_config failed."
            )
        await async_request_pool_config(self.__protocol, self.__data)

    async def _async_get_status(self):
        if not self.__connected:
            raise ScreenLogicWarning(
                "Not connected to protocol adapter. get_status failed."
            )
        await async_request_pool_status(self.__protocol, self.__data)

    async def _async_get_pumps(self):
        if not self.__connected:
            raise ScreenLogicWarning(
                "Not connected to protocol adapter. get_pumps failed."
            )
        for pumpID in self.__data[DATA.KEY_PUMPS]:
            if self.__data[DATA.KEY_PUMPS][pumpID]["data"] != 0:
                await async_request_pump_status(self.__protocol, self.__data, pumpID)

    async def _async_get_chemistry(self):
        if not self.__connected:
            raise ScreenLogicWarning(
                "Not connected to protocol adapter. get_chemistry failed."
            )
        await async_request_chemistry(self.__protocol, self.__data)

    async def _async_get_scg(self):
        if not self.__connected:
            raise ScreenLogicWarning(
                "Not connected to protocol adapter. get_scg failed."
            )
        await async_request_scg_config(self.__protocol, self.__data)

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
