from dataclasses import dataclass

from .base import *

__all__ = (
    "BodyTypeDefinition",
    "Heater",
)


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


@dataclass(frozen=True)
class BodyTypeDefinition:
    body_type: BODY_TYPE
    heat_range: SLValueRange

    @property
    def name(self) -> str:
        return self.body_type.title


@dataclass
class Heater:
    """Represents a heater for a body of water within the pool system."""

    id: int
    body_def: BodyTypeDefinition
    last_temp: int = None
    state: HEAT_STATE = HEAT_STATE.OFF
    heat_setpoint: int = None
    cool_setpoint: int = None
    mode: HEAT_MODE = HEAT_MODE.OFF

    @property
    def name(self) -> str:
        return f"{self.body_def.name} Heater"
