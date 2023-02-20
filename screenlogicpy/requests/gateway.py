from ..const import CODE
from .protocol import ScreenLogicProtocol
from .request import async_make_request
from .utility import decodeMessageString


async def async_request_gateway_version(
    protocol: ScreenLogicProtocol, max_retries: int
):
    if result := await async_make_request(
        protocol, CODE.VERSION_QUERY, max_retries=max_retries
    ):
        return decodeMessageString(result)
