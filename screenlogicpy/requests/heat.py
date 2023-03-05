import struct

from ..const import CODE
from .protocol import ScreenLogicProtocol
from .request import async_make_request


async def async_request_set_heat_setpoint(
    protocol: ScreenLogicProtocol, body: int, set_point: float, max_retries: int
) -> bool:
    return (
        await async_make_request(
            protocol,
            CODE.SETHEATTEMP_QUERY,
            struct.pack("<III", 0, body, set_point),
            max_retries,
        )
        == b""
    )


async def async_request_set_heat_mode(
    protocol: ScreenLogicProtocol, body: int, heat_mode: int, max_retries: int
) -> bool:
    return (
        await async_make_request(
            protocol,
            CODE.SETHEATMODE_QUERY,
            struct.pack("<III", 0, body, heat_mode),
            max_retries,
        )
        == b""
    )
