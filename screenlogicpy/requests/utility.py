import struct
from typing import List, Tuple

from ..const import CODE, DATA, MESSAGE, ScreenLogicError, UNIT


def makeMessage(msgID: int, msgCode: int, messageData: bytes = b""):
    """Returns packed bytes formatted as a ready-to-send ScreenLogic message."""
    return struct.pack(
        MESSAGE.HEADER_FORMAT + str(len(messageData)) + "s",
        msgID,
        msgCode,
        len(messageData),
        messageData,
    )


def takeMessage(data: bytes) -> Tuple[int, int, bytes]:
    """Return (messageID, messageCode, message) from raw ScreenLogic message bytes."""
    messageBytes = len(data) - MESSAGE.HEADER_LENGTH
    msgID, msgCode, msgLen, message = struct.unpack(
        MESSAGE.HEADER_FORMAT + str(messageBytes) + "s", data
    )
    if msgLen != messageBytes:
        raise ScreenLogicError(
            f"Response length invalid. Claimed: {msgLen}. Received: {messageBytes}. Message ID: {msgID}. Message Code: {msgCode}. Data: {data}"
        )
    if msgCode == CODE.UNKNOWN_ANSWER:
        raise ScreenLogicError("Request rejected")
    return msgID, msgCode, message  # return raw data


def takeMessages(data: bytes) -> List[Tuple[int, int, bytes]]:
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


def encodeMessageString(string):
    data = string.encode()
    length = len(data)
    over = length % 4
    pad = (4 - over) if over > 0 else 0  # pad string to multiple of 4
    fmt = "<I" + str(length + pad) + "s"
    return struct.pack(fmt, length, data)


def decodeMessageString(data):
    size = struct.unpack_from("<I", data, 0)[0]
    return struct.unpack_from("<" + str(size) + "s", data, struct.calcsize("<I"))[
        0
    ].decode("utf-8")


def getSome(want, buff, offset):
    fmt = want if want.startswith(">") else "<" + want
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


def getString(buff, offset):
    fmtLen = "<I"
    offsetLen = offset + struct.calcsize(fmtLen)
    sLen = struct.unpack_from(fmtLen, buff, offset)[0]
    if sLen % 4 != 0:
        sLen += 4 - sLen % 4

    fmt = "<{}{}".format(sLen, "s")
    newoffset = offsetLen + struct.calcsize(fmt)
    return struct.unpack_from(fmt, buff, offsetLen)[0], newoffset


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


def packResponse(buff, data):
    packed = {}
    packed["raw"] = buff
    packed["parsed"] = data
    return packed


def getTemperatureUnit(data: dict):
    return (
        UNIT.CELSIUS
        if DATA.KEY_CONFIG in data
        and "is_celsius" in data[DATA.KEY_CONFIG]
        and data[DATA.KEY_CONFIG]["is_celsius"]["value"]
        else UNIT.FAHRENHEIT
    )
