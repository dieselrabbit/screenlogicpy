import datetime


import struct

from ..const import CODE, DATA
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
    config = data.setdefault(DATA.KEY_CONFIG, {})

    dt, offset = getTime(buffer, 0)
    config["controller_time"] = dt.timestamp()

    auto_dst, offset = getSome("I", buffer, offset)
    config["controller_time_auto_dst"] = {
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
