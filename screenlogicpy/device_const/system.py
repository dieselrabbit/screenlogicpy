from enum import IntFlag
from ..const import SLIntEnum


class BODY_TYPE(SLIntEnum):
    POOL = 0
    SPA = 1


class CONTROLLER:
    CONTROLLER_HARDWARE_MAP = {
        0: {0: "IntelliTouch i5+3S"},
        1: {0: "IntelliTouch i7+3"},
        2: {0: "IntelliTouch i9+3"},
        3: {0: "IntelliTouch i5+3S"},
        4: {0: "IntelliTouch i9+3S"},
        5: {0: "IntelliTouch i10+3D", 1: "IntelliTouch i10X"},
        6: {0: "IntelliTouch i10X"},
        10: {0: "SunTouch"},
        11: {0: "Suntouch/Intellicom"},
        13: {
            0: "EasyTouch2 8",
            1: "EasyTouch2 8P",
            2: "EasyTouch2 4",
            3: "EasyTouch2 4P",
            5: "EasyTouch2 PL4",
            6: "EasyTouch2 PSL4",
        },
        14: {
            0: "EasyTouch1 8",
            1: "EasyTouch1 8P",
            2: "EasyTouch1 4",
            3: "EasyTouch1 4P",
        },
    }

    @classmethod
    def model_from_type(cls, controller_type: int, hardware_type: int) -> str:
        try:
            return cls.CONTROLLER_HARDWARE_MAP[controller_type][hardware_type]
        except KeyError:
            return f"Unknown Model C:{controller_type} H:{hardware_type}"


class CONTROLLER_STATE(SLIntEnum):
    UNKNOWN = 0
    READY = 1
    SYNC = 2
    SERVICE = 3


EQUIPMENT_MASK = 0x1FFFF


class EQUIPMENT_FLAG(IntFlag):
    """Equipment flags."""

    SOLAR = 0x1
    SOLAR_AS_HEAT_PUMP = 0x2
    CHLORINATOR = 0x4
    INTELLIBRITE = 0x8
    INTELLIFLO_0 = 0x10
    INTELLIFLO_1 = 0x20
    INTELLIFLO_2 = 0x40
    INTELLIFLO_3 = 0x80
    INTELLIFLO_4 = 0x100
    INTELLIFLO_5 = 0x200
    INTELLIFLO_6 = 0x400
    INTELLIFLO_7 = 0x800
    NO_SPECIAL_LIGHTS = 0x1000
    HAS_COOLING = 0x2000
    MAGIC_STREAM = 0x4000
    INTELLICHEM = 0x8000
    HYBRID_HEATER = 0x10000


class COLOR_MODE(SLIntEnum):
    ALL_OFF = 0
    ALL_ON = 1
    COLOR_SET = 2
    COLOR_SYNC = 3
    COLOR_SWIM = 4
    PARTY = 5
    ROMANCE = 6
    CARIBBEAN = 7
    AMERICAN = 8
    SUNSET = 9
    ROYAL = 10
    SAVE = 11
    RECALL = 12
    BLUE = 13
    GREEN = 14
    RED = 15
    WHITE = 16
    MAGENTA = 17
    THUMPER = 18
    NEXT_MODE = 19
    RESET = 20
    HOLD = 21
