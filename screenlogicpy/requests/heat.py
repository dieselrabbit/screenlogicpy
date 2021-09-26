import asyncio
import struct

from ..const import CODE, MESSAGE, ScreenLogicWarning
from .protocol import ScreenLogicProtocol


async def async_request_set_heat_setpoint(
    protocol: ScreenLogicProtocol, body, setpoint
):
    try:
        await asyncio.wait_for(
            (
                request := protocol.await_send_data(
                    CODE.SETHEATTEMP_QUERY, struct.pack("<III", 0, body, setpoint), body
                )
            ),
            MESSAGE.COM_TIMEOUT,
        )
        return not request.cancelled() and request.result() == b""
    except asyncio.TimeoutError:
        raise ScreenLogicWarning("Timeout requesting heat setpoint change")


async def async_request_set_heat_mode(protocol: ScreenLogicProtocol, body, heat_mode):
    try:
        await asyncio.wait_for(
            (
                request := protocol.await_send_data(
                    CODE.SETHEATMODE_QUERY,
                    struct.pack("<III", 0, body, heat_mode),
                    body,
                )
            ),
            MESSAGE.COM_TIMEOUT,
        )
        return not request.cancelled() and request.result() == b""
    except asyncio.TimeoutError:
        raise ScreenLogicWarning("Timeout requesting heat mode change")
