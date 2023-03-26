# import json
import struct

from ..const import (
    CODE,
    BODY_TYPE,
    DEVICE_TYPE,
    ON_OFF,
    STATE_TYPE,
    UNIT,
)
from ..data import ATTR, DEVICE, KEY, VALUE, UNKNOWN
from .protocol import ScreenLogicProtocol
from .request import async_make_request
from .utility import getSome, getTemperatureUnit


async def async_request_pool_status(
    protocol: ScreenLogicProtocol, data: dict, max_retries: int
) -> bytes:
    if result := await async_make_request(
        protocol, CODE.POOLSTATUS_QUERY, struct.pack("<I", 0), max_retries
    ):
        decode_pool_status(result, data)
        return result


def decode_pool_status(buff: bytes, data: dict) -> None:
    controller: dict = data.setdefault(DEVICE.CONTROLLER, {})

    controller[VALUE.STATUS], offset = getSome("I", buff, 0)  # byte offset 0

    controller_sensor: dict = controller.setdefault(KEY.SENSOR, {})

    freezeMode, offset = getSome("B", buff, offset)  # byte offset 4
    controller_sensor[VALUE.FREEZE_MODE] = {
        ATTR.NAME: "Freeze Mode",
        ATTR.VALUE: ON_OFF.from_bool(freezeMode & 0x08),
    }

    controller_config: dict = controller.setdefault(KEY.CONFIGURATION, {})

    controller_config[VALUE.REMOTES], offset = getSome("B", buff, offset)  # 5

    poolDelay, offset = getSome("B", buff, offset)  # 6
    controller_sensor[VALUE.POOL_DELAY] = {
        ATTR.NAME: "Pool Delay",
        ATTR.VALUE: poolDelay,
    }

    spaDelay, offset = getSome("B", buff, offset)  # 7
    controller_sensor[VALUE.SPA_DELAY] = {
        ATTR.NAME: "Spa Delay",
        ATTR.VALUE: spaDelay,
    }

    cleanerDelay, offset = getSome("B", buff, offset)  # 8
    controller_sensor[VALUE.CLEANER_DELAY] = {
        ATTR.NAME: "Cleaner Delay",
        ATTR.VALUE: cleanerDelay,
    }

    controller_config[UNKNOWN(offset)], offset = getSome("B", buff, offset)  # 9
    controller_config[UNKNOWN(offset)], offset = getSome("B", buff, offset)  # 10
    controller_config[UNKNOWN(offset)], offset = getSome("B", buff, offset)  # 11

    temperature_unit = getTemperatureUnit(data)

    airTemp, offset = getSome("i", buff, offset)  # 12
    controller_sensor[VALUE.AIR_TEMPERATURE] = {
        ATTR.NAME: "Air Temperature",
        ATTR.VALUE: airTemp,
        ATTR.UNIT: temperature_unit,
        ATTR.DEVICE_TYPE: DEVICE_TYPE.TEMPERATURE,
        ATTR.STATE_TYPE: STATE_TYPE.MEASUREMENT,
    }

    bodiesCount, offset = getSome("I", buff, offset)  # 16

    # Should this default to 2?
    bodiesCount = min(bodiesCount, 2)

    body: dict = data.setdefault(DEVICE.BODY, {})

    for i in range(bodiesCount):
        body_indexed: dict = body.setdefault(i, {})

        bodyType, offset = getSome("I", buff, offset)
        if bodyType not in [type_.value for type_ in BODY_TYPE]:
            bodyType = 0

        body_indexed[ATTR.BODY_TYPE] = bodyType

        body_name = BODY_TYPE(bodyType).title

        lastTemp, offset = getSome("i", buff, offset)
        body_indexed[VALUE.LAST_TEMPERATURE] = {
            ATTR.NAME: f"Last {body_name} Temperature",
            ATTR.VALUE: lastTemp,
            ATTR.UNIT: temperature_unit,
            ATTR.DEVICE_TYPE: DEVICE_TYPE.TEMPERATURE,
            ATTR.STATE_TYPE: STATE_TYPE.MEASUREMENT,
        }

        heatStatus, offset = getSome("i", buff, offset)
        body_indexed[VALUE.HEAT_STATE] = {
            ATTR.NAME: f"{body_name} Heat",
            ATTR.VALUE: heatStatus,
        }

        heatSetPoint, offset = getSome("i", buff, offset)
        body_indexed[VALUE.HEAT_SETPOINT] = {
            ATTR.NAME: f"{body_name} Heat Set Point",
            ATTR.VALUE: heatSetPoint,
            ATTR.UNIT: temperature_unit,
            ATTR.DEVICE_TYPE: DEVICE_TYPE.TEMPERATURE,
        }

        coolSetPoint, offset = getSome("i", buff, offset)
        body_indexed[VALUE.COOL_SETPOINT] = {
            ATTR.NAME: f"{body_name} Cool Set Point",
            ATTR.VALUE: coolSetPoint,
            ATTR.UNIT: temperature_unit,
        }

        heatMode, offset = getSome("i", buff, offset)
        body_indexed[VALUE.HEAT_MODE] = {
            ATTR.NAME: f"{body_name} Heat Mode",
            ATTR.VALUE: heatMode,
        }

    circuitCount, offset = getSome("I", buff, offset)

    circuit: dict = data.setdefault(DEVICE.CIRCUIT, {})

    for i in range(circuitCount):
        circuit_id, offset = getSome("I", buff, offset)

        circuit_indexed: dict = circuit.setdefault(circuit_id, {})

        if "id" not in circuit_indexed:
            circuit_indexed[ATTR.CIRCUIT_ID] = circuit_id

        circuit_indexed_state: dict = circuit_indexed.setdefault(VALUE.STATE, {})

        circuit_indexed_state[ATTR.VALUE], offset = getSome("I", buff, offset)

        color_set, offset = getSome("B", buff, offset)
        color_position, offset = getSome("B", buff, offset)
        color_stagger, offset = getSome("B", buff, offset)
        circuit_indexed[KEY.COLOR] = {
            ATTR.COLOR_SET: color_set,
            ATTR.COLOR_POSITION: color_position,
            ATTR.COLOR_STAGGER: color_stagger,
        }

        circuit_indexed_config: dict = circuit_indexed.setdefault(KEY.CONFIGURATION, {})
        circuit_indexed_config[ATTR.DELAY], offset = getSome("B", buff, offset)

    pH, offset = getSome("i", buff, offset)
    controller_sensor[VALUE.PH] = {
        ATTR.NAME: "pH",
        ATTR.VALUE: (pH / 100),
        ATTR.UNIT: UNIT.PH,
        ATTR.STATE_TYPE: STATE_TYPE.MEASUREMENT,
    }

    orp, offset = getSome("i", buff, offset)
    controller_sensor[VALUE.ORP] = {
        ATTR.NAME: "ORP",
        ATTR.VALUE: orp,
        ATTR.UNIT: UNIT.MILLIVOLT,
        ATTR.STATE_TYPE: STATE_TYPE.MEASUREMENT,
    }

    saturation, offset = getSome("i", buff, offset)
    controller_sensor[VALUE.SATURATION] = {
        ATTR.NAME: "Saturation Index",
        ATTR.VALUE: (saturation / 100),
        ATTR.UNIT: UNIT.SATURATION_INDEX,
        ATTR.STATE_TYPE: STATE_TYPE.MEASUREMENT,
    }

    saltPPM, offset = getSome("i", buff, offset)
    controller_sensor[VALUE.SALT_PPM] = {
        ATTR.NAME: "Salt",
        ATTR.VALUE: (saltPPM * 50),
        ATTR.UNIT: UNIT.PARTS_PER_MILLION,
        ATTR.STATE_TYPE: STATE_TYPE.MEASUREMENT,
    }

    pHTank, offset = getSome("i", buff, offset)
    controller_sensor[VALUE.PH_SUPPLY_LEVEL] = {
        ATTR.NAME: "pH Supply Level",
        ATTR.VALUE: pHTank,
        ATTR.STATE_TYPE: STATE_TYPE.MEASUREMENT,
    }

    orpTank, offset = getSome("i", buff, offset)
    controller_sensor[VALUE.ORP_SUPPLY_LEVEL] = {
        ATTR.NAME: "ORP Supply Level",
        ATTR.VALUE: orpTank,
        ATTR.STATE_TYPE: STATE_TYPE.MEASUREMENT,
    }

    alarm, offset = getSome("i", buff, offset)
    controller_sensor[VALUE.ACTIVE_ALARM] = {
        ATTR.NAME: "Active Alarm",
        ATTR.VALUE: alarm,
        ATTR.DEVICE_TYPE: DEVICE_TYPE.ALARM,
    }
