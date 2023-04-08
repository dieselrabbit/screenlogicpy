import struct

from ..const.common import STATE_TYPE, UNIT
from ..const.msg import CODE, COM_MAX_RETRIES
from ..const.data import ATTR, DEVICE, KEY, VALUE
from ..device_const.scg import LIMIT_FOR_BODY, MAX_SC_RUNTIME
from ..device_const.system import BODY_TYPE
from .protocol import ScreenLogicProtocol
from .request import async_make_request
from .utility import getSome


async def async_request_scg_config(
    protocol: ScreenLogicProtocol, data: dict, max_retries: int
) -> bytes:
    if result := await async_make_request(
        protocol, CODE.SCGCONFIG_QUERY, struct.pack("<I", 0), max_retries
    ):
        decode_scg_config(result, data)
        return result


def decode_scg_config(buff: bytes, data: dict) -> None:
    scg: dict = data.setdefault(DEVICE.SCG, {})

    scg[VALUE.SCG_PRESENT], offset = getSome("I", buff, 0)  # 0

    scg_sensor: dict = scg.setdefault(KEY.SENSOR, {})

    state, offset = getSome("I", buff, offset)  # 4
    scg_sensor[VALUE.STATE] = {
        ATTR.NAME: "Chlorinator",
        ATTR.VALUE: state,
    }

    scg_config: dict = scg.setdefault(KEY.CONFIGURATION, {})

    level1, offset = getSome("I", buff, offset)  # 8
    scg_config[VALUE.POOL_SETPOINT] = {
        ATTR.NAME: "Pool Chlorinator Setpoint",
        ATTR.VALUE: level1,
        ATTR.UNIT: UNIT.PERCENT,
        ATTR.MIN_SETPOINT: 0,
        ATTR.MAX_SETPOINT: LIMIT_FOR_BODY[BODY_TYPE.POOL],
        ATTR.STEP: 5,
        ATTR.BODY_TYPE: BODY_TYPE.POOL.value,
    }

    level2, offset = getSome("I", buff, offset)  # 12
    scg_config[VALUE.SPA_SETPOINT] = {
        ATTR.NAME: "Spa Chlorinator Setpoint",
        ATTR.VALUE: level2,
        ATTR.UNIT: UNIT.PERCENT,
        ATTR.MIN_SETPOINT: 0,
        ATTR.MAX_SETPOINT: LIMIT_FOR_BODY[BODY_TYPE.SPA],
        ATTR.STEP: 5,
        ATTR.BODY_TYPE: BODY_TYPE.SPA.value,
    }

    salt, offset = getSome("I", buff, offset)  # 16
    scg_sensor[VALUE.SALT_PPM] = {
        ATTR.NAME: "Chlorinator Salt",
        ATTR.VALUE: (salt * 50),
        ATTR.UNIT: UNIT.PARTS_PER_MILLION,
        ATTR.STATE_TYPE: STATE_TYPE.MEASUREMENT,
    }

    flags, offset = getSome("I", buff, offset)  # 20
    scg[ATTR.FLAGS] = flags

    superChlorTimer, offset = getSome("I", buff, offset)  # 24
    scg_config[VALUE.SUPER_CHLOR_TIMER] = {
        ATTR.NAME: "Super Chlorination Timer",
        ATTR.VALUE: superChlorTimer,
        ATTR.UNIT: UNIT.HOUR,
        ATTR.MIN_SETPOINT: 1,
        ATTR.MAX_SETPOINT: MAX_SC_RUNTIME,
        ATTR.STEP: 1,
    }


async def async_request_set_scg_config(
    protocol: ScreenLogicProtocol,
    pool_output: int,
    spa_output: int,
    super_chlor: int = 0,
    super_time: int = 0,
    max_retries: int = COM_MAX_RETRIES,
) -> bool:
    return (
        await async_make_request(
            protocol,
            CODE.SETSCG_QUERY,
            struct.pack("<IIIII", 0, pool_output, spa_output, super_chlor, super_time),
            max_retries,
        )
        == b""
    )
