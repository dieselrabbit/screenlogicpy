import struct

from ..const import CODE, DATA
from .protocol import ScreenLogicProtocol
from .request import async_make_request
from .utility import getSome


async def async_request_scg_config(protocol: ScreenLogicProtocol, data: dict) -> bytes:
    if result := await async_make_request(
        protocol, CODE.SCGCONFIG_QUERY, struct.pack("<I", 0)
    ):
        decode_scg_config(result, data)
        return result


def decode_scg_config(buff: bytes, data: dict) -> None:
    scg = data.setdefault(DATA.KEY_SCG, {})

    present, offset = getSome("I", buff, 0)
    scg["scg_present"] = present

    status, offset = getSome("I", buff, offset)
    scg["scg_status"] = {"name": "SCG Status", "value": status}

    level1, offset = getSome("I", buff, offset)
    scg["scg_level1"] = {"name": "Pool SCG Level", "value": level1, "unit": "%"}

    level2, offset = getSome("I", buff, offset)
    scg["scg_level2"] = {"name": "Spa SCG Level", "value": level2, "unit": "%"}

    salt, offset = getSome("I", buff, offset)
    scg["scg_salt_ppm"] = {"name": "SCG Salt", "value": (salt * 50), "unit": "ppm"}

    flags, offset = getSome("I", buff, offset)
    scg["scg_flags"] = flags

    superChlorTimer, offset = getSome("I", buff, offset)
    scg["scg_super_chlor_timer"] = {
        "name": "SCG Super Chlorination Timer",
        "value": superChlorTimer,
    }


async def async_request_set_scg_config(
    protocol: ScreenLogicProtocol, pool_output: int, spa_output: int
) -> bool:
    return (
        await async_make_request(
            protocol,
            CODE.SETSCG_QUERY,
            struct.pack("<IIIII", 0, pool_output, spa_output, 0, 0),
        )
        == b""
    )
