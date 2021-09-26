import asyncio
import struct

from ..const import CODE, MESSAGE, ScreenLogicWarning
from .protocol import ScreenLogicProtocol


async def async_request_pool_button_press(
    protocol: ScreenLogicProtocol, circuit_id, circuit_state
):
    try:
        await asyncio.wait_for(
            (
                request := protocol.await_send_data(
                    CODE.BUTTONPRESS_QUERY,
                    struct.pack("<III", 0, circuit_id, circuit_state),
                    circuit_id,
                )
            ),
            MESSAGE.COM_TIMEOUT,
        )
        return not request.cancelled() and request.result() == b""
    except asyncio.TimeoutError:
        raise ScreenLogicWarning("Timeout requesting button press")
