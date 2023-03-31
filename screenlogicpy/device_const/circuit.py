from ..const import SLIntEnum


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


class INTERFACE(SLIntEnum):
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
