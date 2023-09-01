from ..const import SLIntEnum


class PUMP_TYPE(SLIntEnum):
    NONE = 0
    INTELLIFLO_VF = 1
    INTELLIFLO_VS = 2
    INTELLIFLO_VSF = 3

    @property
    def title(self) -> str:
        return self._title().replace("Intelliflow", "IntelliFlow")
