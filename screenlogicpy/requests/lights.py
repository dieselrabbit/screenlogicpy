import asyncio
import struct

from ..const import CODE, MESSAGE, ScreenLogicWarning
from .protocol import ScreenLogicProtocol


async def async_request_pool_lights_command(
    protocol: ScreenLogicProtocol, light_command
) -> bool:
    try:
        await asyncio.wait_for(
            (
                request := protocol.await_send_message(
                    CODE.LIGHTCOMMAND_QUERY, struct.pack("<II", 0, light_command)
                )
            ),
            MESSAGE.COM_TIMEOUT,
        )
        return not request.cancelled() and request.result() == b""
    except asyncio.TimeoutError:
        raise ScreenLogicWarning("Timeout requesting light command")
