from enum import IntFlag
from dataclasses import dataclass, field

from .base import *
from .circuit import Circuit


__all__ = (
    "CONTROLLER_HARDWARE_MAP",
    "BODY_COUNT",
    "PUMP_COUNT",
    "EQUIPMENT_MASK_736",
    "CONTROLLER_STATE",
    "EQUIPMENT_FLAG",
    "COLOR_MODE",
    "TimeConfig",
    "ControllerConfig",
    "Controller",
)

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

BODY_COUNT = 2  # Bodies of water

PUMP_COUNT = 8

# Only lower half of equipment int is valid on build 736.0
EQUIPMENT_MASK_736 = 0xFFFF


class CONTROLLER_STATE(SLIntEnum):
    UNKNOWN = 0
    READY = 1
    SYNC = 2
    SERVICE = 3


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


@dataclass
class TimeConfig:

    auto_dst: bool = False
    tz_offset: int = 0
    client: float = 0.0
    delta: float = 0.0


@dataclass
class ControllerConfig:

    controller_data: int = 0
    colors: dict[str, tuple[int,]] = field(default_factory=dict)
    default_circuit_name: str = ""
    is_celsius: bool = False
    remotes: int = 0
    show_alarms: bool = False
    time_config: TimeConfig = field(default_factory=TimeConfig)
    view_flags: int = 0


@dataclass
class Controller:
    """Represents the main pool controller within the system."""

    id: int = 0
    config: ControllerConfig = field(default_factory=ControllerConfig)
    controller_type: int = 0
    hardware_type: int = 0
    equipment_flags: EQUIPMENT_FLAG = 0
    circuits: dict[str, Circuit] = field(default_factory=dict)
    state: CONTROLLER_STATE = 0
    freeze_flags: int = 0
    pool_delay: bool = False
    spa_delay: bool = False
    cleaner_delay: bool = False
    air_temperature: int = 0
    ph: float = 0.0
    orp: int = 0
    saturation_index: float = 0.0
    salt_ppm: int = 0
    ph_supply_level: int = 0
    orp_supply_level: int = 0
    active_alert: bool = False
    firmware: str = ""
    time: float = 0.0

    @property
    def model(self) -> str:
        return self.model_from_type(
            self.controller_type,
            self.hardware_type,
        )

    @property
    def freeze_mode(self) -> bool:
        return self.freeze_flags & 0x08 != 0

    def set_color_light(self, mode: int) -> None:
        pass

    def circuit_from_device_id(self, device_id: int) -> Circuit | None:
        for cid, circuit in self.circuits.items():
            if circuit.device_id == device_id:
                return circuit
        return None

    def circuit_from_id(self, circuit_id: int) -> Circuit | None:
        return self.circuits.get(str(circuit_id), None)

    @classmethod
    def model_from_type(cls, controller_type: int, hardware_type: int) -> str:
        try:
            return CONTROLLER_HARDWARE_MAP[controller_type][hardware_type]
        except KeyError:
            return f"Unknown Model C:{controller_type} H:{hardware_type}"
