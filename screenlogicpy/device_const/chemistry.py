from enum import IntFlag
from ..const import SLIntEnum
from ..const.common import RANGE


class ALARM(IntFlag):
    FLOW = 0x01
    PH_HIGH = 0x02
    PH_LOW = 0x04
    ORP_HIGH = 0x08
    ORP_LOW = 0x10
    PH_SUPPLY = 0x20
    ORP_SUPPLY = 0x40
    PROBE_FAULT = 0x80


class ALERT(IntFlag):
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
        # Pentair values
        if -0.1 <= sat <= 0.1:
            return cls.IDEAL
        elif -0.5 <= sat <= 0.5:
            return cls.NORMAL
        return cls.CORROSIVE if sat < -0.5 else cls.SCALING


class DOSE:
    class MASK(IntFlag):
        ORP_TYPE = 0x03
        PH_TYPE = 0x0C
        PH_STATE = 0x30
        ORP_STATE = 0xC0

    class STATE(SLIntEnum):
        DOSING = 0
        MIXING = 1
        MONITORING = 2

    class TYPE:
        class ORP(SLIntEnum):
            NONE = 0
            CHLORINE = 1
            SCG = 2  # ?

        class PH(SLIntEnum):
            NONE = 0
            ACID = 1
            CO2 = 2


class FLAG(IntFlag):
    FLOW_DELAY = 0x02
    INTELLICHLOR = 0x04
    PH_PRIORITY = 0x08
    USE_CHLORINATOR = 0x10
    ADVANCED_DISPLAY = 0x20
    PH_SUPPLY_TYPE = 0x40
    COMMS_LOST = 0x80  # ?


# Valid ranges listed in IntelliChem documentation
RANGE_PH_SETPOINT = {RANGE.MIN: 7.2, RANGE.MAX: 7.6}
RANGE_ORP_SETPOINT = {RANGE.MIN: 400, RANGE.MAX: 800}
