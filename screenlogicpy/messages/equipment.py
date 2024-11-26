import struct

from .base import *
from ..system import *

__all__ = (
    "GetEquipmentConfigRequest",
    "GetEquipmentConfigResponse",
)


class GetEquipmentConfigRequest(BaseRequest):
    _code = MessageCode.GET_EQUIPMENT
    _payload = Payload(struct.pack("<I", 0))


class GetEquipmentConfigResponse(BaseResponse):
    _code = MessageCode.GET_EQUIPMENT + 1

    def decode(self, system: System) -> None:

        controller = system.controller
        controller.controller_type = self.payload.next_uint8()
        controller.hardware_type = self.payload.next_uint8()

        unknowns = system.unknown_values.setdefault(self.code, {})
        unknowns[self.payload.position] = self.payload.unknown_uint16()

        controller.config.controller_data = self.payload.next_uint32()

        equip = system.config.equipment
        equip.version_array = self.payload.next_array()
        equip.speed_array = self.payload.next_array()
        equip.valve_array = self.payload.next_array()
        equip.remote_array = self.payload.next_array()
        equip.sensor_array = self.payload.next_array()
        equip.delay_array = self.payload.next_array()
        equip.macro_array = self.payload.next_array()
        equip.misc_array = self.payload.next_array()
        equip.light_array = self.payload.next_array()
        equip.flow_array = self.payload.next_array()
        equip.sg_array = self.payload.next_array()
        equip.spaflow_array = self.payload.next_array()

        controller.firmware = f"{equip.version_array[0]}.{equip.version_array[1]}"
