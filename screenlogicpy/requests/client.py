import struct

from ..const.common import CLIENT_ID, ScreenLogicResponseError
from ..const.msg import CODE, COM_MAX_RETRIES
from .protocol import ScreenLogicProtocol
from .request import async_make_request


async def async_request_add_client(
    protocol: ScreenLogicProtocol,
    clientID: int = CLIENT_ID,
    max_retries: int = COM_MAX_RETRIES,
) -> bool:
    if (
        response := await async_make_request(
            protocol,
            CODE.ADD_CLIENT_QUERY,
            struct.pack("<II", 0, clientID),
            max_retries,
        )
    ) != b"":
        raise ScreenLogicResponseError(
            f"Add client failed. Unexpected response:{response}"
        )


async def async_request_remove_client(
    protocol: ScreenLogicProtocol,
    clientID: int = CLIENT_ID,
    max_retries: int = COM_MAX_RETRIES,
) -> bool:
    if (
        response := await async_make_request(
            protocol,
            CODE.REMOVE_CLIENT_QUERY,
            struct.pack("<II", 0, clientID),
            max_retries,
        )
    ) != b"":
        raise ScreenLogicResponseError(
            f"Remove client failed. Unexpected response:{response}"
        )
