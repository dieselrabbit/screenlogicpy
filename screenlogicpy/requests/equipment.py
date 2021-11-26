import asyncio
import struct

from ..const import CODE, MESSAGE, ScreenLogicWarning
from .protocol import ScreenLogicProtocol
from .utility import getSome, getArray


async def async_request_equipment_config(protocol: ScreenLogicProtocol, data):
    try:
        await asyncio.wait_for(
            (
                request := protocol.await_send_message(
                    CODE.EQUIPMENT_QUERY, struct.pack("<2I", 0, 0)
                )
            ),
            MESSAGE.COM_TIMEOUT,
        )
        if not request.cancelled():
            decode_equipment_config(request.result(), data)
    except asyncio.TimeoutError:
        raise ScreenLogicWarning("Timeout polling equipment config")


# pylint: disable=unused-variable
def decode_equipment_config(buff, data):
    if "equipment" not in data:
        data["equipment"] = {}

    equip = data["equipment"]

    equip["controllerType"], offset = getSome("B", buff, 0)
    equip["hardwareType"], offset = getSome("B", buff, offset)

    skip1, offset = getSome("B", buff, offset)
    skip2, offset = getSome("B", buff, offset)
    equip["controllerData"], offset = getSome("I", buff, offset)

    equip["versionDataArray"], offset = getArray(buff, offset)
    equip["speedDataArray"], offset = getArray(buff, offset)
    equip["valveDataArray"], offset = getArray(buff, offset)
    equip["remoteDataArray"], offset = getArray(buff, offset)
    equip["sensorDataArray"], offset = getArray(buff, offset)
    equip["delayDataArray"], offset = getArray(buff, offset)
    equip["macrosDataArray"], offset = getArray(buff, offset)
    equip["miscDataArray"], offset = getArray(buff, offset)
    equip["lightDataArray"], offset = getArray(buff, offset)
    equip["flowsDataArray"], offset = getArray(buff, offset)
    equip["sgsDataArray"], offset = getArray(buff, offset)
    equip["spaFlowsDataArray"], offset = getArray(buff, offset)
