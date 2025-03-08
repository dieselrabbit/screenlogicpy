from ..const import SLIntEnum
from ..const.common import SLIntValueRange

class PUMP_TYPE(SLIntEnum):
    NONE = 0
    INTELLIFLO_VF = 1
    INTELLIFLO_VS = 2
    INTELLIFLO_VSF = 3

    @property
    def title(self) -> str:
        return self._title().replace("Intelliflow", "IntelliFlow")

class INDEX_RANGE:
    PUMP = SLIntValueRange(0, 7)
    FLOW = SLIntValueRange(0, 7)

class FLOW_RANGE:
    GPM = SLIntValueRange(15, 130)
    RPM = SLIntValueRange(400, 3450)