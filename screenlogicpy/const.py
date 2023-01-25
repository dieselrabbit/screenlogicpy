import struct

ADD_UNKNOWN_VALUES = False

SL_GATEWAY_IP = "ip"
SL_GATEWAY_PORT = "port"
SL_GATEWAY_TYPE = "gtype"
SL_GATEWAY_SUBTYPE = "gsubtype"
SL_GATEWAY_NAME = "name"


class ScreenLogicError(Exception):
    pass


class ScreenLogicWarning(Exception):
    pass


class MESSAGE:
    COM_TIMEOUT = 5
    HEADER_FORMAT = "<HHI"
    HEADER_LENGTH = struct.calcsize(HEADER_FORMAT)


# Some of the message codes
class CODE:
    MSG_CODE_1 = 0
    UNKNOWN_ANSWER = 13
    CHALLENGE_QUERY = 14
    CHALLENGE_ANSWER = CHALLENGE_QUERY + 1
    LOCALLOGIN_QUERY = 27
    LOCALLOGIN_ANSWER = LOCALLOGIN_QUERY + 1
    VERSION_QUERY = 8120
    VERSION_ANSWER = VERSION_QUERY + 1
    POOLSTATUS_QUERY = 12526
    POOLSTATUS_ANSWER = POOLSTATUS_QUERY + 1
    SETHEATTEMP_QUERY = 12528
    SETHEATTEMP_ANSWER = SETHEATTEMP_QUERY + 1
    BUTTONPRESS_QUERY = 12530
    BUTTONPRESS_ANSWER = BUTTONPRESS_QUERY + 1
    CTRLCONFIG_QUERY = 12532
    CTRLCONFIG_ANSWER = CTRLCONFIG_QUERY + 1
    SETHEATMODE_QUERY = 12538
    SETHEATMODE_ANSWER = SETHEATMODE_QUERY + 1
    SETCOOLTEMP_QUERY = 12590
    SETCOOLTEMP_ANSWER = SETCOOLTEMP_QUERY + 1
    GATEWAYDATA_QUERY = 18003
    GATEWAYDATA_ANSWER = GATEWAYDATA_QUERY + 1
    CONTROLLER_QUERY = 12532
    CONTROLLER_ANSWER = CONTROLLER_QUERY + 1
    EQUIPMENT_QUERY = 12566
    EQUIPMENT_ANSWER = EQUIPMENT_QUERY + 1
    PUMPSTATUS_QUERY = 12584
    PUMPSTATUS_ANSWER = PUMPSTATUS_QUERY + 1
    LIGHTCOMMAND_QUERY = 12556
    LIGHTCOMMAND_ANSWER = LIGHTCOMMAND_QUERY + 1
    CHEMISTRY_QUERY = 12592
    CHEMISTRY_ANSWER = CHEMISTRY_QUERY + 1
    SETCHEMDATA_QUERY = 12594
    SETCHEMDATA_ANSWER = SETCHEMDATA_QUERY + 1
    SCGCONFIG_QUERY = 12572
    SCGCONFIG_ANSWER = SCGCONFIG_QUERY + 1
    SETSCG_QUERY = 12576
    SETSCG_ANSWER = SETSCG_QUERY + 1


class DATA:
    KEY_ALERTS = "alerts"
    KEY_BODIES = "bodies"
    KEY_CHEMISTRY = "chemistry"
    KEY_CIRCUITS = "circuits"
    KEY_COLORS = "colors"
    KEY_CONFIG = "config"
    KEY_NOTIFICATIONS = "notifications"
    KEY_PUMPS = "pumps"
    KEY_SCG = "scg"
    KEY_SENSORS = "sensors"


class BODY_TYPE:
    POOL = 0
    SPA = 1

    NAME_FOR_NUM = {POOL: "Pool", SPA: "Spa"}

    NUM_FOR_NAME = {name: num for num, name in NAME_FOR_NUM.items()}


class ON_OFF:
    OFF = 0
    ON = 1

    NAME_FOR_NUM = {OFF: "Off", ON: "On"}

    NUM_FOR_NAME = {name: num for num, name in NAME_FOR_NUM.items()}

    @classmethod
    def from_bool(cls, expresson: bool):
        return cls.ON if expresson else cls.OFF


class HEAT_MODE:
    OFF = 0
    SOLAR = 1
    SOLAR_PREFERRED = 2
    HEATER = 3
    DONT_CHANGE = 4

    NAME_FOR_NUM = {
        OFF: "Off",
        SOLAR: "Solar",
        SOLAR_PREFERRED: "Solar Preferred",
        HEATER: "Heater",
        DONT_CHANGE: "Don't Change",
    }

    NUM_FOR_NAME = {name: num for num, name in NAME_FOR_NUM.items()}


class COLOR_MODE:
    OFF = 0
    ON = 1
    SET = 2
    SYNC = 3
    SWIM = 4
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
    NEXT = 19
    RESET = 20
    HOLD = 21

    NAME_FOR_NUM = {
        OFF: "All Off",
        ON: "All On",
        SET: "Color Set",
        SYNC: "Color Sync",
        SWIM: "Color Swim",
        PARTY: "Party",
        ROMANCE: "Romance",
        CARIBBEAN: "Caribbean",
        AMERICAN: "American",
        SUNSET: "Sunset",
        ROYAL: "Royal",
        SAVE: "Save",
        RECALL: "Recall",
        BLUE: "Blue",
        GREEN: "Green",
        RED: "Red",
        WHITE: "White",
        MAGENTA: "Magenta",
        THUMPER: "Thumper",
        NEXT: "Next Mode",
        RESET: "Reset",
        HOLD: "Hold",
    }

    NUM_FOR_NAME = {name: num for num, name in NAME_FOR_NUM.items()}


class RANGE:
    MIN = 0
    MAX = 1

    NAME_FOR_NUM = {MIN: "Minimum", MAX: "Maximum"}


class DEVICE_TYPE:
    ALARM = "alarm"
    DURATION = "duration"
    ENERGY = "energy"
    POWER = "power"
    TEMPERATURE = "temperature"
    VOLUME = "volume"


class UNIT:
    # Chemistry
    PARTS_PER_MILLION = "ppm"
    PERCENT = "%"
    PH = "pH"
    SATURATION_INDEX = "lsi"

    # Electrical
    MILLIVOLT = "mV"
    WATT = "W"

    # Flow
    GALLONS_PER_MINUTE = "gpm"

    # Speed
    REVOLUTIONS_PER_MINUTE = "rpm"

    # Temperature
    CELSIUS = "\xb0C"
    FAHRENHEIT = "\xb0F"

    # Time
    HOUR = "hr"
    SECOND = "sec"

    # Volume
    MILLILITER = "mL"


class EQUIPMENT:
    CONTROLLER_HARDWARE = {
        0: {0: "IntelliTouch i5+3S"},
        1: {0: "IntelliTouch i7+3"},
        2: {0: "IntelliTouch i9+3"},
        3: {0: "IntelliTouch i5+3S"},
        4: {0: "IntelliTouch i9+3S"},
        5: {0: "IntelliTouch i10+3D", 1: "IntelliTouch i10X"},
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

    PUMP_TYPE = {
        0: "None",
        1: "Intelliflo VF",
        2: "Intelliflo VS",
        3: "Intelliflo VSF",
    }

    FLAG_SOLAR = 0x1
    FLAG_SOLAR_AS_HEAT_PUMP = 0x2
    FLAG_CHLORINATOR = 0x4
    FLAG_SPA_SIDE_REMOTE = 0x20
    FLAG_COOLING = 0x800
    FLAG_INTELLICHEM = 0x8000


class CIRCUIT_FUNCTION:
    # Known circuit functions.
    GENERIC = 0
    SPA = 1
    POOL = 2
    MASTER_CLEANER = 5
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

    GROUP_CORE = [
        SPA,
        POOL,
    ]

    GROUP_LIGHTING = [
        LIGHT,
        DIMMER,
        SAM_LIGHT,
        SAL_LIGHT,
        PHOTONGEN,
        COLOR_WHEEL,
        INTELLIBRITE,
        MAGICSTREAM,
    ]


class INTERFACE_GROUP:
    # Known interface groups
    POOL = 0
    SPA = 1
    FEATURES = 2
    LIGHTS = 3


class CHEMISTRY:
    FLAG_ALARM_FLOW = 0x01
    FLAG_ALARM_PH = 0x06
    FLAG_ALARM_ORP = 0x18
    FLAG_ALARM_PH_SUPPLY = 0x20
    FLAG_ALARM_ORP_SUPPLY = 0x40
    FLAG_ALARM_PROBE_FAULT = 0x80

    # Unconfirmed
    FLAG_STATUS_NORMAL = 0x01
    FLAG_STATUS_IDEAL = 0x02
    FLAG_STATUS_CORROSIVE = 0x04
    FLAG_STATUS_SCALING = 0x08

    MASK_STATUS_ORP_DOSE_TYPE = 0x03
    MASK_STATUS_PH_DOSE_TYPE = 0x0C
    MASK_STATUS_PH_DOSING = 0x30
    MASK_STATUS_ORP_DOSING = 0xC0

    FLAG_WARNING_PH_LOCKOUT = 0x01
    FLAG_WARNING_PH_LIMIT = 0x02
    FLAG_WARNING_ORP_LIMIT = 0x04
    FLAG_WARNING_INVALID_SETUP = 0x08
    FLAG_WARNING_CHLORINATOR_COMM_ERROR = 0x10

    FLAG_FLAGS_FLOW_DELAY = 0x02
    FLAG_FLAGS_INTELLICHLOR = 0x04
    FLAG_FLAGS_MANUAL_DOSING = 0x08
    FLAG_FLAGS_USE_CHLORINATOR = 0x10
    FLAG_FLAGS_ADVANCED_DISPLAY = 0x20
    FLAG_FLAGS_PH_SUPPLY_TYPE = 0x40
    FLAG_FLAGS_COMMS_LOST = 0x80  # ?

    # Valid ranges listed in IntelliChem documentation
    RANGE_PH_SETPOINT = {RANGE.MIN: 7.2, RANGE.MAX: 7.6}
    RANGE_ORP_SETPOINT = {RANGE.MIN: 400, RANGE.MAX: 800}


class CHEM_DOSING_STATE:
    DOSING = 0
    MIXING = 1
    MONITORING = 2

    NAME_FOR_NUM = {DOSING: "Dosing", MIXING: "Mixing", MONITORING: "Monitoring"}
    NUM_FOR_NAME = {name: num for num, name in NAME_FOR_NUM.items()}


class CHEM_DOSE_TYPE:
    class ORP:
        NONE = 0
        CHLORINE = 1
        SCG = 2  # ?

        NAME_FOR_NUM = {
            NONE: "None",
            CHLORINE: "Chlorine",
            SCG: "Salt Chlorine Generator",
        }
        NUM_FOR_NAME = {name: num for num, name in NAME_FOR_NUM.items()}

    class PH:
        NONE = 0
        ACID = 1
        CO2 = 2

        NAME_FOR_NUM = {NONE: "None", ACID: "Acid", CO2: "CO2"}
        NUM_FOR_NAME = {name: num for num, name in NAME_FOR_NUM.items()}


class SCG:
    LIMIT_FOR_BODY = {BODY_TYPE.POOL: 100, BODY_TYPE.SPA: 100}
    MAX_SC_RUNTIME = 72


GENERIC_CIRCUIT_NAMES = [
    *[f"Aux {num}" for num in range(1, 8)],  # Last number is 7
    "AuxEx",
    *[f"Feature {num}" for num in range(1, 9)],  # Last number is 8
]

DEFAULT_CIRCUIT_NAMES = ["Spa", "Pool", *GENERIC_CIRCUIT_NAMES]


# COLOR_MODES_* may not be complete
COLOR_MODES_GENERIC = {num: COLOR_MODE.NAME_FOR_NUM[num] for num in [0, 1]}

COLOR_MODES_COLORS = {num: COLOR_MODE.NAME_FOR_NUM[num] for num in [13, 14, 15, 16, 17]}

COLOR_MODES_SAM = {
    **COLOR_MODES_GENERIC,
    **{num: COLOR_MODE.NAME_FOR_NUM[num] for num in [2, 3, 4]},
    **COLOR_MODES_COLORS,
}

COLOR_MODES_INTELLIBRITE = {
    **COLOR_MODES_GENERIC,
    **COLOR_MODES_SAM,
    **{num: COLOR_MODE.NAME_FOR_NUM[num] for num in [5, 6, 7, 8, 9, 10, 11, 12]},
    **COLOR_MODES_COLORS,
}

COLOR_MODES_MAGICSTREAM = {
    **COLOR_MODES_GENERIC,
    **{num: COLOR_MODE.NAME_FOR_NUM[num] for num in [18, 19, 20, 21]},
}
