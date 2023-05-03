import struct

from ..const.common import DEVICE_TYPE, STATE_TYPE, UNIT
from ..const.data import ATTR, DEVICE, VALUE, UNKNOWN
from ..const.msg import CODE
from .protocol import ScreenLogicProtocol
from .request import async_make_request
from .utility import getSome


async def async_request_pump_status(
    protocol: ScreenLogicProtocol, data: dict, pump_index: int, max_retries: int
) -> bytes:
    if result := await async_make_request(
        protocol, CODE.PUMPSTATUS_QUERY, struct.pack("<II", 0, pump_index), max_retries
    ):
        decode_pump_status(result, data, pump_index)
        return result


def decode_pump_status(buff: bytes, data: dict, pump_index: int) -> None:
    pump: dict = data.setdefault(DEVICE.PUMP, {})

    pump_indexed: dict = pump.setdefault(pump_index, {})

    pump_indexed[VALUE.TYPE], offset = getSome("I", buff, 0)
    pump_state, offset = getSome("I", buff, offset)
    pump_indexed_state: dict = pump_indexed.setdefault(
        VALUE.STATE, {ATTR.NAME: "", ATTR.VALUE: 0}
    )
    # Filter wild values from pump state
    if not pump_state & 0x80000000:
        pump_indexed_state[ATTR.VALUE] = pump_state

    curW, offset = getSome("I", buff, offset)
    pump_indexed[VALUE.WATTS_NOW] = {}  # Need to find value when unsupported.

    curR, offset = getSome("I", buff, offset)
    pump_indexed[VALUE.RPM_NOW] = {}  # Need to find value when unsupported.

    pump_indexed[UNKNOWN(offset)], offset = getSome("I", buff, offset)

    curG, offset = getSome("I", buff, offset)
    if curG != 255:  # GPM reads 255 when unsupported.
        pump_indexed[VALUE.GPM_NOW] = {}

    pump_indexed[UNKNOWN(offset)], offset = getSome("I", buff, offset)

    pump_indexed_preset: dict = pump_indexed.setdefault(VALUE.PRESET, {})
    name = "Default"
    for i in range(8):
        pump_indexed_preset_indexed: dict = pump_indexed_preset.setdefault(i, {})
        pump_indexed_preset_indexed[ATTR.DEVICE_ID], offset = getSome("I", buff, offset)
        if DEVICE.CIRCUIT in data:
            for circuit in data[DEVICE.CIRCUIT].values():
                if (
                    pump_indexed_preset_indexed[ATTR.DEVICE_ID]
                    == circuit[ATTR.DEVICE_ID]
                    and name == "Default"
                ):
                    name = circuit[ATTR.NAME]
                    break
        pump_indexed_preset_indexed[ATTR.SETPOINT], offset = getSome("I", buff, offset)
        pump_indexed_preset_indexed[ATTR.IS_RPM], offset = getSome("I", buff, offset)

    name = name.strip().strip(",") + " Pump"
    pump_indexed_state[ATTR.NAME] = name

    if VALUE.WATTS_NOW in pump_indexed:
        pump_indexed[VALUE.WATTS_NOW] = {
            ATTR.NAME: f"{name} Watts Now",
            ATTR.VALUE: curW,
            ATTR.UNIT: UNIT.WATT,
            ATTR.DEVICE_TYPE: DEVICE_TYPE.POWER,
            ATTR.STATE_TYPE: STATE_TYPE.MEASUREMENT,
        }

    if VALUE.RPM_NOW in pump_indexed:
        pump_indexed[VALUE.RPM_NOW] = {
            ATTR.NAME: f"{name} RPM Now",
            ATTR.VALUE: curR,
            ATTR.UNIT: UNIT.REVOLUTIONS_PER_MINUTE,
            ATTR.STATE_TYPE: STATE_TYPE.MEASUREMENT,
        }

    if VALUE.GPM_NOW in pump_indexed:
        pump_indexed[VALUE.GPM_NOW] = {
            ATTR.NAME: f"{name} GPM Now",
            ATTR.VALUE: curG,
            ATTR.UNIT: UNIT.GALLONS_PER_MINUTE,
            ATTR.STATE_TYPE: STATE_TYPE.MEASUREMENT,
        }
