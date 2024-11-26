import struct

from .base import *
from ..system import *

__all__ = (
    "UserConfigRequest",
    "UserConfigResponse",
)


class UserConfigRequest(BaseRequest):
    _code = MessageCode.GET_USER_CONFIG
    _payload = Payload(struct.pack("<I", 0))


class UserConfigResponse(BaseResponse):
    _code = MessageCode.GET_USER_CONFIG + 1

    def decode(self, system: System) -> None:

        gateway = system.gateway

        unknowns = system.unknown_values.setdefault(self.code, {})
        unknowns[self.payload.position] = self.payload.unknown_int32()
        unknowns[self.payload.position] = self.payload.unknown_int32()

        gateway.name = self.payload.next_string()

        gateway.config.user_zip = self.payload.next_string()

        gateway.config.user_latitude = self.payload.next_uint32() / 10000  # North

        gateway.config.user_longitude = self.payload.next_uint32() / -10000  # West

        system.controller.config.time_config.tz_offset = self.payload.next_int32()

        gateway.firmware = self.payload.next_string()

        unknowns[self.payload.position] = self.payload.unknown_int32()
        unknowns[self.payload.position] = self.payload.unknown_int32()
        unknowns[self.payload.position] = self.payload.unknown_int32()
        unknowns[self.payload.position] = self.payload.unknown_int32()
        unknowns[self.payload.position] = self.payload.unknown_int32()
        unknowns[self.payload.position] = self.payload.unknown_int32()
        unknowns[self.payload.position] = self.payload.unknown_int32()
        unknowns[self.payload.position] = self.payload.unknown_int32()
        gateway.config.architecture = self.payload.next_string()
        gateway.config.style = self.payload.next_string()
