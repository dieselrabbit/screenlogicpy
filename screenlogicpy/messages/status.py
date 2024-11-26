from copy import deepcopy
import struct

from .base import *
from ..devices.base import *
from ..devices.circuit import Circuit
from ..devices.controller import CONTROLLER_STATE
from ..devices.heater import HEAT_MODE, HEAT_STATE, Heater
from ..system import *

__all__ = (
    "PoolStatusRequest",
    "PoolStatusResponse",
    "PoolStatusChanged",
)


class PoolStatusRequest(BaseRequest):
    _code = MessageCode.GET_POOL_STATUS
    _payload = Payload(struct.pack("<I", 0))


class PoolStatusResponse(BaseResponse):
    _code = MessageCode.GET_POOL_STATUS + 1

    def decode(self, system: System) -> None:
        """Decode a pool status response or update message payload and set the relevant values on the provided Pool Controller."""
        controller = system.controller

        controller.state = CONTROLLER_STATE(self.payload.next_uint32())
        controller.freeze_flags = self.payload.next_uint8()
        controller.config.remotes = self.payload.next_uint8()
        controller.pool_delay = bool(self.payload.next_uint8())
        controller.spa_delay = bool(self.payload.next_uint8())
        controller.cleaner_delay = bool(self.payload.next_uint8())

        unknowns = system.unknown_values.setdefault(self.code, {})

        # Skip ahead 3 bytes?
        unknowns[self.payload.position] = self.payload.unknown_uint8()
        unknowns[self.payload.position] = self.payload.unknown_uint8()
        unknowns[self.payload.position] = self.payload.unknown_uint8()

        controller.air_temperature = self.payload.next_int32()

        # Bodies of water
        body_count = self.payload.next_uint32()

        for i in range(body_count):
            btype, ltemp, hstate, heat_sp, cool_sp, hmode = self.payload.next("<I5i")
            heater: Heater = system.heaters.setdefault(
                str(i), Heater(i, system.config.body_defs[str(btype)])
            )
            heater.last_temp = ltemp
            heater.state = HEAT_STATE(hstate)
            heater.heat_setpoint = heat_sp
            heater.cool_setpoint = cool_sp
            heater.mode = HEAT_MODE(hmode)

        # Circuits
        circuit_count = self.payload.next_uint32()

        for i in range(circuit_count):
            circuit_id = self.payload.next_uint32()

            circuit: Circuit = controller.circuits[str(circuit_id)]

            circuit.state = bool(self.payload.next_uint32())
            circuit.config.light_set = self.payload.next_uint8()
            circuit.config.light_position = self.payload.next_uint8()
            circuit.config.light_stagger = self.payload.next_uint8()

            circuit.delay_active = bool(self.payload.next_uint8())

        controller.ph = self.payload.next_int32() / 100
        controller.orp = self.payload.next_int32()
        controller.saturation_index = self.payload.next_int32() / 100
        controller.salt_ppm = self.payload.next_int32() * 50
        controller.ph_supply_level = self.payload.next_int32()
        controller.orp_supply_level = self.payload.next_int32()
        controller.active_alert = bool(self.payload.next_int32())


class PoolStatusChanged(PoolStatusResponse):
    _code = MessageCode.STATUS_CHANGED
