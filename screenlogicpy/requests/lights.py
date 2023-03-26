import struct

from ..const import CODE
from ..data import ATTR, DEVICE, KEY
from .protocol import ScreenLogicProtocol
from .request import async_make_request
from .utility import getSome, getString


async def async_request_pool_lights_command(
    protocol: ScreenLogicProtocol, light_command: int, max_retries: int
) -> bool:
    return (
        await async_make_request(
            protocol,
            CODE.LIGHTCOMMAND_QUERY,
            struct.pack("<II", 0, light_command),
            max_retries,
        )
        == b""
    )


def decode_color_update(buff: bytes, data: dict):
    controller: dict = data.setdefault(DEVICE.CONTROLLER, {})

    color_state: dict = controller.setdefault(KEY.COLOR_LIGHTS, {})

    color_state[ATTR.COLOR_MODE], offset = getSome("I", buff, 0)  # 0

    color_state[ATTR.PROGRESS], offset = getSome("I", buff, offset)  # 4

    color_state[ATTR.LIMIT], offset = getSome("I", buff, offset)  # 8

    color_state[ATTR.TEXT], offset = getString(buff, offset)  # 12
