import struct

from ..const import CODE, CLIENT_ID, MESSAGE
from .protocol import ScreenLogicProtocol
from .request import async_make_request


async def async_request_add_client(
    protocol: ScreenLogicProtocol,
    clientID: int = CLIENT_ID,
    max_retries: int = MESSAGE.COM_MAX_RETRIES,
) -> bool:
    return (
        await async_make_request(
            protocol,
            CODE.ADD_CLIENT_QUERY,
            struct.pack("<II", 0, clientID),
            max_retries,
        )
        == b""
    )


async def async_request_remove_client(
    protocol: ScreenLogicProtocol,
    clientID: int = CLIENT_ID,
    max_retries: int = MESSAGE.COM_MAX_RETRIES,
) -> bool:
    return (
        await async_make_request(
            protocol,
            CODE.REMOVE_CLIENT_QUERY,
            struct.pack("<II", 0, clientID),
            max_retries,
        )
        == b""
    )
