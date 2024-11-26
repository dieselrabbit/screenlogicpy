from dataclasses import dataclass, field

from .base import *


__all__ = ("SaltChlorineGenerator",)


class STATUS_FLAG(SLIntEnum):
    SCG_ACTIVE = 0x01

    # Assumptions
    SALT_VERY_LOW = 0x10
    SALT_LOW = 0x20
    SALT_OK = 0x40
    SALT_HIGH = 0x80

    # Maybe
    ICHEM_IN_CONTROL = 0x8000


class STATE_FLAG(SLIntEnum):
    SUPER_CHLORINATE = 0x01


class SCG_RANGE:
    POOL_SETPOINT = SLValueRange(0, 100)
    SPA_SETPOINT = SLValueRange(0, 100)
    SUPER_CHLOR_RT = SLValueRange(0, 72)


RANGE_FOR_BODY = {
    BODY_TYPE.POOL: SCG_RANGE.POOL_SETPOINT,
    BODY_TYPE.SPA: SCG_RANGE.SPA_SETPOINT,
}


@dataclass
class SCGConfig:

    is_present: bool = False
    pool_range: SCG_RANGE = SCG_RANGE.POOL_SETPOINT
    spa_range: SCG_RANGE = SCG_RANGE.SPA_SETPOINT


@dataclass
class SaltChlorineGenerator:
    """Represents a SCG device connected to a pool controller or IntelliChem."""

    config: SCGConfig = field(default_factory=SCGConfig)
    state: bool = False
    pool_setpoint: int = None
    spa_setpoint: int = None
    salt_ppm: int = 0
    state_flags: STATE_FLAG = 0
    super_chlorinate_time: int = 0

    @property
    def super_chlorinate(self) -> bool:
        return STATE_FLAG.SUPER_CHLORINATE in self.state_flags

    def set_scg_config(
        self,
        *,
        pool_setpoint: int | None = None,
        spa_setpoint: int | None = None,
        super_chlorinate: int | None = None,
        super_chlor_timer: int | None = None,
    ) -> None:
        pass
