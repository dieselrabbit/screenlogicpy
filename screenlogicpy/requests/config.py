# import json
import struct

from ..const import CODE, BODY_TYPE, DATA
from .protocol import ScreenLogicProtocol
from .request import async_make_request
from .utility import getSome, getString


async def async_request_pool_config(
    protocol: ScreenLogicProtocol, data: dict, max_retries: int
) -> bytes:
    if result := await async_make_request(
        protocol,
        CODE.CTRLCONFIG_QUERY,
        struct.pack("<2I", 0, 0),  # 0,1 yields different return
        max_retries,
    ):
        decode_pool_config(result, data)
        return result


def decode_pool_config(buff: bytes, data: dict) -> dict:
    config: dict = data.setdefault(DATA.KEY_CONFIG, {})

    controllerID, offset = getSome("I", buff, 0)
    config["controller_id"] = {"name": "Controller ID", "value": controllerID}

    bodies: dict = data.setdefault(DATA.KEY_BODIES, {})

    for i in range(2):
        currentBody: dict = bodies.setdefault(i, {})

        minSetPoint, offset = getSome("B", buff, offset)
        MINspName = "{} Minimum Set Point".format(BODY_TYPE.NAME_FOR_NUM[i])
        currentBody["min_set_point"] = {"name": MINspName, "value": minSetPoint}
        maxSetPoint, offset = getSome("B", buff, offset)
        MAXspName = "{} Maximum Set Point".format(BODY_TYPE.NAME_FOR_NUM[i])
        currentBody["max_set_point"] = {"name": MAXspName, "value": maxSetPoint}

    degC, offset = getSome("B", buff, offset)
    config["is_celsius"] = {"name": "Is Celsius", "value": degC}

    controllerType, offset = getSome("B", buff, offset)
    config["controller_type"] = controllerType

    hwType, offset = getSome("B", buff, offset)
    config["hardware_type"] = hwType

    controllerbuff, offset = getSome("B", buff, offset)
    config["controller_buffer"] = controllerbuff

    equipFlags, offset = getSome("I", buff, offset)
    config["equipment_flags"] = equipFlags

    genCircuitName, offset = getString(buff, offset)
    config["generic_circuit_name"] = {
        "name": "Default Circuit Name",
        "value": genCircuitName,
    }

    circuitCount, offset = getSome("I", buff, offset)
    config["circuit_count"] = {"name": "Number of Circuits", "value": circuitCount}

    circuits: dict = data.setdefault(DATA.KEY_CIRCUITS, {})

    for i in range(circuitCount):

        circuitID, offset = getSome("i", buff, offset)

        currentCircuit = circuits.setdefault(circuitID, {})

        currentCircuit["id"] = circuitID

        circuitName, offset = getString(buff, offset)
        currentCircuit["name"] = circuitName

        cNameIndex, offset = getSome("B", buff, offset)
        currentCircuit["name_index"] = cNameIndex

        cFunction, offset = getSome("B", buff, offset)
        currentCircuit["function"] = cFunction

        cInterface, offset = getSome("B", buff, offset)
        currentCircuit["interface"] = cInterface

        cFlags, offset = getSome("B", buff, offset)
        currentCircuit["flags"] = cFlags

        cColorSet, offset = getSome("B", buff, offset)
        currentCircuit["color_set"] = cColorSet

        cColorPos, offset = getSome("B", buff, offset)
        currentCircuit["color_position"] = cColorPos

        cColorStagger, offset = getSome("B", buff, offset)
        currentCircuit["color_stagger"] = cColorStagger

        cDeviceID, offset = getSome("B", buff, offset)
        currentCircuit["device_id"] = cDeviceID

        cDefaultRT, offset = getSome("H", buff, offset)
        currentCircuit["default_rt"] = cDefaultRT

        currentCircuit[f"unknown_at_offset_{offset:02}"], offset = getSome(
            "B", buff, offset
        )

        currentCircuit[f"unknown_at_offset_{offset:02}"], offset = getSome(
            "B", buff, offset
        )

    colorCount, offset = getSome("I", buff, offset)
    config["color_count"] = {"name": "Number of Colors", "value": colorCount}

    colors = config.setdefault(DATA.KEY_COLORS, [{} for x in range(colorCount)])

    for i in range(colorCount):
        colorName, offset = getString(buff, offset)
        rgbR, offset = getSome("I", buff, offset)
        rgbG, offset = getSome("I", buff, offset)
        rgbB, offset = getSome("I", buff, offset)
        colors[i] = {"name": colorName, "value": (rgbR, rgbG, rgbB)}

    pumpCircuitCount = 8

    pumps: dict = data.setdefault(DATA.KEY_PUMPS, {})

    for i in range(pumpCircuitCount):
        currentPump = pumps.setdefault(i, {})

        pumpData, offset = getSome("B", buff, offset)
        currentPump["data"] = pumpData

    interfaceTabFlags, offset = getSome("I", buff, offset)
    config["interface_tab_flags"] = interfaceTabFlags

    showAlarms, offset = getSome("I", buff, offset)
    config["show_alarms"] = showAlarms
