# import json
import struct

from ..const import (
    CODE,
    BODY_TYPE,
    DATA,
    DEVICE_TYPE,
    ON_OFF,
    STATE_TYPE,
    UNIT,
)
from .protocol import ScreenLogicProtocol
from .request import async_make_request
from .utility import getSome, getTemperatureUnit


async def async_request_pool_status(protocol: ScreenLogicProtocol, data: dict) -> bytes:
    if result := await async_make_request(
        protocol, CODE.POOLSTATUS_QUERY, struct.pack("<I", 0)
    ):
        decode_pool_status(result, data)
        return result


def decode_pool_status(buff: bytes, data: dict) -> None:
    config = data.setdefault(DATA.KEY_CONFIG, {})

    ok, offset = getSome("I", buff, 0)  # byte offset 0
    config["ok"] = ok

    freezeMode, offset = getSome("B", buff, offset)  # byte offset 4
    config["freeze_mode"] = {
        "name": "Freeze Mode",
        "value": ON_OFF.from_bool(freezeMode & 0x08),
    }

    remotes, offset = getSome("B", buff, offset)  # 5
    config["remotes"] = {"name": "Remotes", "value": remotes}

    poolDelay, offset = getSome("B", buff, offset)  # 6
    config["pool_delay"] = {"name": "Pool Delay", "value": poolDelay}

    spaDelay, offset = getSome("B", buff, offset)  # 7
    config["spa_delay"] = {"name": "Spa Delay", "value": spaDelay}

    cleanerDelay, offset = getSome("B", buff, offset)  # 8
    config["cleaner_delay"] = {"name": "Cleaner Delay", "value": cleanerDelay}

    config[f"unknown_at_offset_{offset:02}"], offset = getSome("B", buff, offset)  # 9
    config[f"unknown_at_offset_{offset:02}"], offset = getSome("B", buff, offset)  # 10
    config[f"unknown_at_offset_{offset:02}"], offset = getSome("B", buff, offset)  # 11

    sensors = data.setdefault(DATA.KEY_SENSORS, {})

    temperature_unit = getTemperatureUnit(data)

    airTemp, offset = getSome("i", buff, offset)  # 12
    sensors["air_temperature"] = {
        "name": "Air Temperature",
        "value": airTemp,
        "unit": temperature_unit,
        "device_type": DEVICE_TYPE.TEMPERATURE,
        "state_type": STATE_TYPE.MEASUREMENT,
    }

    bodiesCount, offset = getSome("I", buff, offset)  # 16

    # Should this default to 2?
    bodiesCount = min(bodiesCount, 2)

    bodies: dict = data.setdefault(DATA.KEY_BODIES, {})

    for i in range(bodiesCount):
        currentBody: dict = bodies.setdefault(i, {})

        bodyType, offset = getSome("I", buff, offset)
        if bodyType not in range(2):
            bodyType = 0

        currentBody.setdefault("min_set_point", {})["unit"] = temperature_unit

        currentBody.setdefault("max_set_point", {})["unit"] = temperature_unit

        currentBody["body_type"] = {"name": "Type of body of water", "value": bodyType}

        lastTemp, offset = getSome("i", buff, offset)
        bodyName = "Last {} Temperature".format(BODY_TYPE.NAME_FOR_NUM[bodyType])
        currentBody["last_temperature"] = {
            "name": bodyName,
            "value": lastTemp,
            "unit": temperature_unit,
            "device_type": DEVICE_TYPE.TEMPERATURE,
            "state_type": STATE_TYPE.MEASUREMENT,
        }

        heatStatus, offset = getSome("i", buff, offset)
        heaterName = "{} Heat".format(BODY_TYPE.NAME_FOR_NUM[bodyType])
        currentBody["heat_status"] = {"name": heaterName, "value": heatStatus}

        heatSetPoint, offset = getSome("i", buff, offset)
        hspName = "{} Heat Set Point".format(BODY_TYPE.NAME_FOR_NUM[bodyType])
        currentBody["heat_set_point"] = {
            "name": hspName,
            "value": heatSetPoint,
            "unit": temperature_unit,
            "device_type": DEVICE_TYPE.TEMPERATURE,
        }

        coolSetPoint, offset = getSome("i", buff, offset)
        cspName = "{} Cool Set Point".format(BODY_TYPE.NAME_FOR_NUM[bodyType])
        currentBody["cool_set_point"] = {
            "name": cspName,
            "value": coolSetPoint,
            "unit": temperature_unit,
        }

        heatMode, offset = getSome("i", buff, offset)
        hmName = "{} Heat Mode".format(BODY_TYPE.NAME_FOR_NUM[bodyType])
        currentBody["heat_mode"] = {
            "name": hmName,
            "value": heatMode,
        }

    circuitCount, offset = getSome("I", buff, offset)

    circuits: dict = data.setdefault(DATA.KEY_CIRCUITS, {})

    for i in range(circuitCount):
        circuitID, offset = getSome("I", buff, offset)

        currentCircuit = circuits.setdefault(circuitID, {})

        if "id" not in currentCircuit:
            currentCircuit["id"] = circuitID

        circuitState, offset = getSome("I", buff, offset)
        currentCircuit["value"] = circuitState

        cColorSet, offset = getSome("B", buff, offset)
        currentCircuit["color_set"] = cColorSet

        cColorPos, offset = getSome("B", buff, offset)
        currentCircuit["color_position"] = cColorPos

        cColorStagger, offset = getSome("B", buff, offset)
        currentCircuit["color_stagger"] = cColorStagger

        circuitDelay, offset = getSome("B", buff, offset)
        currentCircuit["delay"] = circuitDelay

    pH, offset = getSome("i", buff, offset)
    sensors["ph"] = {
        "name": "pH",
        "value": (pH / 100),
        "unit": UNIT.PH,
        "state_type": STATE_TYPE.MEASUREMENT,
    }

    orp, offset = getSome("i", buff, offset)
    sensors["orp"] = {
        "name": "ORP",
        "value": orp,
        "unit": UNIT.MILLIVOLT,
        "state_type": STATE_TYPE.MEASUREMENT,
    }

    saturation, offset = getSome("i", buff, offset)
    sensors["saturation"] = {
        "name": "Saturation Index",
        "value": (saturation / 100),
        "unit": UNIT.SATURATION_INDEX,
        "state_type": STATE_TYPE.MEASUREMENT,
    }

    saltPPM, offset = getSome("i", buff, offset)
    sensors["salt_ppm"] = {
        "name": "Salt",
        "value": (saltPPM * 50),
        "unit": UNIT.PARTS_PER_MILLION,
        "state_type": STATE_TYPE.MEASUREMENT,
    }

    pHTank, offset = getSome("i", buff, offset)
    sensors["ph_supply_level"] = {
        "name": "pH Supply Level",
        "value": pHTank,
        "state_type": STATE_TYPE.MEASUREMENT,
    }

    orpTank, offset = getSome("i", buff, offset)
    sensors["orp_supply_level"] = {
        "name": "ORP Supply Level",
        "value": orpTank,
        "state_type": STATE_TYPE.MEASUREMENT,
    }

    alarm, offset = getSome("i", buff, offset)
    sensors["chem_alarm"] = {
        "name": "Chemistry Alarm",
        "value": alarm,
        "device_type": DEVICE_TYPE.ALARM,
    }
