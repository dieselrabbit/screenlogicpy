from enum import IntFlag
from dataclasses import dataclass, field

from .base import *

__all__ = ("Circuit",)


class CIRCUIT_FLAG(IntFlag):
    FREEZE_ENABLED = 1
    DARK = 2


class FUNCTION(SLIntEnum):
    # Known circuit functions.
    GENERIC = 0
    SPA = 1
    POOL = 2
    SECOND_SPA = 3
    SECOND_POOL = 4
    MASTER_CLEANER = 5
    CLEANER = 6
    LIGHT = 7
    DIMMER = 8
    SAM_LIGHT = 9
    SAL_LIGHT = 10
    PHOTONGEN = 11
    COLOR_WHEEL = 12
    VALVE = 13
    SPILLWAY = 14
    FLOOR_CLEANER = 15
    INTELLIBRITE = 16
    MAGICSTREAM = 17
    DIMMER_25 = 18


class VIEW(SLIntEnum):
    POOL = 0
    SPA = 1
    FEATURES = 2
    SYNC_SWIM = 3
    LIGHTS = 4
    DONT_SHOW = 5
    INVALID = 6


GENERIC_CIRCUIT_NAMES = [
    *[f"Aux {num}" for num in range(1, 25)],  # Last number is 24
    "AuxEx",
    *[f"Feature {num}" for num in range(1, 9)],  # Last number is 8
]

DEFAULT_CIRCUIT_NAMES = ["Spa", "Pool", *GENERIC_CIRCUIT_NAMES]


@dataclass
class CircuitConfig:

    name_index: int = None
    flags: int = 0
    light_set: int = 0
    light_position: int = 0
    light_stagger: int = 0


@dataclass
class Circuit:
    """Represents a Controller circuit and its configuration."""

    id: int
    name: str
    device_id: int = None
    state: bool = False
    delay_active: bool = False
    function: FUNCTION = FUNCTION.GENERIC
    default_runtime: int = 720
    display: VIEW = VIEW.FEATURES
    config: CircuitConfig = field(default_factory=CircuitConfig)

    @property
    def freeze_enabled(self) -> bool:
        return CIRCUIT_FLAG.FREEZE_ENABLED in self.flags
