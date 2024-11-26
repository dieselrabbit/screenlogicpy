import struct

from ..devices.chemistry import (
    ALARM_FLAG,
    ALERT_FLAG,
    BALANCE_FLAG,
    CONFIG_FLAG,
)
from ..system import *
from .base import *

__all__ = (
    "GetChemistryStatusRequest",
    "GetChemistryStatusResponse",
    "ChemistryStatusChanged",
    "SetChemistryConfigRequest",
    "SetChemistryConfigResponse",
)


class GetChemistryStatusRequest(BaseRequest):
    _code = MessageCode.GET_CHEMISTRY
    _payload = Payload(struct.pack("<I", 0))


class GetChemistryStatusResponse(BaseResponse):
    _code = MessageCode.GET_CHEMISTRY + 1

    def decode(self, system: System) -> None:

        chem = system.chemistry

        chem.is_present = self.payload.next_uint32() == 42

        unknowns = system.unknown_values.setdefault(self.code, {})

        unknowns[self.payload.position] = self.payload.unknown_uint8()

        chem.ph_now = self.payload.next(">H")[0] / 100
        chem.orp_now = self.payload.next(">H")[0]
        chem.ph_setpoint = self.payload.next(">H")[0] / 100
        chem.orp_setpoint = self.payload.next(">H")[0]
        chem.ph_dose_last_duration = self.payload.next(">I")[0]
        chem.orp_dose_last_duration = self.payload.next(">I")[0]
        chem.ph_dose_last_volume = self.payload.next(">H")[0]
        chem.orp_dose_last_volume = self.payload.next(">H")[0]
        chem.ph_supply_level = self.payload.next_uint8()
        chem.orp_supply_level = self.payload.next_uint8()

        chem.saturation_index = self.payload.next_int8() / 100
        chem.calcium_hardness = self.payload.next(">H")[0]
        chem.cya = self.payload.next(">H")[0]
        chem.total_alkalinity = self.payload.next(">H")[0]
        chem.salt_tds = self.payload.next_uint8() * 50

        chem.probe_is_celsius = bool(self.payload.next_uint8())
        chem.probe_temperature = self.payload.next_int8()

        chem.alarm_flags = ALARM_FLAG(self.payload.next_uint8())
        chem.alert_flags = ALERT_FLAG(self.payload.next_uint8())
        chem.dose_states = self.payload.next_uint8()
        chem.config_flags = CONFIG_FLAG(self.payload.next_uint8())

        ver_minor = self.payload.next_uint8()
        ver_major = self.payload.next_uint8()
        chem.firmware = f"{ver_major}.{ver_minor:03}"

        chem.balance_flags = BALANCE_FLAG(self.payload.next_uint8())

        unknowns[self.payload.position] = self.payload.unknown_uint8()
        unknowns[self.payload.position] = self.payload.unknown_uint8()
        unknowns[self.payload.position] = self.payload.unknown_uint8()


class ChemistryStatusChanged(GetChemistryStatusResponse):
    _code = MessageCode.CHEMISTRY_CHANGED


class SetChemistryConfigRequest(BaseRequest):
    _code = MessageCode.SET_CHEMISTRY_CONFIG

    def __init__(
        self,
        ph_setpoint: int,
        orp_setpoint: int,
        calcium: int,
        alkalinity: int,
        cyanuric: int,
        salt: int,
    ) -> None:
        self._payload = Payload(
            struct.pack(
                "<7I", 0, ph_setpoint, orp_setpoint, calcium, alkalinity, cyanuric, salt
            )
        )


class SetChemistryConfigResponse(BaseResponse):
    _code = MessageCode.SET_CHEMISTRY_CONFIG + 1
