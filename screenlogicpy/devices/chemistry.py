from dataclasses import dataclass, field
from enum import IntFlag

from .base import *

__all__ = ("IntelliChem",)


class ALARM_FLAG(IntFlag):
    FLOW = 0x01
    PH_HIGH = 0x02
    PH_LOW = 0x04
    ORP_HIGH = 0x08
    ORP_LOW = 0x10
    PH_SUPPLY = 0x20
    ORP_SUPPLY = 0x40
    PROBE_FAULT = 0x80


class ALERT_FLAG(IntFlag):
    PH_LOCKOUT = 0x01
    PH_LIMIT = 0x02
    ORP_LIMIT = 0x04
    INVALID_SETUP = 0x08
    CHLORINATOR_COMM_ERROR = 0x10


class BALANCE:
    IDEAL = "Ideal"
    NORMAL = "Normal"
    SCALING = "Scaling"
    CORROSIVE = "Corrosive"

    @classmethod
    def from_saturation(cls, sat: float) -> str:
        # Pentair display values. Different than alarm values.
        if -0.1 <= sat <= 0.1:
            return cls.IDEAL
        elif -0.5 <= sat <= 0.5:
            return cls.NORMAL
        return cls.CORROSIVE if sat < -0.5 else cls.SCALING


class BALANCE_FLAG(IntFlag):
    CORROSIVE = 0x1
    SCALING = 0x2


class CONFIG_FLAG(IntFlag):
    FLOW_DELAY = 0x02
    INTELLICHLOR = 0x04
    PH_PRIORITY = 0x08
    USE_CHLORINATOR = 0x10
    ADVANCED_DISPLAY = 0x20
    PH_SUPPLY_TYPE = 0x40
    COMMS_LOST = 0x80  # ?


class DOSE_MASK(IntFlag):
    ORP_TYPE = 0x03
    PH_TYPE = 0x0C
    PH_STATE = 0x30
    ORP_STATE = 0xC0


class DOSE_STATE(SLIntEnum):
    DOSING = 0
    MIXING = 1
    MONITORING = 2


class DOSE_TYPE_ORP(SLIntEnum):
    NONE = 0
    CHLORINE = 1
    SCG = 2  # ?


class DOSE_TYPE_PH(SLIntEnum):
    NONE = 0
    ACID = 1
    CO2 = 2


# Valid ranges listed in IntelliChem documentation
class CHEM_RANGE:
    PH_SETPOINT = SLValueRange(7.2, 7.6)
    ORP_SETPOINT = SLValueRange(400, 800)
    CALCIUM_HARDNESS = SLValueRange(25, 800)
    CYANURIC_ACID = SLValueRange(0, 201)
    TOTAL_ALKALINITY = SLValueRange(25, 800)
    SALT_TDS = SLValueRange(500, 6500)


@dataclass
class IntelliChem:
    """Represents an IntelliChem device."""

    is_present: bool = False
    ph_now: float = 0.0
    orp_now: int = 0
    ph_setpoint: float = 7.5
    orp_setpoint: int = 650
    ph_dose_last_duration: int = 0
    orp_dose_last_duration: int = 0
    ph_dose_last_volume: int = 0
    orp_dose_last_volume: int = 0
    ph_range: SLValueRange = CHEM_RANGE.PH_SETPOINT
    orp_range: SLValueRange = CHEM_RANGE.ORP_SETPOINT
    ph_supply_level: int = 0
    orp_supply_level: int = 0
    saturation_index: float = 0.0
    calcium_hardness: int = 0
    cya: int = 0
    total_alkalinity: int = 0
    salt_tds: int = 0
    probe_is_celsius: bool = False
    probe_temperature: int = 0
    alarm_flags: ALARM_FLAG = 0
    alert_flags: ALERT_FLAG = 0
    dose_states: int = 0
    config_flags: CONFIG_FLAG = 0
    balance_flags: BALANCE_FLAG = 0
    firmware: str = ""

    @property
    def ph_dose_state(self) -> DOSE_STATE:
        return DOSE_STATE((self.dose_states & DOSE_MASK.PH_STATE) >> 4)

    @property
    def orp_dose_state(self) -> DOSE_STATE:
        return DOSE_STATE((self.dose_states & DOSE_MASK.ORP_STATE) >> 6)

    # Alarms
    @property
    def alarm_flow(self) -> bool:
        return ALARM_FLAG.FLOW in self.alarm_flags

    @property
    def alarm_ph_high(self) -> bool:
        return ALARM_FLAG.PH_HIGH in self.alarm_flags

    @property
    def alarm_ph_low(self) -> bool:
        return ALARM_FLAG.PH_LOW in self.alarm_flags

    @property
    def alarm_orp_high(self) -> bool:
        return ALARM_FLAG.ORP_HIGH in self.alarm_flags

    @property
    def alarm_orp_low(self) -> bool:
        return ALARM_FLAG.ORP_LOW in self.alarm_flags

    @property
    def alarm_ph_supply(self) -> bool:
        return ALARM_FLAG.PH_SUPPLY in self.alarm_flags

    @property
    def alarm_orp_supply(self) -> bool:
        return ALARM_FLAG.ORP_SUPPLY in self.alarm_flags

    @property
    def alarm_probe_fault(self) -> bool:
        return ALARM_FLAG.PROBE_FAULT in self.alarm_flags

    # SI <= -0.41
    @property
    def alarm_balance_corosive(self) -> bool:
        return BALANCE_FLAG.CORROSIVE in self.balance_flags

    # SI >= +0.53
    @property
    def alarm_balance_scaling(self) -> bool:
        return BALANCE_FLAG.SCALING in self.balance_flags

    # Alerts
    @property
    def alert_ph_lockout(self) -> bool:
        return ALERT_FLAG.PH_LOCKOUT in self.alert_flags

    @property
    def alert_ph_limit(self) -> bool:
        return ALERT_FLAG.PH_LIMIT in self.alert_flags

    @property
    def alert_orp_limit(self) -> bool:
        return ALERT_FLAG.ORP_LIMIT in self.alert_flags

    def set_chemistry_values(
        self,
        *,
        ph_setpoint: float | None = None,
        orp_setpoint: int | None = None,
        calcium_hardness: int | None = None,
        total_alkalinity: int | None = None,
        cya: int | None = None,
        salt_tds_ppm: int | None = None,
    ) -> None:
        pass
