# import json
import struct
from .utility import sendReceiveMessage, getSome
from ..const import code, DATA


def request_scg_config(gateway_socket, data):
    response = sendReceiveMessage(
        gateway_socket, code.SCGCONFIG_QUERY, struct.pack("<I", 0)
    )
    decode_scg_config(response, data)


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
