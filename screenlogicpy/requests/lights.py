import struct

from ..const import CODE, DATA
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
    config = data.setdefault(DATA.KEY_CONFIG, {})

    color_state = config.setdefault("color_state", {})

    mode, offset = getSome("I", buff, 0)  # 0
    color_state["mode"] = mode

    progress, offset = getSome("I", buff, offset)  # 4
    color_state["progress"] = progress

    limit, offset = getSome("I", buff, offset)  # 8
    color_state["limit"] = limit

    text, offset = getString(buff, offset)  # 12
    color_state["text"] = text
