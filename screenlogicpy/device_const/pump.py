from ..const import SLIntEnum
from ..const.common import SLValueRange

class PUMP_TYPE(SLIntEnum):
    NONE = 0
    INTELLIFLO_VF = 1
    INTELLIFLO_VS = 2
    INTELLIFLO_VSF = 3

    @property
    def title(self) -> str:
        return self._title().replace("Intelliflow", "IntelliFlow")

class INDEX_RANGE:
    PUMP = SLValueRange(0, 7)
    FLOW = SLValueRange(0, 7)

class FLOW_RANGE:
    GPM = SLValueRange(15, 130)
    RPM = SLValueRange(400, 3450)