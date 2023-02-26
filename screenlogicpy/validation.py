from abc import ABC, abstractmethod
from .const import BODY_TYPE, COLOR_MODE, HEAT_MODE


class ValidationKeys:
    # ScreenLogic data
    HEAT_MODE = "heat_mode"
    HEAT_TEMP = "heat_temp"
    BODY = "body"
    CIRCUIT = "circuit"
    ON_OFF = "on_off_state"
    COLOR_MODE = "color_mode"
    SCG_SETPOINT = "scg_setpoint"
    SC_RUNTIME = "sc_runtime"
    PH_SETPOINT = "ph_setpoint"
    ORP_SETPOINT = "orp_setpoint"
    TOTAL_ALKALINITY = "total_alkalinity"
    CALCIUM_HARDNESS = "calcium_hardness"
    CYANURIC_ACID = "cyanuric_acid"
    SALT_TDS = "salt_tds_ppm"

    # screenlogicpy Settings
    MAX_RETRIES = "max_retries"
    CLIENT_ID = "client_id"


class BoundsValidation(ABC):
    def __init__(self, name: str = None) -> None:
        self.name = name

    @abstractmethod
    def is_valid(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def validate(self, value, hint: str = None) -> None:
        if not self.is_valid(value):
            param = "" if self.name is None else f"{self.name} "
            hint = "" if hint is None else f". {hint}"
            raise ValueError(f"Invalid {param}value: {value}{hint}")


class BoundsRange(BoundsValidation):
    def __init__(self, min, max, name: str = None) -> None:
        if min is not None and max is not None and type(min) != type(max):
            raise TypeError("Parameters 'min' and 'max' must be of the same type")
        self.min = min
        self.max = max
        super().__init__(name)

    def clamp(self, value):
        if self.min is not None and self.max is not None:
            return max(min(value, self.max), self.min)
        elif self.max is not None:
            return min(value, self.max)
        elif self.min is not None:
            return max(value, self.min)
        return value

    def is_valid(self, value) -> bool:
        if value is None:
            return False
        if self.min is not None and self.max is not None:
            return self.min <= value <= self.max
        elif self.max is not None:
            return value <= self.max
        elif self.min is not None:
            return self.min <= value
        return True

    def validate(self, value) -> None:
        super().validate(value, f"Must be between {self.min} and {self.max}")


class BoundsSet(BoundsValidation):
    def __init__(self, options, name: str = None) -> None:
        self.values = set(options)
        super().__init__(name)

    def is_valid(self, value) -> bool:
        return value in self.values

    def validate(self, value) -> None:
        super().validate(value, f"Must be in {self.values}")


Key = ValidationKeys
DATA_BOUNDS_CONST = {
    Key.ON_OFF: BoundsSet({0, 1}, Key.ON_OFF),
    Key.COLOR_MODE: BoundsSet(COLOR_MODE.NAME_FOR_NUM.keys(), Key.COLOR_MODE),
    Key.HEAT_MODE: BoundsSet(HEAT_MODE.NAME_FOR_NUM.keys(), Key.HEAT_MODE),
    # Valid ranges per documentation
    Key.SCG_SETPOINT: {
        BODY_TYPE.POOL: BoundsRange(0, 100, f"{Key.SCG_SETPOINT}_pool"),
        BODY_TYPE.SPA: BoundsRange(0, 100, f"{Key.SCG_SETPOINT}_spa"),
    },
    Key.SC_RUNTIME: BoundsRange(1, 72, Key.SC_RUNTIME),
    Key.ORP_SETPOINT: BoundsRange(400, 800, Key.ORP_SETPOINT),
    Key.PH_SETPOINT: BoundsRange(7.2, 7.6, Key.PH_SETPOINT),
    # Valid settable ranges in IntelliChem
    Key.CALCIUM_HARDNESS: BoundsRange(25, 800, Key.CALCIUM_HARDNESS),
    Key.CYANURIC_ACID: BoundsRange(0, 201, Key.CYANURIC_ACID),
    Key.SALT_TDS: BoundsRange(500, 6500, Key.SALT_TDS),
    Key.TOTAL_ALKALINITY: BoundsRange(25, 800, Key.TOTAL_ALKALINITY),
}

SETTING_BOUNDS_CONST = {
    Key.MAX_RETRIES: BoundsRange(0, 5, Key.MAX_RETRIES),
    Key.CLIENT_ID: BoundsRange(32767, 65535, Key.CLIENT_ID),
}


class DATA_BOUNDS:
    ON_OFF = BoundsSet({0, 1}, "on_off_state")

    # Valid ranges per documentation
    COLOR_MODE = BoundsSet(COLOR_MODE.NAME_FOR_NUM.keys(), "color_mode")
    HEAT_MODE = BoundsSet(HEAT_MODE.NAME_FOR_NUM.keys(), "heat_mode")
    SCG_SETPOINT_POOL = BoundsRange(0, 100, "scg_setpoint_pool")
    SCG_SETPOINT_SPA = BoundsRange(0, 100, "scg_setpoint_spa")
    SC_RUNTIME = BoundsRange(1, 72, "sc_runtime")
    CHEM_SETPOINT_ORP = BoundsRange(400, 800, "orp_setpoint")
    CHEM_SETPOINT_PH = BoundsRange(7.2, 7.6, "ph_setpoint")

    # Valid ranges as settable on IntelliChem controller
    CHEM_CALCIUM_HARDNESS = BoundsRange(25, 800, "calcium_hardness")
    CHEM_CYANURIC_ACID = BoundsRange(0, 201, "cyanuric_acid")
    CHEM_SALT_TDS = BoundsRange(500, 6500, "salt_tds_ppm")
    CHEM_TOTAL_ALKALINITY = BoundsRange(25, 800, "total_alkalinity")

    # Placeholders that should be overridden with actual values from system config
    CIRCUIT = BoundsSet({500, 505}, "circuit")
    BODY = BoundsSet({0, 1}, "body")
    HEAT_TEMP = {
        0: BoundsRange(40, 104, "heat_temp_pool"),
        1: BoundsRange(40, 104, "heat_temp_spa"),
    }


class SETTINGS_BOUNDS:
    MAX_RETRIES = BoundsRange(0, 5, "max_retries")
    CLIENT_ID = BoundsRange(32767, 65535, "client_id")
