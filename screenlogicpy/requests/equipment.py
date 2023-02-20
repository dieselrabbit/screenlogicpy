import struct

from ..const import CODE
from .protocol import ScreenLogicProtocol
from .request import async_make_request
from .utility import getSome, getArray


async def async_request_equipment_config(
    protocol: ScreenLogicProtocol, data: dict, max_retries: int
) -> bytes:
    if result := await async_make_request(
        protocol, CODE.EQUIPMENT_QUERY, struct.pack("<2I", 0, 0), max_retries
    ):
        decode_equipment_config(result, data)
        return result


def decode_equipment_config(buff: bytes, data: dict) -> None:
    equip = data.setdefault("equipment", {})

    equip["controllerType"], offset = getSome("B", buff, 0)
    equip["hardwareType"], offset = getSome("B", buff, offset)

    equip[f"unknown_at_offset_{offset:02}"], offset = getSome("B", buff, offset)
    equip[f"unknown_at_offset_{offset:02}"], offset = getSome("B", buff, offset)
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
