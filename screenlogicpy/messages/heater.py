import struct

from screenlogicpy.devices.controller import Controller

from .base import *
from ..devices.heater import HEAT_MODE
from ..system import System


class SetHeatModeRequest(BaseRequest):
    _code = MessageCode.SET_HEAT_MODE

    def __init__(self, heater: int, mode: HEAT_MODE) -> None:
        self._payload = Payload(struct.pack("<III", 0, heater, mode))


class SetHeatModeResponse(BaseResponse):
    _code = MessageCode.SET_HEAT_MODE + 1

    def decode(self, system: System) -> None:
        return


class SetHeatTemperature(BaseRequest):
    _code = MessageCode.SET_HEAT_TEMPERATURE

    def __init__(self, heater: int, temperature: int) -> None:
        self._payload = Payload(struct.pack("<III", 0, heater, temperature))


class SetHeatTemperature(BaseResponse):
    _code = MessageCode.SET_HEAT_TEMPERATURE + 1

    def decode(self, system: System) -> None:
        return
