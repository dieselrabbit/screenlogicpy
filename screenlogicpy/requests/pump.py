# import json
import asyncio
import struct

from ..const import CODE, DATA, DEVICE_TYPE, MESSAGE, ScreenLogicWarning
from .protocol import ScreenLogicProtocol
from .utility import getSome


async def async_request_pump_status(protocol: ScreenLogicProtocol, data, pumpID):
    try:
        await asyncio.wait_for(
            (
                request := protocol.await_send_message(
                    CODE.PUMPSTATUS_QUERY, struct.pack("<II", 0, pumpID)
                )
            ),
            MESSAGE.COM_TIMEOUT,
        )
        if not request.cancelled():
            decode_pump_status(request.result(), data, pumpID)
    except asyncio.TimeoutError:
        raise ScreenLogicWarning(f"Timeout poiling pump {pumpID} status")


# pylint: disable=unused-variable
def decode_pump_status(buff, data, pumpID):
    # print(buff)
    if DATA.KEY_PUMPS not in data:
        data[DATA.KEY_PUMPS] = {}

    if pumpID not in data[DATA.KEY_PUMPS]:
        data[DATA.KEY_PUMPS][pumpID] = {}

    pump = data[DATA.KEY_PUMPS][pumpID]
    pump["name"] = ""
    pump["pumpType"], offset = getSome("I", buff, 0)
    pump["state"], offset = getSome("I", buff, offset)

    curW, offset = getSome("I", buff, offset)
    pump["currentWatts"] = {}  # Need to find value when unsupported.

    curR, offset = getSome("I", buff, offset)
    pump["currentRPM"] = {}  # Need to find value when unsupported.

    unknown1, offset = getSome("I", buff, offset)

    curG, offset = getSome("I", buff, offset)
    if curG != 255:  # GPM reads 255 when unsupported.
        pump["currentGPM"] = {}

    unknown2, offset = getSome("I", buff, offset)

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
            "unit": "W",
            "device_type": DEVICE_TYPE.ENERGY,
        }

    if "currentRPM" in pump:
        pump["currentRPM"] = {
            "name": pump["name"] + " Current RPM",
            "value": curR,
            "unit": "rpm",
        }

    if "currentGPM" in pump:
        pump["currentGPM"] = {
            "name": pump["name"] + " Current GPM",
            "value": curG,
            "unit": "gpm",
        }
    # print(json.dumps(data, indent=4))
