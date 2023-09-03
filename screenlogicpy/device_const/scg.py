from .system import BODY_TYPE
from ..const.common import SLValueRange


class SCG_RANGE:
    POOL_SETPOINT = SLValueRange(0, 100)
    SPA_SETPOINT = SLValueRange(0, 100)
    SUPER_CHLOR_RT = SLValueRange(0, 72)


RANGE_FOR_BODY = {
    BODY_TYPE.POOL: SCG_RANGE.POOL_SETPOINT,
    BODY_TYPE.SPA: SCG_RANGE.SPA_SETPOINT,
}
