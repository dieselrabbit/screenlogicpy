from .system import BODY_TYPE
from ..const.common import SLIntEnum, SLValueRange


class STATUS_FLAG(SLIntEnum):
    SCG_ACTIVE = 0x01

    # Assumptions
    SALT_VERY_LOW = 0x10
    SALT_LOW = 0x20
    SALT_OK = 0x40
    SALT_HIGH = 0x80

    # Maybe
    ICHEM_IN_CONTROL = 0x8000


class STATE_FLAG(SLIntEnum):
    SUPER_CHLORINATE = 0x01


class SCG_RANGE:
    POOL_SETPOINT = SLValueRange(0, 100)
    SPA_SETPOINT = SLValueRange(0, 100)
    SUPER_CHLOR_RT = SLValueRange(0, 72)


RANGE_FOR_BODY = {
    BODY_TYPE.POOL: SCG_RANGE.POOL_SETPOINT,
    BODY_TYPE.SPA: SCG_RANGE.SPA_SETPOINT,
}
