import struct

from ..const.common import ScreenLogicResponseError
from ..const.msg import CODE
from .protocol import ScreenLogicProtocol
from .request import async_make_request


async def async_request_pool_button_press(
    protocol: ScreenLogicProtocol, circuit_id: int, circuit_state: int, max_retries: int
) -> bool:
    if (
        response := await async_make_request(
            protocol,
            CODE.BUTTONPRESS_QUERY,
            struct.pack("<III", 0, circuit_id, circuit_state),
            max_retries,
        )
    ) != b"":
        raise ScreenLogicResponseError(
            f"Set circuit failed. Unexpected response: {response}"
        )
