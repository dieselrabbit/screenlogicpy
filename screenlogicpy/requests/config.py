# import json
import struct

from ..const.msg import CODE
from ..const.data import ATTR, DEVICE, KEY, VALUE, UNKNOWN
from ..device_const.system import CONTROLLER, EQUIPMENT_FLAG, EQUIPMENT_MASK
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
    controller: dict = data.setdefault(DEVICE.CONTROLLER, {})

    controller[VALUE.CONTROLLER_ID], offset = getSome("I", buff, 0)

    controller_config: dict = controller.setdefault(KEY.CONFIGURATION, {})
    body_type_setpoint: dict = controller_config.setdefault(ATTR.BODY_TYPE, {})

    for i in range(2):
        body_type_setpoint_indexed: dict = body_type_setpoint.setdefault(i, {})

        minSetPoint, offset = getSome("B", buff, offset)
        body_type_setpoint_indexed[ATTR.MIN_SETPOINT] = minSetPoint

        maxSetPoint, offset = getSome("B", buff, offset)
        body_type_setpoint_indexed[ATTR.MAX_SETPOINT] = maxSetPoint

    degC, offset = getSome("B", buff, offset)
    controller_config[VALUE.IS_CELSIUS] = {
        ATTR.NAME: "Is Celsius",
        ATTR.VALUE: degC,
    }

    c_type, offset = getSome("B", buff, offset)
    controller_config[VALUE.CONTROLLER_TYPE] = c_type

    h_type, offset = getSome("B", buff, offset)
    controller_config[VALUE.HARDWARE_TYPE] = h_type

    controller[VALUE.MODEL] = {
        ATTR.NAME: "Model",
        ATTR.VALUE: CONTROLLER.model_from_type(c_type, h_type),
    }

    controller_config[VALUE.CONTROLLER_DATA], offset = getSome("B", buff, offset)

    controller_equipment: dict = controller.setdefault(KEY.EQUIPMENT, {})
    equipFlags, offset = getSome("I", buff, offset)

    # Include only known flags.
    controller_equipment[ATTR.FLAGS] = equipFlags & EQUIPMENT_MASK

    controller_equipment[VALUE.LIST] = [
        # What's needed? Friendly name or FLAG name?
        member.name  # .title
        for member in EQUIPMENT_FLAG
        if member in EQUIPMENT_FLAG(equipFlags)
    ]

    controller_config[VALUE.DEFAULT_CIRCUIT_NAME], offset = getString(buff, offset)

    circuitCount, offset = getSome("I", buff, offset)
    controller_config[VALUE.CIRCUIT_COUNT] = circuitCount

    circuit: dict = data.setdefault(DEVICE.CIRCUIT, {})

    for i in range(circuitCount):

        circuit_id, offset = getSome("i", buff, offset)

        circuit_indexed: dict = circuit.setdefault(circuit_id, {})

        circuit_indexed[ATTR.CIRCUIT_ID] = circuit_id

        circuit_indexed[ATTR.NAME], offset = getString(buff, offset)

        circuit_indexed_config: dict = circuit_indexed.setdefault(KEY.CONFIGURATION, {})
        circuit_indexed_config[ATTR.NAME_INDEX], offset = getSome("B", buff, offset)

        func, offset = getSome("B", buff, offset)
        circuit_indexed[ATTR.FUNCTION] = func  # CIRCUIT_FUNCTION(func)

        interface, offset = getSome("B", buff, offset)
        circuit_indexed[ATTR.INTERFACE] = interface  # INTERFACE_GROUP(interface)

        circuit_indexed_config[ATTR.FLAGS], offset = getSome("B", buff, offset)

        color_set, offset = getSome("B", buff, offset)
        color_position, offset = getSome("B", buff, offset)
        color_stagger, offset = getSome("B", buff, offset)
        circuit_indexed[KEY.COLOR] = {
            ATTR.COLOR_SET: color_set,
            ATTR.COLOR_POSITION: color_position,
            ATTR.COLOR_STAGGER: color_stagger,
        }

        circuit_indexed[ATTR.DEVICE_ID], offset = getSome("B", buff, offset)

        circuit_indexed_config[ATTR.DEFAULT_RUNTIME], offset = getSome(
            "H", buff, offset
        )

        circuit_indexed_config[UNKNOWN(offset)], offset = getSome("B", buff, offset)

        circuit_indexed_config[UNKNOWN(offset)], offset = getSome("B", buff, offset)

    colorCount, offset = getSome("I", buff, offset)
    controller_config[VALUE.COLOR_COUNT] = colorCount

    color: list = controller_config.setdefault(KEY.COLOR, [])

    for i in range(colorCount):
        colorName, offset = getString(buff, offset)
        rgbR, offset = getSome("I", buff, offset)
        rgbG, offset = getSome("I", buff, offset)
        rgbB, offset = getSome("I", buff, offset)
        color.append(
            {
                ATTR.NAME: colorName,
                ATTR.VALUE: (rgbR, rgbG, rgbB),
            }
        )

    pump_count = 8

    pump: dict = data.setdefault(DEVICE.PUMP, {})

    for i in range(pump_count):
        pump_indexed = pump.setdefault(i, {})

        pump_indexed[VALUE.DATA], offset = getSome("B", buff, offset)

    controller_config[VALUE.INTERFACE_TAB_FLAGS], offset = getSome("I", buff, offset)

    controller_config[VALUE.SHOW_ALARMS], offset = getSome("I", buff, offset)
