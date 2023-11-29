from ..const.common import ScreenLogicResponseError
from ..const.msg import CODE
from .protocol import ScreenLogicProtocol
from .request import async_make_request


async def async_request_ping(protocol: ScreenLogicProtocol, max_retries: int) -> bytes:
    if (
        response := await async_make_request(
            protocol, CODE.PING_QUERY, max_retries=max_retries
        )
    ) != b"":
        raise ScreenLogicResponseError(f"Ping failed. Unexpected response: {response}")
