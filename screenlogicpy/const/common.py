from enum import IntEnum

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


class ScreenLogicConnectionError(ScreenLogicException):
    pass


class ScreenLogicResponseError(ScreenLogicException):
    pass


class ScreenLogicLoginError(ScreenLogicException):
    pass


class SLIntEnum(IntEnum):
    @classmethod
    def parse(cls, value: str, default=0) -> "SLIntEnum":
        """Attempt to return and Enum from the provided string."""
        try:
            return (
                cls(value)
                if isinstance(value, int)
                else cls(int(value))
                if value.isdigit()
                else cls[value.replace(" ", "_").replace("'", "").upper()]
            )
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

    def _title(self) -> str:
        return self.name.replace("_", " ").title()

    @property
    def title(self) -> str:
        return self._title()


class DATA_REQUEST:
    CHEMISTRY = "chemistry"
    KEY_COLOR = "color"
    CONFIG = "config"
    PUMPS = "pumps"
    SCG = "scg"
    STATUS = "status"
    VERSION = "version"


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


class ON_OFF(SLIntEnum):
    OFF = 0
    ON = 1

    @classmethod
    def from_bool(cls, expression: bool):
        return cls.ON.value if expression else cls.OFF.value
