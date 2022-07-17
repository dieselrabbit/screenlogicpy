import asyncio

from .protocol import ScreenLogicProtocol
from ..const import MESSAGE, ScreenLogicWarning


async def async_make_request(
    protocol: ScreenLogicProtocol, messageCode: int, message: bytes = b""
) -> bytes:
    try:
        await asyncio.wait_for(
            (request := protocol.await_send_message(messageCode, message)),
            MESSAGE.COM_TIMEOUT,
        )
        if not request.cancelled():
            return request.result()
    except asyncio.TimeoutError:
        raise ScreenLogicWarning(
            f"Timeout waiting for response to message code '{messageCode}'"
        )
