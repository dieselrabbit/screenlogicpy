import struct
import sys
from typing import Any

from ..const import ScreenLogicError
from ..const.common import UNIT
from ..const.msg import HEADER_FORMAT, HEADER_LENGTH
from ..const.data import ATTR, DEVICE, GROUP, VALUE

if sys.version_info[:2] < (3, 11):
    from async_timeout import timeout as asyncio_timeout  # noqa F401
else:
    from asyncio import timeout as asyncio_timeout  # noqa F401


def makeMessage(msgID: int, msgCode: int, messageData: bytes = b""):
    """Returns packed bytes formatted as a ready-to-send ScreenLogic message."""
    return struct.pack(
        f"{HEADER_FORMAT}{str(len(messageData))}s",
        msgID,
        msgCode,
        len(messageData),
        messageData,
    )


def takeMessage(data: bytes) -> tuple[int, int, bytes]:
    """Return (messageID, messageCode, message) from raw ScreenLogic message bytes."""
    messageBytes = len(data) - HEADER_LENGTH
    msgID, msgCode, msgLen, msgData = struct.unpack(
        f"{HEADER_FORMAT}{messageBytes}s", data
    )
    if msgLen != messageBytes:
        raise ScreenLogicError(
            f"Response length invalid. Claimed: {msgLen}. Received: {messageBytes}. Message ID: {msgID}. Message Code: {msgCode}. Data: {data}"
        )
    return msgID, msgCode, msgData  # return raw data


def takeMessages(data: bytes) -> list[tuple[int, int, bytes]]:
    messages = []
    pos = 0
    try:
        while pos < len(data):
            msgID, pos = getSome("H", data, pos)
            msgCode, pos = getSome("H", data, pos)
            msgLength, pos = getSome("I", data, pos)
            message, pos = getSome(f"{msgLength}s", data, pos)
            messages.append([msgID, msgCode, message])
        return messages
    except struct.error as err:
        raise ScreenLogicError(
            f"Unexpected amount of data received. Data: {data}"
        ) from err


def encodeMessageString(string) -> bytes:
    data = string.encode()
    length = len(data)
    over = length % 4
    pad = (4 - over) if over > 0 else 0  # pad string to multiple of 4
    fmt = f"<I{str(length + pad)}s"
    return struct.pack(fmt, length, data)


def decodeMessageString(data) -> str:
    size = struct.unpack_from("<I", data, 0)[0]
    return struct.unpack_from(f"<{str(size)}s", data, struct.calcsize("<I"))[0].decode(
        "utf-8"
    )


def getSome(format, buff, offset) -> tuple[Any, int]:
    fmt = format if format.startswith(">") else f"<{format}"
    newoffset = offset + struct.calcsize(fmt)
    return struct.unpack_from(fmt, buff, offset)[0], newoffset


def getValueAt(buff, offset, want, **kwargs):
    fmt = want if want.startswith(">") else "<" + want
    val = kwargs.get("adjustment", lambda x: x)(
        struct.unpack_from(fmt, buff, offset)[0]
    )
    if name := kwargs.get("name"):
        data = {
            "name": name,
            "value": val,
        }
        if unit := kwargs.get("unit"):
            data["unit"] = unit
        if device_type := kwargs.get("device_type"):
            data["device_type"] = device_type
    else:
        data = val
    newoffset = offset + struct.calcsize(fmt)
    return data, newoffset


def getString(buff, offset) -> tuple[str, int]:
    fmtLen = "<I"
    offsetLen = offset + struct.calcsize(fmtLen)
    sLen = struct.unpack_from(fmtLen, buff, offset)[0]
    if sLen % 4 != 0:
        sLen += 4 - sLen % 4

    fmt = f"<{sLen}s"
    newoffset = offsetLen + struct.calcsize(fmt)
    padded_str = struct.unpack_from(fmt, buff, offsetLen)[0]
    return padded_str.decode("utf-8").strip("\0"), newoffset


def getArray(buff, offset):
    itemCount, offset = getSome("I", buff, offset)
    items = [0 for x in range(itemCount)]
    for i in range(itemCount):
        items[i], offset = getSome("B", buff, offset)
    offsetPad = 0
    if itemCount % 4 != 0:
        offsetPad = (4 - itemCount % 4) % 4
        offset += offsetPad
    return items, offset


def getTemperatureUnit(data: dict):
    return (
        UNIT.CELSIUS
        if data.get(DEVICE.CONTROLLER, {})
        .get(GROUP.CONFIGURATION, {})
        .get(VALUE.IS_CELSIUS, {})
        .get(ATTR.VALUE)
        else UNIT.FAHRENHEIT
    )
