# import json
import asyncio
import struct

from ..const import (
    ADD_UNKNOWN_VALUES,
    CODE,
    BODY_TYPE,
    DATA,
    DEVICE_TYPE,
    MESSAGE,
    UNIT,
    ScreenLogicWarning,
)
from .protocol import ScreenLogicProtocol
from .utility import getSome


async def async_request_pool_status(protocol: ScreenLogicProtocol, data):
    try:
        await asyncio.wait_for(
            (
                request := protocol.await_send_message(
                    CODE.POOLSTATUS_QUERY, struct.pack("<I", 0)
                )
            ),
            MESSAGE.COM_TIMEOUT,
        )
        if not request.cancelled():
            decode_pool_status(request.result(), data)
    except asyncio.TimeoutError:
        raise ScreenLogicWarning("Timeout polling pool status")


# pylint: disable=unused-variable
def decode_pool_status(buff, data):
    # print(buff)

    if DATA.KEY_CONFIG not in data:
        data[DATA.KEY_CONFIG] = {}

    config = data[DATA.KEY_CONFIG]

    ok, offset = getSome("I", buff, 0)
    config["ok"] = {"name": "OK Check", "value": ok}

    freezeMode, offset = getSome("B", buff, offset)
    config["freeze_mode"] = {"name": "Freeze Mode", "value": freezeMode}

    remotes, offset = getSome("B", buff, offset)
    config["remotes"] = {"name": "Remotes", "value": remotes}

    poolDelay, offset = getSome("B", buff, offset)
    config["pool_delay"] = {"name": "Pool Delay", "value": poolDelay}

    spaDelay, offset = getSome("B", buff, offset)
    config["spa_delay"] = {"name": "Spa Delay", "value": spaDelay}

    cleanerDelay, offset = getSome("B", buff, offset)
    config["cleaner_delay"] = {"name": "Cleaner Delay", "value": cleanerDelay}

    unknown = {}
    # fast forward 3 bytes. Unknown data.
    ff1, offset = getSome("B", buff, offset)
    unknown["ff1"] = ff1
    ff2, offset = getSome("B", buff, offset)
    unknown["ff2"] = ff2
    ff3, offset = getSome("B", buff, offset)
    unknown["ff3"] = ff3

    unit_txt = (
        UNIT.CELSIUS
        if "is_celsius" in config and config["is_celsius"]["value"]
        else UNIT.FAHRENHEIT
    )

    if DATA.KEY_SENSORS not in data:
        data[DATA.KEY_SENSORS] = {}

    sensors = data[DATA.KEY_SENSORS]

    airTemp, offset = getSome("i", buff, offset)
    sensors["air_temperature"] = {
        "name": "Air Temperature",
        "value": airTemp,
        "unit": unit_txt,
        "device_type": DEVICE_TYPE.TEMPERATURE,
    }

    bodiesCount, offset = getSome("I", buff, offset)
    # Should this default to 2?
    bodiesCount = min(bodiesCount, 2)

    if DATA.KEY_BODIES not in data:
        data[DATA.KEY_BODIES] = {}

    bodies = data[DATA.KEY_BODIES]

    for i in range(bodiesCount):
        bodyType, offset = getSome("I", buff, offset)
        if bodyType not in range(2):
            bodyType = 0

        if i not in bodies:
            bodies[i] = {}

        currentBody = bodies[i]

        if "min_set_point" not in currentBody:
            currentBody["min_set_point"] = {}

        currentBody["min_set_point"]["unit"] = unit_txt

        if "max_set_point" not in currentBody:
            currentBody["max_set_point"] = {}

        currentBody["max_set_point"]["unit"] = unit_txt

        currentBody["body_type"] = {"name": "Type of body of water", "value": bodyType}

        lastTemp, offset = getSome("i", buff, offset)
        bodyName = "Last {} Temperature".format(BODY_TYPE.NAME_FOR_NUM[bodyType])
        currentBody["last_temperature"] = {
            "name": bodyName,
            "value": lastTemp,
            "unit": unit_txt,
            "device_type": DEVICE_TYPE.TEMPERATURE,
        }

        heatStatus, offset = getSome("i", buff, offset)
        heaterName = "{} Heat".format(BODY_TYPE.NAME_FOR_NUM[bodyType])
        currentBody["heat_status"] = {"name": heaterName, "value": heatStatus}

        heatSetPoint, offset = getSome("i", buff, offset)
        hspName = "{} Heat Set Point".format(BODY_TYPE.NAME_FOR_NUM[bodyType])
        currentBody["heat_set_point"] = {
            "name": hspName,
            "value": heatSetPoint,
            "unit": unit_txt,
            "device_type": DEVICE_TYPE.TEMPERATURE,
        }

        coolSetPoint, offset = getSome("i", buff, offset)
        cspName = "{} Cool Set Point".format(BODY_TYPE.NAME_FOR_NUM[bodyType])
        currentBody["cool_set_point"] = {
            "name": cspName,
            "value": coolSetPoint,
            "unit": unit_txt,
        }

        heatMode, offset = getSome("i", buff, offset)
        hmName = "{} Heat Mode".format(BODY_TYPE.NAME_FOR_NUM[bodyType])
        currentBody["heat_mode"] = {"name": hmName, "value": heatMode}

    circuitCount, offset = getSome("I", buff, offset)

    if DATA.KEY_CIRCUITS not in data:
        data[DATA.KEY_CIRCUITS] = {}

    circuits = data[DATA.KEY_CIRCUITS]

    for i in range(circuitCount):
        circuitID, offset = getSome("I", buff, offset)

        if circuitID not in circuits:
            circuits[circuitID] = {}

        currentCircuit = circuits[circuitID]

        if "id" not in currentCircuit:
            currentCircuit["id"] = circuitID

        circuitstate, offset = getSome("I", buff, offset)
        currentCircuit["value"] = circuitstate

        cColorSet, offset = getSome("B", buff, offset)
        currentCircuit["color_set"] = cColorSet

        cColorPos, offset = getSome("B", buff, offset)
        currentCircuit["color_position"] = cColorPos

        cColorStagger, offset = getSome("B", buff, offset)
        currentCircuit["color_stagger"] = cColorStagger

        circuitDelay, offset = getSome("B", buff, offset)
        currentCircuit["delay"] = circuitDelay

    pH, offset = getSome("i", buff, offset)
    sensors["ph"] = {"name": "pH", "value": (pH / 100), "unit": "pH"}

    orp, offset = getSome("i", buff, offset)
    sensors["orp"] = {"name": "ORP", "value": orp, "unit": "mV"}

    saturation, offset = getSome("i", buff, offset)
    sensors["saturation"] = {
        "name": "Saturation Index",
        "value": (saturation / 100),
        "unit": "lsi",
    }

    saltPPM, offset = getSome("i", buff, offset)
    sensors["salt_ppm"] = {"name": "Salt", "value": (saltPPM * 50), "unit": "ppm"}

    pHTank, offset = getSome("i", buff, offset)
    sensors["ph_supply_level"] = {"name": "pH Supply Level", "value": pHTank}

    orpTank, offset = getSome("i", buff, offset)
    sensors["orp_supply_level"] = {"name": "ORP Supply Level", "value": orpTank}

    alarm, offset = getSome("i", buff, offset)
    sensors["chem_alarm"] = {
        "name": "Chemistry Alarm",
        "value": alarm,
        "device_type": DEVICE_TYPE.ALARM,
    }

    if ADD_UNKNOWN_VALUES:
        sensors["unknown"] = unknown
    # print(json.dumps(data, indent=4))
