from ..const.msg import CODE
from ..const.data import ATTR, DEVICE, VALUE
from .protocol import ScreenLogicProtocol
from .request import async_make_request
from .utility import decodeMessageString


async def async_request_gateway_version(
    protocol: ScreenLogicProtocol, data: dict, max_retries: int
):
    if result := await async_make_request(
        protocol, CODE.VERSION_QUERY, max_retries=max_retries
    ):
        decode_version(result, data)
        return result


def decode_version(buff: bytes, data: dict):
    adapter: dict = data.setdefault(DEVICE.ADAPTER, {})

    adapter[VALUE.FIRMWARE] = {
        ATTR.NAME: "Protocol Adapter Firmware",
        ATTR.VALUE: decodeMessageString(buff),
    }
