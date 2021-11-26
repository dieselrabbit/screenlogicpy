# import json
import asyncio
import struct

from ..const import CODE, DATA, MESSAGE, ScreenLogicWarning
from .protocol import ScreenLogicProtocol
from .utility import getSome


async def async_request_scg_config(protocol: ScreenLogicProtocol, data):
    try:
        await asyncio.wait_for(
            (
                request := protocol.await_send_message(
                    CODE.SCGCONFIG_QUERY, struct.pack("<I", 0)
                )
            ),
            MESSAGE.COM_TIMEOUT,
        )
        if not request.cancelled():
            decode_scg_config(request.result(), data)
    except asyncio.TimeoutError:
        raise ScreenLogicWarning("Timeout polling scg config")


def decode_scg_config(buff, data):
    # print(buff)

    if DATA.KEY_SCG not in data:
        data[DATA.KEY_SCG] = {}

    scg = data[DATA.KEY_SCG]

    present, offset = getSome("I", buff, 0)
    scg["scg_present"] = present

    status, offset = getSome("I", buff, offset)
    scg["scg_status"] = {"name": "SCG Status", "value": status}

    level1, offset = getSome("I", buff, offset)
    scg["scg_level1"] = {"name": "SCG Level 1", "value": level1, "unit": "%"}

    level2, offset = getSome("I", buff, offset)
    scg["scg_level2"] = {"name": "SCG Level 2", "value": level2, "unit": "%"}

    salt, offset = getSome("I", buff, offset)
    scg["scg_salt_ppm"] = {"name": "SCG Salt", "value": (salt * 50), "unit": "ppm"}

    flags, offset = getSome("I", buff, offset)
    scg["scg_flags"] = flags

    superChlorTimer, offset = getSome("I", buff, offset)
    scg["scg_super_chlor_timer"] = {
        "name": "SCG Super Chlorination Timer",
        "value": superChlorTimer,
    }

    # print(json.dumps(data, indent=2))


async def async_request_set_scg_config(
    protocol: ScreenLogicProtocol, pool_output, spa_output
):
    try:
        await asyncio.wait_for(
            (
                request := protocol.await_send_message(
                    CODE.SETSCG_QUERY,
                    struct.pack("<IIIII", 0, pool_output, spa_output, 0, 0),
                )
            ),
            MESSAGE.COM_TIMEOUT,
        )
        return not request.cancelled() and request.result() == b""
    except asyncio.TimeoutError:
        raise ScreenLogicWarning("Timeout requesting scg config change")
