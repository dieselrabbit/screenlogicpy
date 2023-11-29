from .const import BODY_TYPE, COLOR_MODE, HEAT_MODE


class DataValidationKey:
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


class DataValidation:
    DV_KEY = DataValidationKey

    # These shouldn't change between pool configurations
    _static_bounds = {
        DV_KEY.ON_OFF: {0, 1},
        # Valid ranges per documentation
        DV_KEY.SCG_SETPOINT: {
            BODY_TYPE.POOL: (0, 100),
            BODY_TYPE.SPA: (0, 100),
        },
        DV_KEY.SC_RUNTIME: (1, 72),
        DV_KEY.ORP_SETPOINT: (400, 800),
        DV_KEY.PH_SETPOINT: (7.2, 7.6),
        # Valid ranges as settable on IntelliChem controller
        DV_KEY.CALCIUM_HARDNESS: (25, 800),
        DV_KEY.CYANURIC_ACID: (0, 201),
        DV_KEY.SALT_TDS: (500, 6500),
        DV_KEY.TOTAL_ALKALINITY: (25, 800),
    }

    # Placeholders that should be overridden with actual values from pool config
    _config_bounds = {
        DV_KEY.BODY: {0, 1},
        DV_KEY.CIRCUIT: {500, 505},
        DV_KEY.COLOR_MODE: set(COLOR_MODE.NAME_FOR_NUM.keys()),
        DV_KEY.HEAT_MODE: set(HEAT_MODE.NAME_FOR_NUM.keys()),
        DV_KEY.HEAT_TEMP: {
            0: (40, 104),
            1: (40, 104),
        },
    }

    # Specific to screenlogicpy
    _app_bounds = {
        DV_KEY.MAX_RETRIES: (0, 5),
        DV_KEY.CLIENT_ID: (32767, 65535),
    }

    def __init__(self) -> None:
        self._data_bounds = {
            **self._static_bounds,
            **self._app_bounds,
            **self._config_bounds,
        }

    def get_bounds(self, key):
        if isinstance(key, tuple):
            return self._data_bounds[key[0]][key[1]]
        elif isinstance(key, str):
            return self._data_bounds[key]
        else:
            raise TypeError(f"Invalid data validation key: {key}")

    def is_valid(self, key, value) -> bool:
        bounds = self.get_bounds(key)
        if isinstance(bounds, set):
            return self._is_valid_set(bounds, value)
        elif isinstance(bounds, tuple):
            return self._is_valid_range(bounds, value)
        return False

    def _is_valid_range(self, bounds, value) -> bool:
        if value is None:
            return False
        bounds_min, bounds_max = bounds
        if bounds_min is not None and bounds_max is not None:
            return bounds_min <= value <= bounds_max
        elif bounds_max is not None:
            return value <= bounds_max
        elif bounds_min is not None:
            return bounds_min <= value
        return True

    def _is_valid_set(self, bounds, value) -> bool:
        return value in bounds

    def validate(self, key, value):
        bounds = self.get_bounds(key)
        if not self.is_valid(key, value):
            raise ValueError(f"{key} {value} not in {bounds}")

    def clamp(self, key, value):
        bounds = self.get_bounds(key)
        if not isinstance(bounds, tuple):
            raise ValueError(f"{key} not a min/max.")
        bounds_min, bounds_max = bounds
        if bounds_min is not None and bounds_max is not None:
            return max(min(value, bounds_max), bounds_min)
        elif bounds_max is not None:
            return min(value, bounds_max)
        elif bounds_min is not None:
            return max(value, bounds_min)
        return value

    def update(self, key, new_bounds) -> None:
        bounds = self.get_bounds(key)
        if not isinstance(new_bounds, type(bounds)):
            raise TypeError(
                f"New bounds ({type(new_bounds)}) does not match existing bounds ({type(bounds)})"
            )
        if isinstance(key, tuple):
            self._config_bounds[key[0]][key[1]] = new_bounds
        elif isinstance(key, str):
            self._config_bounds[key] = new_bounds
        else:
            raise TypeError(f"Invalid data validation key: {key}")
        self._data_bounds.update(self._config_bounds)
