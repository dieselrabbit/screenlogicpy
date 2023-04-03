class ATTR:
    BODY_TYPE = "body_type"
    CIRCUIT_ID = "circuit_id"
    COLOR_MODE = "color_mode"
    COLOR_POSITION = "color_position"
    COLOR_SET = "color_set"
    COLOR_STAGGER = "color_stagger"
    DEFAULT_RUNTIME = "default_runtime"
    DELAY = "delay"
    DEVICE_ID = "device_id"
    DEVICE_TYPE = "device_type"
    ENUM_OPTIONS = "enum_options"
    FLAGS = "flags"
    FUNCTION = "function"
    INTERFACE = "interface"
    IS_RPM = "is_rpm"
    LIMIT = "limit"
    MAX_SETPOINT = "max_setpoint"
    MIN_SETPOINT = "min_setpoint"
    NAME = "name"
    NAME_INDEX = "name_index"
    PROGRESS = "progress"
    SETPOINT = "setpoint"
    STATE_TYPE = "state_type"
    STEP = "step"
    TEXT = "text"
    UNIT = "unit"
    VALUE = "value"


class DEVICE:
    ADAPTER = "adapter"
    CONTROLLER = "controller"
    BODY = "body"
    CIRCUIT = "circuit"
    INTELLICHEM = "intellichem"
    SCG = "scg"
    PUMP = "pump"


class KEY:
    ALARM = "alarm"
    COLOR = "color"
    COLOR_LIGHTS = "color_lights"
    CONFIGURATION = "configuration"
    EQUIPMENT = "equipment"
    ALERT = "alert"
    SENSOR = "sensor"


class VALUE:
    ACTIVE_ALARM = "active_alarm"
    AIR_TEMPERATURE = "air_temperature"
    CALCIUM_HARNESS = "calcium_harness"
    CIRCUIT_COUNT = "circuit_count"
    CLEANER_DELAY = "cleaner_delay"
    COLOR_COUNT = "color_count"
    CONTROLLER_DATA = "controller_data"
    CONTROLLER_ID = "controller_id"
    CONTROLLER_TYPE = "controller_type"
    COOL_SETPOINT = "cool_setpoint"
    CORROSIVE = "corrosive"
    CYA = "cya"
    DATA = "data"
    DEFAULT_CIRCUIT_NAME = "generic_circuit_name"
    DOSE_STATUS = "dose_status"
    FIRMWARE = "firmware"
    FLOW_ALARM = "flow_alarm"
    FREEZE_MODE = "freeze_mode"
    GPM_NOW = "gpm_now"
    HARDWARE_TYPE = "hardware_type"
    HEAT_MODE = "heat_mode"
    HEAT_SETPOINT = "heat_setpoint"
    HEAT_STATE = "heat_state"
    INTERFACE_TAB_FLAGS = "interface_tab_flags"
    IS_CELSIUS = "is_celsius"
    LAST_TEMPERATURE = "last_temperature"
    LIST = "list"
    MODEL = "model"
    OK = "ok"
    ORP = "orp"
    ORP_DOSING_STATE = "orp_dosing_state"
    ORP_HIGH_ALARM = "orp_high_alarm"
    ORP_LAST_DOSE_TIME = "orp_last_dose_time"
    ORP_LAST_DOSE_VOLUME = "orp_last_dose_volume"
    ORP_LIMIT = "orp_limit"
    ORP_LOW_ALARM = "orp_low_alarm"
    ORP_NOW = "orp_now"
    ORP_SETPOINT = "orp_setpoint"
    ORP_SUPPLY_ALARM = "orp_supply_alarm"
    ORP_SUPPLY_LEVEL = "orp_supply_level"
    PH = "ph"
    PH_DOSING_STATE = "ph_dosing_state"
    PH_HIGH_ALARM = "ph_high_alarm"
    PH_LAST_DOSE_TIME = "ph_last_dose_time"
    PH_LAST_DOSE_VOLUME = "ph_last_dose_volume"
    PH_LIMIT = "ph_limit"
    PH_LOCKOUT = "ph_lockout"
    PH_LOW_ALARM = "ph_low_alarm"
    PH_NOW = "ph_now"
    PH_PROBE_WATER_TEMP = "ph_probe_water_temp"
    PH_SETPOINT = "ph_setpoint"
    PH_SUPPLY_ALARM = "ph_supply_alarm"
    PH_SUPPLY_LEVEL = "ph_supply_level"
    POOL_DELAY = "pool_delay"
    POOL_SETPOINT = "pool_setpoint"
    PRESET = "preset"
    PROBE_FAULT_ALARM = "probe_fault_alarm"
    PROBE_IS_CELSIUS = "probe_is_celsius"
    PROGRESS_LIMIT = "progress_limit"
    PROGRESS_NOW = "progress_now"
    PUMP_TYPE = "pump_type"
    REMOTES = "remotes"
    RPM_NOW = "rpm_now"
    SALT_PPM = "salt_ppm"
    SALT_TDS_PPM = "salt_tds_ppm"
    SATURATION = "saturation"
    SCALING = "scaling"
    SCG_PRESENT = "scg_present"
    SHOW_ALARMS = "show_alarms"
    SPA_DELAY = "spa_delay"
    SPA_SETPOINT = "spa_setpoint"
    STATE = "state"
    STATUS = "status"
    SUPER_CHLOR_TIMER = "super_chlor_timer"
    TOTAL_ALKALINITY = "total_alkalinity"
    WATER_BALANCE = "water_balance"
    WATTS_NOW = "watts_now"


def UNKNOWN(offset: int) -> str:
    return f"unknown_at_offset_{offset:02}"
