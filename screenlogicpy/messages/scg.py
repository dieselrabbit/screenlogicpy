import struct

from .base import *
from ..system import *

__all__ = (
    "GetSaltCellConfigRequest",
    "GetSaltCellConfigResponse",
    "SetSaltCellConfigRequest",
    "SetSaltCellConfigResponse",
)


class GetSaltCellConfigRequest(BaseRequest):
    _code = MessageCode.GET_SCG_CONFIG
    _payload = Payload(struct.pack("<I", 0))


class GetSaltCellConfigResponse(BaseResponse):
    _code = MessageCode.GET_SCG_CONFIG + 1

    def decode(self, system: System) -> None:

        scg = system.chlorinator

        scg.config.is_present = bool(self.payload.next_uint32())
        scg.state = self.payload.next_uint32()
        scg.pool_setpoint = self.payload.next_uint32()
        scg.spa_setpoint = self.payload.next_uint32()
        scg.salt_ppm = self.payload.next_uint32()
        scg.state_flags = self.payload.next_uint32()
        scg.super_chlorinate_time = self.payload.next_uint32()


class SetSaltCellConfigRequest(BaseRequest):
    _code = MessageCode.SET_SCG

    def __init__(
        self,
        pool_output: int,
        spa_output: int,
        super_chlor: int = 0,
        super_time: int = 0,
    ) -> None:
        self._payload = Payload(
            struct.pack("<5I", 0, pool_output, spa_output, super_chlor, super_time)
        )


class SetSaltCellConfigResponse(BaseResponse):
    _code = MessageCode.SET_SCG + 1
