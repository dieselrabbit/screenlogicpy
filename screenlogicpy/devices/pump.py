from dataclasses import dataclass, field

from .base import *


__all__ = ("Pump",)


PRESET_COUNT = 8


class PUMP_TYPE(SLIntEnum):
    NONE = 0
    INTELLIFLO_VF = 1
    INTELLIFLO_VS = 2
    INTELLIFLO_VSF = 3

    @property
    def title(self) -> str:
        return self._title().replace("Intelliflow", "IntelliFlow")


class VIRTUAL_DEVICE_ID(SLIntEnum):
    # Internal circuit/function device_ids
    NONE = 0
    SOLAR_ACTIVE = 128
    POOL_OR_SPA_HEATER_ACTIVE = 129
    POOL_HEATER_ACTIVE = 130
    SPA_HEATER_ACTIVE = 131
    FREEZE_MODE_ACTIVE = 132
    HEAT_BOOST = 133
    HEAT_ENABLE = 134
    INCREMENT_PUMP_SPEED = 135
    DECREMENT_PUMP_SPEED = 136
    POOL_HEATER = 155
    SPA_HEATER = 156
    EITHER_HEATER = 157
    SOLAR = 158
    FREEZE = 159


@dataclass
class PumpPreset:
    device_id: int
    setpoint: int = 30
    is_rpm: bool = False


@dataclass
class Pump:
    """Represents a pump connected to a pool controller."""

    id: int
    data: int
    type: PUMP_TYPE = None
    state: bool = False
    watts_now: int = 0
    rpm_now: int = 0
    flow_alarm: bool = False
    gpm_now: int = 0
    presets: dict[str, PumpPreset] = field(default_factory=dict)
    name: str = "Default Pump"
