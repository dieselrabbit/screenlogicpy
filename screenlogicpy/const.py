import struct

SL_GATEWAY_IP = "ip"
SL_GATEWAY_PORT = "port"
SL_GATEWAY_TYPE = "gtype"
SL_GATEWAY_SUBTYPE = "gsubtype"
SL_GATEWAY_NAME = "name"


class ScreenLogicError(Exception):
    pass


class ScreenLogicWarning(Exception):
    pass


class header:
    fmt = "<HHI"
    length = struct.calcsize(fmt)


# Some of the message codes
class code:
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
    SCGCONFIG_QUERY = 12572
    SCGCONFIG_ANSWER = SCGCONFIG_QUERY + 1


class DATA:
    KEY_ALERTS = "alerts"
    KEY_BODIES = "bodies"
    KEY_CHEMISTRY = "chemistry"
    KEY_CIRCUITS = "circuits"
    KEY_COLORS = "colors"
    KEY_CONFIG = "config"
    KEY_NOTIFICATIONS = "notifications"
    KEY_PUMPS = "pumps"
    KEY_SENSORS = "sensors"


# class mapping:
#    BODY_TYPE  = ['Pool', 'Spa']

#    HEAT_MODE  = ['Off', 'Solar',
#                  "Solar Preferred",
#                  'Heat', "Don't Change"]

#    ON_OFF     = ['Off', 'On']

#    COLOR_MODE = ['Off', 'On',
#                  'Set', 'Sync',
#                  'Swim', 'Party',
#                  'Romantic', 'Caribbean',
#                  'American', 'Sunset',
#                  'Royal', 'Save',
#                  'Recall', 'Blue',
#                  'Green', 'Red',
#                  'White', 'Magenta',
#                  'Thumper', 'Next',
#                  'Reset', 'Hold']


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


class DEVICE_TYPE:
    ALARM = "alarm"
    ENERGY = "energy"
    TEMPERATURE = "temperature"


class UNIT:
    CELSIUS = "\xb0C"
    FAHRENHEIT = "\xb0F"


class EQUIPMENT:
    CONTROLLER_HARDWARE = {
        0: {0: "IntelliTouch i5+3S"},
        1: {0: "IntelliTouch i7+3"},
        2: {0: "IntelliTouch i9+3"},
        3: {0: "IntelliTouch i5+3S"},
        4: {0: "IntelliTouch i9+3S"},
        5: {0: "IntelliTouch i10+3D"},
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
        1: "Intelliflow VF",
        2: "Intelliflow VS",
        3: "Intelliflow VSF",
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
    MAGICSTREAM = 8  # ?
    SPILLWAY = 14
    INTELLIBRITE = 16


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

    FLAG_STATUS_CORROSIVE = 0x01
    FLAG_STATUS_SCALING = 0x02
    FLAG_STATUS_PH_DOSING = 0x30
    FLAG_STATUS_ORP_DOSING = 0xC0

    FLAG_WARNING_PH_LOCKOUT = 0x01
    FLAG_WARNING_PH_LIMIT = 0x02
    FLAG_WARNING_ORP_LIMIT = 0x04


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
