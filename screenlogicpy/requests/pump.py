import struct

from ..const import CODE, DATA, DEVICE_TYPE, STATE_TYPE, UNIT
from .protocol import ScreenLogicProtocol
from .request import async_make_request
from .utility import getSome


async def async_request_pump_status(
    protocol: ScreenLogicProtocol, data: dict, pumpID: int, max_retries: int
) -> bytes:
    if result := await async_make_request(
        protocol, CODE.PUMPSTATUS_QUERY, struct.pack("<II", 0, pumpID), max_retries
    ):
        decode_pump_status(result, data, pumpID)
        return result


def decode_pump_status(buff: bytes, data: dict, pumpID: int) -> None:
    pumps: dict = data.setdefault(DATA.KEY_PUMPS, {})

    pump = pumps.setdefault(pumpID, {})

    pump["name"] = ""
    pump["pumpType"], offset = getSome("I", buff, 0)
    pump["state"], offset = getSome("I", buff, offset)

    curW, offset = getSome("I", buff, offset)
    pump["currentWatts"] = {}  # Need to find value when unsupported.

    curR, offset = getSome("I", buff, offset)
    pump["currentRPM"] = {}  # Need to find value when unsupported.

    pump[f"unknown_at_offset_{offset:02}"], offset = getSome("I", buff, offset)

    curG, offset = getSome("I", buff, offset)
    if curG != 255:  # GPM reads 255 when unsupported.
        pump["currentGPM"] = {}

    pump[f"unknown_at_offset_{offset:02}"], offset = getSome("I", buff, offset)

    pump["presets"] = {}
    name = "Default"
    for i in range(8):
        pump["presets"][i] = {}
        pump["presets"][i]["cid"], offset = getSome("I", buff, offset)
        if DATA.KEY_CIRCUITS in data:
            for num, circuit in data[DATA.KEY_CIRCUITS].items():
                if (
                    pump["presets"][i]["cid"] == circuit["device_id"]
                    and name == "Default"
                ):
                    name = circuit["name"]
                    break
        pump["presets"][i]["setPoint"], offset = getSome("I", buff, offset)
        pump["presets"][i]["isRPM"], offset = getSome("I", buff, offset)

    name = name.strip().strip(",") + " Pump"
    pump["name"] = name

    if "currentWatts" in pump:
        pump["currentWatts"] = {
            "name": pump["name"] + " Current Watts",
            "value": curW,
            "unit": UNIT.WATT,
            "device_type": DEVICE_TYPE.POWER,
            "state_type": STATE_TYPE.MEASUREMENT,
        }

    if "currentRPM" in pump:
        pump["currentRPM"] = {
            "name": pump["name"] + " Current RPM",
            "value": curR,
            "unit": UNIT.REVOLUTIONS_PER_MINUTE,
            "state_type": STATE_TYPE.MEASUREMENT,
        }

    if "currentGPM" in pump:
        pump["currentGPM"] = {
            "name": pump["name"] + " Current GPM",
            "value": curG,
            "unit": UNIT.GALLONS_PER_MINUTE,
            "state_type": STATE_TYPE.MEASUREMENT,
        }
