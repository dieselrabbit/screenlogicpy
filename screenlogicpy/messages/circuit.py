import struct

from screenlogicpy.devices.controller import Controller

from .base import *
from ..exceptions import *
from ..system import System


class SetCircuitRequest(BaseRequest):
    _code = MessageCode.SET_CIRCUIT

    def __init__(self, circuit_id: int, is_on: bool) -> None:
        self._payload = Payload(struct.pack("<III", 0, circuit_id, int(is_on)))


class SetCircuitResponse(BaseResponse):
    _code = MessageCode.SET_CIRCUIT + 1

    def decode(self, system: System) -> None:
        if not self.payload == b"":
            raise ScreenLogicResponseError("Unexpected Response")
