from dataclasses import dataclass, field

from .devices import *

__all__ = ("EquipmentConfig", "SystemConfig", "System")


@dataclass
class EquipmentConfig:
    version_array: list = field(default_factory=list)
    speed_array: list = field(default_factory=list)
    valve_array: list = field(default_factory=list)
    remote_array: list = field(default_factory=list)
    sensor_array: list = field(default_factory=list)
    delay_array: list = field(default_factory=list)
    macro_array: list = field(default_factory=list)
    misc_array: list = field(default_factory=list)
    light_array: list = field(default_factory=list)
    flow_array: list = field(default_factory=list)
    sg_array: list = field(default_factory=list)
    spaflow_array: list = field(default_factory=list)


@dataclass
class SystemConfig:

    body_defs: dict[str, BodyTypeDefinition] = field(default_factory=dict)
    equipment: EquipmentConfig = field(default_factory=EquipmentConfig)


@dataclass
class System:

    gateway: Gateway | None = None
    controller: Controller = field(default_factory=Controller)
    pumps: dict[str, Pump] = field(default_factory=dict)
    heaters: dict[str, Heater] = field(default_factory=dict)
    chlorinator: SaltChlorineGenerator | None = None
    chemistry: IntelliChem | None = None
    config: SystemConfig = field(default_factory=SystemConfig)
    unknown_values: dict[int, dict[int, UnknownValue]] = field(default_factory=dict)
