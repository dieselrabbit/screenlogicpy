import datetime


import struct

from ..const.data import DEVICE, GROUP, VALUE
from ..const.msg import CODE
from .protocol import ScreenLogicProtocol
from .request import async_make_request
from .utility import getSome, getTime, encodeMessageTime


async def async_request_date_time(
    protocol: ScreenLogicProtocol, data: dict, max_retries: int = None
) -> bytes:
    if result := await async_make_request(
        protocol, CODE.DATETIME_QUERY, max_retries=max_retries
    ):
        decode_date_time(result, data)
        return result


def decode_date_time(buffer: bytes, data: dict):
    controller: dict = data.setdefault(DEVICE.CONTROLLER, {})
    date_time: dict = controller.setdefault(GROUP.DATE_TIME, {})

    dt, offset = getTime(buffer, 0)
    date_time[VALUE.TIMESTAMP] = dt.timestamp()

    auto_dst, offset = getSome("I", buffer, offset)
    date_time[VALUE.AUTO_DST] = {
        "name": "Automatic Daylight Saving Time",
        "value": auto_dst,
    }


async def async_request_set_date_time(
    protocol: ScreenLogicProtocol,
    date_time: datetime,
    auto_dst: int,
    max_retries: int = None,
) -> bool:
    return (
        await async_make_request(
            protocol,
            CODE.SETDATETIME_QUERY,
            encodeMessageTime(date_time) + struct.pack("<I", auto_dst),
            max_retries,
        )
        == b""
    )
