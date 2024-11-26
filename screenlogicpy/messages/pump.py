import struct

from .base import *
from ..devices.base import *
from ..devices.pump import PRESET_COUNT, PUMP_TYPE, PumpPreset
from ..system import *

__all__ = (
    "PumpStatusRequest",
    "PumpStatusResponse",
)


class PumpStatusRequest(BaseRequest):
    _code = MessageCode.GET_PUMP_STATUS

    def __init__(self, pump_index: int) -> None:
        self._payload = Payload(struct.pack("<II", 0, pump_index))


class PumpStatusResponse(BaseResponse):
    _code = MessageCode.GET_PUMP_STATUS + 1

    def decode(self, system: System, pump_index: int) -> None:

        controller = system.controller

        pump = system.pumps[str(pump_index)]

        pump.type = PUMP_TYPE(self.payload.next_int32())

        state = self.payload.next_int32()
        if state & 0x8000000 == 0:
            pump.state = bool(state)

        pump.watts_now = self.payload.next_int32()
        pump.rpm_now = self.payload.next_int32()
        pump.flow_alarm = self.payload.next_int32()
        pump.gpm_now = self.payload.next_int32()

        unknowns = system.unknown_values.setdefault(self.code, {})
        unknowns[self.payload.position] = self.payload.unknown_uint32()

        name: str | None = None
        for i in range(PRESET_COUNT):
            device_id, setpoint, is_rpm = self.payload.next("<3I")
            pump.presets[str(i)] = PumpPreset(device_id, setpoint, is_rpm)
            if name is None:
                if (
                    circuit := controller.circuit_from_device_id(device_id)
                ) is not None:
                    name = circuit.name

        name = name if name is not None else "Default"
        pump.name = f"{name} Pump"
