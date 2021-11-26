import asyncio

from ..const import CODE, MESSAGE, ScreenLogicWarning
from .protocol import ScreenLogicProtocol
from .utility import decodeMessageString


async def async_request_gateway_version(protocol: ScreenLogicProtocol):
    try:
        await asyncio.wait_for(
            (request := protocol.await_send_message(CODE.VERSION_QUERY)),
            MESSAGE.COM_TIMEOUT,
        )
        if not request.cancelled():
            return decodeMessageString(request.result())
    except asyncio.TimeoutError:
        raise ScreenLogicWarning("Timeout polling gateway version")
