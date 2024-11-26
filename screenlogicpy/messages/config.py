import struct

from .base import *
from ..devices.chemistry import IntelliChem
from ..devices.circuit import (
    FUNCTION,
    VIEW,
    Circuit,
)
from ..devices.controller import (
    BODY_COUNT,
    BODY_TYPE,
    PUMP_COUNT,
    EQUIPMENT_FLAG,
)
from ..devices.heater import BodyTypeDefinition
from ..devices import (
    Pump,
    SaltChlorineGenerator,
    SLValueRange,
)
from ..system import *

__all__ = (
    "GetPoolConfigRequest",
    "GetPoolConfigResponse",
)


class GetPoolConfigRequest(BaseRequest):
    _code = MessageCode.GET_POOL_CONFIG

    def __init__(self, controller_index: int = 0) -> None:
        self._payload = Payload(struct.pack("<II", controller_index, 0))


class GetPoolConfigResponse(BaseResponse):
    _code = MessageCode.GET_POOL_CONFIG + 1

    def decode(self, system: System) -> None:
        """Decode and apply values to `system` object."""

        controller = system.controller

        controller.id = self.payload.next_uint32()

        for body_type in range(BODY_COUNT):
            min_t, max_t = self.payload.next("<2B")
            system.config.body_defs[str(body_type)] = BodyTypeDefinition(
                BODY_TYPE(body_type), SLValueRange(min_t, max_t)
            )

        controller.config.is_celsius = bool(self.payload.next_uint8())
        controller.controller_type = self.payload.next_uint8()
        controller.hardware_type = self.payload.next_uint8()
        controller.config.controller_data = self.payload.next_uint8()
        controller.equipment_flags = EQUIPMENT_FLAG(self.payload.next_uint32())

        controller.config.default_circuit_name = self.payload.next_string()

        circuit_count = self.payload.next_uint32()

        controller.circuits = {}
        for _ in range(circuit_count):
            circuit_id = self.payload.next_int32()

            circuit_name = self.payload.next_string()
            circuit = Circuit(circuit_id, circuit_name)
            circuit.config.name_index = self.payload.next_uint8()
            circuit.function = FUNCTION(self.payload.next_uint8())
            circuit.display = VIEW(self.payload.next_uint8())
            circuit.config.flags = self.payload.next_uint8()
            circuit.config.light_set = self.payload.next_uint8()
            circuit.config.light_position = self.payload.next_uint8()
            circuit.config.light_stagger = self.payload.next_uint8()
            circuit.device_id = self.payload.next_uint8()

            circuit.default_runtime = self.payload.next_uint16()

            unknowns = system.unknown_values.setdefault(self.code, {})

            unknowns[self.payload.position] = self.payload.unknown_uint8()
            unknowns[self.payload.position] = self.payload.unknown_uint8()

            controller.circuits[str(circuit_id)] = circuit

        color_count = self.payload.next_uint32()

        for i in range(color_count):
            color_name = self.payload.next_string()
            controller.config.colors[color_name] = self.payload.next("<3I")

        # controller.pumps = [None] * PUMP_COUNT
        for i in range(PUMP_COUNT):
            if data := self.payload.next_uint8():
                system.pumps[str(i)] = Pump(i, data)

        controller.config.view_flags = self.payload.next_uint32()

        controller.config.show_alarms = bool(self.payload.next_uint32())
