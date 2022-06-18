import struct

from ..const import CODE
from .protocol import ScreenLogicProtocol
from .request import async_make_request


async def async_request_pool_lights_command(
    protocol: ScreenLogicProtocol, light_command: int
) -> bool:
    return (
        await async_make_request(
            protocol, CODE.LIGHTCOMMAND_QUERY, struct.pack("<II", 0, light_command)
        )
        == b""
    )
