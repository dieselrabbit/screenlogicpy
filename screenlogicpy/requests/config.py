import struct

# import json
from .utility import sendRecieveMessage, getSome, getString
from ..const import code, BODY_TYPE


def request_pool_config(gateway_socket, data):
    response = sendRecieveMessage(
        gateway_socket, code.CTRLCONFIG_QUERY, struct.pack("<2I", 0, 0)
    )
    decode_pool_config(response, data)


def decode_pool_config(buff, data):
    # print(buff)
    if "config" not in data:
        data["config"] = {}

    config = data["config"]

    controllerID, offset = getSome("I", buff, 0)
    config["controller_id"] = {"name": "Controller ID", "value": controllerID}

    if "bodies" not in data:
        data["bodies"] = {}

    bodies = data["bodies"]

    for i in range(2):
        if i not in bodies:
            bodies[i] = {}

        currentBody = bodies[i]

        minSetPoint, offset = getSome("B", buff, offset)
        MINspName = "{} Minimum Set Point".format(BODY_TYPE.NAME_FOR_NUM[i])
        currentBody["min_set_point"] = {"name": MINspName, "value": minSetPoint}
        maxSetPoint, offset = getSome("B", buff, offset)
        MAXspName = "{} Minimum Set Point".format(BODY_TYPE.NAME_FOR_NUM[i])
        currentBody["max_set_point"] = {"name": MAXspName, "value": maxSetPoint}

    degC, offset = getSome("B", buff, offset)
    config["is_celcius"] = {"name": "Is Celcius", "value": degC}

    controllerType, offset = getSome("B", buff, offset)
    config["controller_type"] = controllerType

    hwType, offset = getSome("B", buff, offset)
    config["hardware_type"] = hwType

    controllerbuff, offset = getSome("B", buff, offset)
    config["controller_buffer"] = controllerbuff

    equipFlags, offset = getSome("I", buff, offset)
    config["equipment_flags"] = equipFlags

    paddedGenName, offset = getString(buff, offset)
    genCircuitName = paddedGenName.decode("utf-8").strip("\0")
    config["generic_circuit_name"] = {
        "name": "Default Circuit Name",
        "value": genCircuitName,
    }

    circuitCount, offset = getSome("I", buff, offset)
    config["circuit_count"] = {"name": "Number of Circuits", "value": circuitCount}

    if "circuits" not in data:
        data["circuits"] = {}

    circuits = data["circuits"]

    for i in range(circuitCount):

        circuitID, offset = getSome("i", buff, offset)

        if circuitID not in data["circuits"]:
            circuits[circuitID] = {}

        currentCircuit = circuits[circuitID]

        currentCircuit["id"] = circuitID

        paddedName, offset = getString(buff, offset)
        circuitName = paddedName.decode("utf-8").strip("\0")
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

        offset = offset + struct.calcsize("2B")

    colorCount, offset = getSome("I", buff, offset)
    config["color_count"] = {"name": "Number of Colors", "value": colorCount}

    if "colors" not in data["config"] or len(config["colors"]) != colorCount:
        config["colors"] = [{} for x in range(colorCount)]

    for i in range(colorCount):
        paddedColorName, offset = getString(buff, offset)
        colorName = paddedColorName.decode("utf-8").strip("\0")
        rgbR, offset = getSome("I", buff, offset)
        rgbG, offset = getSome("I", buff, offset)
        rgbB, offset = getSome("I", buff, offset)
        config["colors"][i] = {"name": colorName, "value": (rgbR, rgbG, rgbB)}

    pumpCircuitCount = 8
    if "pumps" not in data:
        data["pumps"] = {}

    pumps = data["pumps"]

    for i in range(pumpCircuitCount):
        if i not in pumps:
            pumps[i] = {}
        pumpData, offset = getSome("B", buff, offset)
        pumps[i]["data"] = pumpData

    interfaceTabFlags, offset = getSome("I", buff, offset)
    config["interface_tab_flags"] = interfaceTabFlags

    showAlarms, offset = getSome("I", buff, offset)
    config["show_alarms"] = showAlarms
    # print(json.dumps(data, indent=4))
