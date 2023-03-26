from enum import IntEnum, IntFlag
import struct

CLIENT_ID = 49151

# Protocol adapter closes the connection if it doesn't hear
# from the client for 10 minutes, but we'll go ahead an make
# sure it hears something from us well before then.
COM_KEEPALIVE = 300  # Seconds = 5 minutes

SL_GATEWAY_IP = "ip"
SL_GATEWAY_PORT = "port"
SL_GATEWAY_TYPE = "gtype"
SL_GATEWAY_SUBTYPE = "gsubtype"
SL_GATEWAY_NAME = "name"


class ScreenLogicException(Exception):
    """Common class for all ScreenLogic exceptions."""

    def __init__(self, message: str, *args: object) -> None:
        self.msg = message
        super().__init__(*args)


class ScreenLogicWarning(ScreenLogicException):
    pass


class ScreenLogicError(ScreenLogicException):
    pass


class ScreenLogicRequestError(ScreenLogicException):
    pass


class SLIntEnum(IntEnum):
    @classmethod
    def parse(cls, value: str, default=0) -> "SLIntEnum":
        """Attempt to return and Enum from the provided string."""
        try:
            if value.isdigit():  # isinstance(value, int) or
                return cls(int(value))
            else:
                return cls[value.replace(" ", "_").replace("'", "").upper()]
        except (KeyError, ValueError):
            return None if default is None else cls(default)

    @classmethod
    def parsable(cls) -> tuple:
        """Return a tuple of all parsable values."""
        out = []
        for member in cls:
            out.append(str(member.value))
            out.append(member.name.lower())
        return tuple(out)

    @property
    def title(self) -> str:
        return self.name.replace("_", " ").title().replace("Dont", "Don't")


class MESSAGE:
    COM_MAX_RETRIES = 1
    COM_RETRY_WAIT = 1
    COM_TIMEOUT = 2
    HEADER_FORMAT = "<HHI"
    HEADER_LENGTH = struct.calcsize(HEADER_FORMAT)


# Some of the message codes
# ANSWERS are QUERY + 1
class CODE:
    MSG_CODE_1 = 0
    ERROR_LOGIN_REJECTED = 13
    CHALLENGE_QUERY = 14
    PING_QUERY = 16
    LOCALLOGIN_QUERY = 27
    ERROR_INVALID_REQUEST = 30
    ERROR_BAD_PARAMETER = 31  # Actually bad parameter?
    VERSION_QUERY = 8120
    WEATHER_FORECAST_CHANGED = 9806
    WEATHER_FORECAST_QUERY = 9807
    STATUS_CHANGED = 12500
    COLOR_UPDATE = 12504
    CHEMISTRY_CHANGED = 12505
    ADD_CLIENT_QUERY = 12522
    REMOVE_CLIENT_QUERY = 12524
    POOLSTATUS_QUERY = 12526
    SETHEATTEMP_QUERY = 12528
    BUTTONPRESS_QUERY = 12530
    CTRLCONFIG_QUERY = 12532
    SETHEATMODE_QUERY = 12538
    LIGHTCOMMAND_QUERY = 12556
    SETCHEMDATA_QUERY = 12594
    EQUIPMENT_QUERY = 12566
    SCGCONFIG_QUERY = 12572
    SETSCG_QUERY = 12576
    PUMPSTATUS_QUERY = 12584
    SETCOOLTEMP_QUERY = 12590
    CHEMISTRY_QUERY = 12592
    GATEWAYDATA_QUERY = 18003


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


class RANGE:
    MIN = 0
    MAX = 1

    NAME_FOR_NUM = {MIN: "Minimum", MAX: "Maximum"}


class DEVICE_TYPE:
    ALARM = "alarm"
    DURATION = "duration"
    ENERGY = "energy"
    ENUM = "enum"
    POWER = "power"
    TEMPERATURE = "temperature"
    VOLUME = "volume"


class STATE_TYPE:
    MEASUREMENT = "measurement"
    TOTAL = "total"
    TOTAL_INCREASING = "total_increasing"


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

    @classmethod
    def ControllerModel(cls, controller_type: int, hardware_type: int) -> str:
        try:
            return cls.CONTROLLER_HARDWARE[controller_type][hardware_type]
        except KeyError:
            return f"Unknown C:{controller_type} H:{hardware_type}"

    class FLAG(IntFlag):
        """Known equipment flags."""

        SOLAR = 0x1
        SOLAR_AS_HEAT_PUMP = 0x2
        CHLORINATOR = 0x4
        SPA_SIDE_REMOTE = 0x20
        ULTRATEMP_THEMALFLO = 0x200
        HAS_COOLING = 0x800
        INTELLICHEM = 0x8000


class BODY_TYPE(SLIntEnum):
    POOL = 0
    SPA = 1


class CHEMISTRY:
    class ALARM(IntFlag):
        FLOW = 0x01
        PH_HIGH = 0x02
        PH_LOW = 0x04
        ORP_HIGH = 0x08
        ORP_LOW = 0x10
        PH_SUPPLY = 0x20
        ORP_SUPPLY = 0x40
        PROBE_FAULT = 0x80

    # Unconfirmed, unused.
    # FLAG_STATUS_NORMAL = 0x01
    # FLAG_STATUS_IDEAL = 0x02
    # FLAG_STATUS_CORROSIVE = 0x04
    # FLAG_STATUS_SCALING = 0x08

    class DOSE:
        class MASK(IntFlag):
            ORP_TYPE = 0x03
            PH_TYPE = 0x0C
            PH_STATE = 0x30
            ORP_STATE = 0xC0

        class STATE(SLIntEnum):
            DOSING = 0
            MIXING = 1
            MONITORING = 2

        class TYPE:
            class ORP(SLIntEnum):
                NONE = 0
                CHLORINE = 1
                SCG = 2  # ?

            class PH(SLIntEnum):
                NONE = 0
                ACID = 1
                CO2 = 2

    class ALERT(IntFlag):
        PH_LOCKOUT = 0x01
        PH_LIMIT = 0x02
        ORP_LIMIT = 0x04
        INVALID_SETUP = 0x08
        CHLORINATOR_COMM_ERROR = 0x10

    class FLAG(IntFlag):
        FLOW_DELAY = 0x02
        INTELLICHLOR = 0x04
        PH_PRIORITY = 0x08
        USE_CHLORINATOR = 0x10
        ADVANCED_DISPLAY = 0x20
        PH_SUPPLY_TYPE = 0x40
        COMMS_LOST = 0x80  # ?

    # Valid ranges listed in IntelliChem documentation
    RANGE_PH_SETPOINT = {RANGE.MIN: 7.2, RANGE.MAX: 7.6}
    RANGE_ORP_SETPOINT = {RANGE.MIN: 400, RANGE.MAX: 800}


class CIRCUIT:
    class FUNCTION(SLIntEnum):
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

    class INTERFACE(SLIntEnum):
        # Known interface groups
        POOL = 0
        SPA = 1
        FEATURES = 2
        COLOR_LIGHTS = 3  # ?
        LIGHTS = 4
        DONT_SHOW = 5


"""
    GROUP_CORE = {
        SPA,
        POOL,
    }

    GROUP_LIGHTS_BASIC = {
        LIGHT,
        DIMMER,
    }

    GROUP_LIGHTS_COLOR = {
        SAM_LIGHT,
        SAL_LIGHT,
        PHOTONGEN,
        COLOR_WHEEL,
        INTELLIBRITE,
        MAGICSTREAM,
    }

    GROUP_LIGHTS_ALL = {
        *GROUP_LIGHTS_BASIC,
        *GROUP_LIGHTS_COLOR,
    }
 """


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


class ON_OFF(SLIntEnum):
    OFF = 0
    ON = 1

    @classmethod
    def from_bool(cls, expression: bool):
        return cls.ON.value if expression else cls.OFF.value


class HEAT_MODE(SLIntEnum):
    OFF = 0
    SOLAR = 1
    SOLAR_PREFERRED = 2
    HEATER = 3
    DONT_CHANGE = 4


class SCG:
    LIMIT_FOR_BODY = {BODY_TYPE.POOL: 100, BODY_TYPE.SPA: 100}
    MAX_SC_RUNTIME = 72


GENERIC_CIRCUIT_NAMES = [
    *[f"Aux {num}" for num in range(1, 25)],  # Last number is 24
    "AuxEx",
    *[f"Feature {num}" for num in range(1, 9)],  # Last number is 8
]

DEFAULT_CIRCUIT_NAMES = ["Spa", "Pool", *GENERIC_CIRCUIT_NAMES]


""" # COLOR_MODES_* may not be complete
COLOR_MODES_GENERIC = {
    num: COLOR_MODE.NAME_FOR_NUM[num]
    for num in [
        COLOR_MODE.ALL_OFF,
        COLOR_MODE.ALL_ON,
    ]
}

COLOR_MODES_COLORS = {
    num: COLOR_MODE.NAME_FOR_NUM[num]
    for num in [
        COLOR_MODE.BLUE,
        COLOR_MODE.GREEN,
        COLOR_MODE.RED,
        COLOR_MODE.WHITE,
        COLOR_MODE.MAGENTA,
    ]
}

COLOR_MODES_SAM = {
    **COLOR_MODES_GENERIC,
    **{
        num: COLOR_MODE.NAME_FOR_NUM[num]
        for num in [
            COLOR_MODE.COLOR_SET,
            COLOR_MODE.COLOR_SYNC,
            COLOR_MODE.COLOR_SWIM,
        ]
    },
    **COLOR_MODES_COLORS,
}

COLOR_MODES_INTELLIBRITE = {
    **COLOR_MODES_GENERIC,
    **COLOR_MODES_SAM,
    **{
        num: COLOR_MODE.NAME_FOR_NUM[num]
        for num in [
            COLOR_MODE.PARTY,
            COLOR_MODE.ROMANCE,
            COLOR_MODE.CARIBBEAN,
            COLOR_MODE.AMERICAN,
            COLOR_MODE.SUNSET,
            COLOR_MODE.ROYAL,
            COLOR_MODE.SAVE,
            COLOR_MODE.RECALL,
        ]
    },
    **COLOR_MODES_COLORS,
}

COLOR_MODES_MAGICSTREAM = {
    **COLOR_MODES_GENERIC,
    **{
        num: COLOR_MODE.NAME_FOR_NUM[num]
        for num in [
            COLOR_MODE.THUMPER,
            COLOR_MODE.NEXT_MODE,
            COLOR_MODE.RESET,
            COLOR_MODE.HOLD,
        ]
    },
}
 """
