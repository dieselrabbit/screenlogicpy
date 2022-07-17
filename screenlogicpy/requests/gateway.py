from ..const import CODE
from .protocol import ScreenLogicProtocol
from .request import async_make_request
from .utility import decodeMessageString


async def async_request_gateway_version(protocol: ScreenLogicProtocol):
    if result := await async_make_request(protocol, CODE.VERSION_QUERY):
        return decodeMessageString(result)
