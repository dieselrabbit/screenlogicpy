from dataclasses import dataclass, field

from .base import *

__all__ = (
    "GatewayConfig",
    "GatewayInfo",
    "Gateway",
)


class GatewayType(SLIntEnum):
    FULL = 1
    BRICK = 2
    BRICK_CHILD = 3
    APRILAIRE = 4
    PASSTHOUGH = 5
    ARM = 6
    X86 = 7


@dataclass
class GatewayInfo:
    address: str
    port: int
    type: int | None = None
    subtype: int | None = None
    name: str | None = None


@dataclass
class GatewayConfig:

    user_zip: str = ""
    user_latitude: float = 0.0
    user_longitude: float = 0.0
    architecture: str = ""
    style: str = ""


@dataclass
class Gateway(GatewayInfo):

    mac: str = ""
    firmware: str = ""
    config: GatewayConfig = field(default_factory=GatewayConfig)
