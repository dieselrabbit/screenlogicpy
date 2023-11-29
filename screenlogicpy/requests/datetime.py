from datetime import datetime, timezone
import struct

from ..const.common import ScreenLogicResponseError
from ..const.data import ATTR, DEVICE, GROUP, VALUE
from ..const.msg import CODE
from .protocol import ScreenLogicProtocol
from .request import async_make_request
from .utility import getSome, getTime, encodeMessageTime


async def async_request_date_time(
    protocol: ScreenLogicProtocol, data: dict, max_retries: int = None
) -> bytes:
    if result := await async_make_request(
        protocol, CODE.GET_DATETIME_QUERY, max_retries=max_retries
    ):
        decode_date_time(result, data)
        return result


def decode_date_time(buffer: bytes, data: dict):
    host_time = datetime.now(tz=timezone.utc)
    controller: dict = data.setdefault(DEVICE.CONTROLLER, {})
    date_time: dict = controller.setdefault(GROUP.DATE_TIME, {})

    dt, offset = getTime(buffer, 0)
    date_time[VALUE.TIMESTAMP] = dt.timestamp()
    date_time[VALUE.TIMESTAMP_HOST] = host_time.timestamp()

    auto_dst, offset = getSome("I", buffer, offset)
    date_time[VALUE.AUTO_DST] = {
        ATTR.NAME: "Automatic Daylight Saving Time",
        ATTR.VALUE: auto_dst,
    }


async def async_request_set_date_time(
    protocol: ScreenLogicProtocol,
    date_time: datetime,
    auto_dst: int,
    max_retries: int = None,
) -> bool:
    if (
        response := await async_make_request(
            protocol,
            CODE.SET_DATETIME_QUERY,
            encodeMessageTime(date_time) + struct.pack("<I", auto_dst),
            max_retries,
        )
    ) != b"":
        raise ScreenLogicResponseError(
            f"Set datetime failed. Unexpected response: {response}"
        )
