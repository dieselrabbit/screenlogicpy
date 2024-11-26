import importlib
import inspect
import struct
from datetime import datetime, timezone
from typing import Any

from ..devices import SLIntEnum, UnknownValue
from ..system import System

__all__ = (
    "HEADER_FORMAT",
    "HEADER_LENGTH",
    "MessageCode",
    "Payload",
    "AbstractMessage",
    "BaseRequest",
    "BaseResponse",
    "BadParameterResponse",
    "InvalidRequestResponse",
    "LoginRejectedResponse",
    "encode_datetime",
    "encode_string",
)

ALIGN_BYTES = 4

HEADER_FORMAT = "<HHI"
HEADER_LENGTH = struct.calcsize(HEADER_FORMAT)


def align_bytes(count: int) -> int:
    over = count % ALIGN_BYTES
    return count if over == 0 else count + (ALIGN_BYTES - over)


def encode_string(string: str, utf_16: bool = False) -> bytes:
    encoding = "utf-16" if utf_16 else "utf-8"
    data = string.encode(encoding)
    length = align_bytes(len(data))
    fmt = f"<I{str(length)}s"
    if utf_16:
        length = length | 0x80000000  # Set high bit for utf-16
    return struct.pack(fmt, length, data)


def encode_datetime(date_time: datetime) -> bytes:
    return struct.pack(
        "<8H",
        date_time.year,
        date_time.month,
        date_time.weekday(),
        date_time.day,
        date_time.hour,
        date_time.minute,
        0,  # Setting seconds causes controller time to revert to the prev min after :59
        int(date_time.microsecond / 1000),
    )


class MessageCode(SLIntEnum):
    """Message codes for communication with the ScreenLogic gateway."""

    LOGIN_REJECTED = 13
    CHALLENGE = 14
    PING_REQ = 16
    LOCAL_LOGIN = 27
    INVALID_REQUEST = 30
    BAD_PARAMETER = 31  # Actually bad parameter?
    GET_USER_CONFIG = 8058
    GET_DATETIME = 8110
    SET_DATETIME = 8112
    GET_VERSION = 8120
    WEATHER_FORECAST_CHANGED = 9806
    GET_WEATHER_FORECAST = 9807
    STATUS_CHANGED = 12500
    COLOR_UPDATE = 12504
    CHEMISTRY_CHANGED = 12505
    ADD_CLIENT = 12522
    REMOVE_CLIENT = 12524
    GET_POOL_STATUS = 12526
    SET_HEAT_TEMPERATURE = 12528
    SET_CIRCUIT = 12530
    GET_POOL_CONFIG = 12532
    SET_HEAT_MODE = 12538
    SET_LIGHTS = 12556
    SET_CHEMISTRY_CONFIG = 12594
    GET_EQUIPMENT = 12566
    GET_SCG_CONFIG = 12572
    SET_SCG = 12576
    GET_PUMP_STATUS = 12584
    SET_COOL_TEMPERATURE = 12590
    GET_CHEMISTRY = 12592
    GET_GATEWAY_CONFIG = 18003


class Payload:
    _bytes: bytes
    _pos: int = 0

    def __init__(self, data: bytes = b"") -> None:
        self._bytes = data

    @property
    def bytes(self) -> bytes:
        return self._bytes

    @property
    def length(self) -> int:
        return len(self._bytes)

    @property
    def position(self) -> int:
        return self._pos

    @position.setter
    def position(self, value: int) -> None:
        if value < 0 or value >= self.length:
            raise ValueError()
        self._pos = value

    def next(self, format: str) -> tuple[Any, ...]:
        data = struct.unpack_from(format, self._bytes, self._pos)
        self._pos += struct.calcsize(format)
        return data

    def next_int8(self) -> int:
        return self.next("<b")[0]

    def next_uint8(self) -> int:
        return self.next("<B")[0]

    def next_int16(self) -> int:
        return self.next("<h")[0]

    def next_uint16(self) -> int:
        return self.next("<H")[0]

    def next_int32(self) -> int:
        return self.next("<i")[0]

    def next_uint32(self) -> int:
        return self.next("<I")[0]

    def next_string(self) -> str:
        str_len = self.next_uint32()
        encoding = "utf-8"
        if str_len & 0x80000000:  # High bit signifies utf-16 encoding
            str_len = str_len & 0x7FFFFFFF  # Strip off the high bit
            encoding = "utf-16"
        pad_len = align_bytes(str_len)
        return self.next(f"<{pad_len}s")[0].decode(encoding).strip("\0")

    def next_array(self) -> list:
        array_len = self.next_uint32()
        items = []
        for _ in range(array_len):
            items.append(self.next_uint8())
        self._pos += align_bytes(array_len) - array_len
        return items

    def next_datetime(self, tz: timezone = timezone.utc) -> datetime:
        year, month, _, day, hour, minute, second, millisecond = self.next("<8H")
        return datetime(year, month, day, hour, minute, second, millisecond * 1000, tz)

    def unknown_int8(self) -> UnknownValue:
        return UnknownValue(self.next_int8(), "<b")

    def unknown_uint8(self) -> UnknownValue:
        return UnknownValue(self.next_uint8(), "<B")

    def unknown_int16(self) -> UnknownValue:
        return UnknownValue(self.next_int16(), "<h")

    def unknown_uint16(self) -> UnknownValue:
        return UnknownValue(self.next_uint16(), "<H")

    def unknown_int32(self) -> UnknownValue:
        return UnknownValue(self.next_int32(), "<i")

    def unknown_uint32(self) -> UnknownValue:
        return UnknownValue(self.next_uint32(), "<I")


class AbstractMessage:
    """Defines a single message between a ScreenLogicClient and a ScreenLogic Gateway."""

    _code: MessageCode | None = None
    _id: int = 0
    _payload: Payload = Payload()

    @property
    def code(self) -> int:
        return self._code

    @property
    def id(self) -> int:
        return self._id

    @property
    def payload(self) -> Payload:
        return self._payload

    def size(self) -> int:
        return self._payload.length

    def to_bytes(self, message_id: int = 0) -> bytes:
        id = self._id or message_id
        length = self._payload.length
        return struct.pack(
            f"{HEADER_FORMAT}{length}s", id, self._code, length, self._payload.bytes
        )


class BaseRequest(AbstractMessage):
    """Defines a request made of a ScreenLogic Gateway."""

    def __init__(self, id: int = 0) -> None:
        self._id = id


class BaseResponse(AbstractMessage):
    """Defines a response from a ScreenLogic Gateway."""

    def __init__(self, payload: Payload = Payload(), id: int = 0) -> None:
        self._payload = payload
        self._id = id

    def decode(self, system: System) -> None:
        raise NotImplementedError()


class BadParameterResponse(BaseResponse):
    _code = MessageCode.BAD_PARAMETER


class InvalidRequestResponse(BaseResponse):
    _code = MessageCode.INVALID_REQUEST


class LoginRejectedResponse(BaseResponse):
    _code = MessageCode.LOGIN_REJECTED


def import_messages(modules: list[str]) -> dict[int, BaseRequest | BaseResponse]:
    out = {}
    for module_name in modules:
        module = importlib.import_module(module_name, ".messages")
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj):
                if issubclass(obj, (BaseRequest, BaseResponse)):
                    out[obj._code] = obj
    return out
