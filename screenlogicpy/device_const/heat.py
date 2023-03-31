from ..const import SLIntEnum


class HEAT_MODE(SLIntEnum):
    OFF = 0
    SOLAR = 1
    SOLAR_PREFERRED = 2
    HEATER = 3
    DONT_CHANGE = 4

    @property
    def title(self) -> str:
        return self._title().replace("Dont", "Don't")


class HEAT_STATE(SLIntEnum):
    OFF = 0
    SOLAR = 1
    HEATER = 2
    BOTH = 3
