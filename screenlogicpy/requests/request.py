import asyncio

from ..const import MESSAGE, ScreenLogicWarning
from .protocol import ScreenLogicProtocol
from .utility import asyncio_timeout


async def async_make_request(
    protocol: ScreenLogicProtocol, messageCode: int, message: bytes = b""
) -> bytes:
    request = protocol.await_send_message(messageCode, message)
    try:
        async with asyncio_timeout(MESSAGE.COM_TIMEOUT):
            await request
    except asyncio.TimeoutError:
        raise ScreenLogicWarning(
            f"Timeout waiting for response to message code '{messageCode}'"
        )
    if not request.cancelled():
        return request.result()
