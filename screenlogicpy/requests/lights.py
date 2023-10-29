import struct

from ..const.common import ScreenLogicResponseError
from ..const.msg import CODE
from ..const.data import ATTR, DEVICE, GROUP
from .protocol import ScreenLogicProtocol
from .request import async_make_request
from .utility import getSome, getString


async def async_request_pool_lights_command(
    protocol: ScreenLogicProtocol, light_command: int, max_retries: int
) -> bool:
    if (
        response := await async_make_request(
            protocol,
            CODE.LIGHTCOMMAND_QUERY,
            struct.pack("<II", 0, light_command),
            max_retries,
        )
    ) != b"":
        raise ScreenLogicResponseError(
            f"Set color lights failed: Unexpected response: {response}"
        )


def decode_color_update(buff: bytes, data: dict):
    controller: dict = data.setdefault(DEVICE.CONTROLLER, {})

    color_state: dict = controller.setdefault(GROUP.COLOR_LIGHTS, {})

    color_state[ATTR.COLOR_MODE], offset = getSome("I", buff, 0)  # 0

    color_state[ATTR.PROGRESS], offset = getSome("I", buff, offset)  # 4

    color_state[ATTR.LIMIT], offset = getSome("I", buff, offset)  # 8

    color_state[ATTR.TEXT], offset = getString(buff, offset)  # 12
