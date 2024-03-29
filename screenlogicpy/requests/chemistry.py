# import json
import struct

from ..const.common import (
    DEVICE_TYPE,
    ON_OFF,
    STATE_TYPE,
    UNIT,
    ScreenLogicResponseError,
)
from ..const.data import ATTR, DEVICE, GROUP, VALUE, UNKNOWN
from ..const.msg import CODE
from ..device_const.chemistry import (
    ALARM_FLAG,
    ALERT_FLAG,
    BALANCE_FLAG,
    CHEM_RANGE,
    DOSE_MASK,
    DOSE_STATE,
)
from .protocol import ScreenLogicProtocol
from .request import async_make_request
from .utility import getSome, getTemperatureUnit


async def async_request_chemistry(
    protocol: ScreenLogicProtocol, data: dict, max_retries: int
) -> bytes:
    if result := await async_make_request(
        protocol, CODE.CHEMISTRY_QUERY, struct.pack("<I", 0), max_retries
    ):
        decode_chemistry(result, data)
        return result


# pylint: disable=unused-variable
def decode_chemistry(buff: bytes, data: dict) -> None:
    intellichem: dict = data.setdefault(DEVICE.INTELLICHEM, {})

    # size of msg?
    intellichem[UNKNOWN(0)], offset = getSome("I", buff, 0)  # byte offset 0

    # unknown value
    intellichem[UNKNOWN(offset)], offset = getSome("B", buff, offset)  # byte offset 4

    intellichem_sensor: dict = intellichem.setdefault(GROUP.SENSOR, {})

    pH, offset = getSome(">H", buff, offset)  # 5
    intellichem_sensor[VALUE.PH_NOW] = {
        ATTR.NAME: "pH Now",
        ATTR.VALUE: (pH / 100),
        ATTR.UNIT: UNIT.PH,
        ATTR.STATE_TYPE: STATE_TYPE.MEASUREMENT,
    }

    orp, offset = getSome(">H", buff, offset)  # 7
    intellichem_sensor[VALUE.ORP_NOW] = {
        ATTR.NAME: "ORP Now",
        ATTR.VALUE: orp,
        ATTR.UNIT: UNIT.MILLIVOLT,
        ATTR.STATE_TYPE: STATE_TYPE.MEASUREMENT,
    }

    intellichem_config: dict = intellichem.setdefault(GROUP.CONFIGURATION, {})

    pHSetpoint, offset = getSome(">H", buff, offset)  # 9
    intellichem_config[VALUE.PH_SETPOINT] = {
        ATTR.NAME: "pH Setpoint",
        ATTR.VALUE: (pHSetpoint / 100),
        ATTR.UNIT: UNIT.PH,
        ATTR.MIN_SETPOINT: CHEM_RANGE.PH_SETPOINT.minimum,
        ATTR.MAX_SETPOINT: CHEM_RANGE.PH_SETPOINT.maximum,
    }

    orpSetpoint, offset = getSome(">H", buff, offset)  # 11
    intellichem_config[VALUE.ORP_SETPOINT] = {
        ATTR.NAME: "ORP Setpoint",
        ATTR.VALUE: orpSetpoint,
        ATTR.UNIT: UNIT.MILLIVOLT,
        ATTR.MIN_SETPOINT: CHEM_RANGE.ORP_SETPOINT.minimum,
        ATTR.MAX_SETPOINT: CHEM_RANGE.ORP_SETPOINT.maximum,
    }

    intellichem_dosing: dict = intellichem.setdefault(GROUP.DOSE_STATUS, {})

    pHDoseTime, offset = getSome(">I", buff, offset)  # 13
    intellichem_dosing[VALUE.PH_LAST_DOSE_TIME] = {
        ATTR.NAME: "Last pH Dose Time",
        ATTR.VALUE: pHDoseTime,
        ATTR.UNIT: UNIT.SECOND,
        ATTR.DEVICE_TYPE: DEVICE_TYPE.DURATION,
        ATTR.STATE_TYPE: STATE_TYPE.TOTAL_INCREASING,
    }

    orpDoseTime, offset = getSome(">I", buff, offset)  # 17
    intellichem_dosing[VALUE.ORP_LAST_DOSE_TIME] = {
        ATTR.NAME: "Last ORP Dose Time",
        ATTR.VALUE: orpDoseTime,
        ATTR.UNIT: UNIT.SECOND,
        ATTR.DEVICE_TYPE: DEVICE_TYPE.DURATION,
        ATTR.STATE_TYPE: STATE_TYPE.TOTAL_INCREASING,
    }

    pHDoseVolume, offset = getSome(">H", buff, offset)  # 21
    intellichem_dosing[VALUE.PH_LAST_DOSE_VOLUME] = {
        ATTR.NAME: "Last pH Dose Volume",
        ATTR.VALUE: pHDoseVolume,
        ATTR.UNIT: UNIT.MILLILITER,
        ATTR.DEVICE_TYPE: DEVICE_TYPE.VOLUME,
        ATTR.STATE_TYPE: STATE_TYPE.TOTAL_INCREASING,
    }

    orpDoseVolume, offset = getSome(">H", buff, offset)  # 23
    intellichem_dosing[VALUE.ORP_LAST_DOSE_VOLUME] = {
        ATTR.NAME: "Last ORP Dose Volume",
        ATTR.VALUE: orpDoseVolume,
        ATTR.UNIT: UNIT.MILLILITER,
        ATTR.DEVICE_TYPE: DEVICE_TYPE.VOLUME,
        ATTR.STATE_TYPE: STATE_TYPE.TOTAL_INCREASING,
    }

    pHSupplyLevel, offset = getSome("B", buff, offset)  # 25
    intellichem_sensor[VALUE.PH_SUPPLY_LEVEL] = {
        ATTR.NAME: "pH Supply Level",
        ATTR.VALUE: pHSupplyLevel,
        ATTR.STATE_TYPE: STATE_TYPE.MEASUREMENT,
    }

    orpSupplyLevel, offset = getSome("B", buff, offset)  # 26 (21)
    intellichem_sensor[VALUE.ORP_SUPPLY_LEVEL] = {
        ATTR.NAME: "ORP Supply Level",
        ATTR.VALUE: orpSupplyLevel,
        ATTR.STATE_TYPE: STATE_TYPE.MEASUREMENT,
    }

    saturation, offset = getSome("B", buff, offset)  # 27
    intellichem_sensor[VALUE.SATURATION] = {
        ATTR.NAME: "Saturation Index",
        ATTR.VALUE: (saturation - 256) / 100 if saturation & 0x80 else saturation / 100,
        ATTR.UNIT: UNIT.SATURATION_INDEX,
        ATTR.STATE_TYPE: STATE_TYPE.MEASUREMENT,
    }

    cal, offset = getSome(">H", buff, offset)  # 28
    intellichem_config[VALUE.CALCIUM_HARDNESS] = {
        ATTR.NAME: "Calcium Hardness",
        ATTR.VALUE: cal,
        ATTR.UNIT: UNIT.PARTS_PER_MILLION,
        ATTR.MIN_SETPOINT: CHEM_RANGE.CALCIUM_HARDNESS.minimum,
        ATTR.MAX_SETPOINT: CHEM_RANGE.CALCIUM_HARDNESS.maximum,
    }

    cya, offset = getSome(">H", buff, offset)  # 30
    intellichem_config[VALUE.CYA] = {
        ATTR.NAME: "Cyanuric Acid",
        ATTR.VALUE: cya,
        ATTR.UNIT: UNIT.PARTS_PER_MILLION,
        ATTR.MIN_SETPOINT: CHEM_RANGE.CYANURIC_ACID.minimum,
        ATTR.MAX_SETPOINT: CHEM_RANGE.CYANURIC_ACID.maximum,
    }

    alk, offset = getSome(">H", buff, offset)  # 32
    intellichem_config[VALUE.TOTAL_ALKALINITY] = {
        ATTR.NAME: "Total Alkalinity",
        ATTR.VALUE: alk,
        ATTR.UNIT: UNIT.PARTS_PER_MILLION,
        ATTR.MIN_SETPOINT: CHEM_RANGE.TOTAL_ALKALINITY.minimum,
        ATTR.MAX_SETPOINT: CHEM_RANGE.TOTAL_ALKALINITY.maximum,
    }

    saltPPM, offset = getSome("B", buff, offset)  # 34
    intellichem_config[VALUE.SALT_TDS_PPM] = {
        ATTR.NAME: "Salt/TDS",
        ATTR.VALUE: (saltPPM * 50),
        ATTR.UNIT: UNIT.PARTS_PER_MILLION,
        ATTR.MIN_SETPOINT: CHEM_RANGE.SALT_TDS.minimum,
        ATTR.MAX_SETPOINT: CHEM_RANGE.SALT_TDS.maximum,
    }

    # Probe temp unit is Celsius?
    intellichem_config[VALUE.PROBE_IS_CELSIUS], offset = getSome(
        "B", buff, offset
    )  # 35

    temperature_unit = getTemperatureUnit(data)

    waterTemp, offset = getSome("B", buff, offset)  # 36
    intellichem_sensor[VALUE.PH_PROBE_WATER_TEMP] = {
        ATTR.NAME: "pH Probe Water Temperature",
        ATTR.VALUE: waterTemp,
        ATTR.UNIT: temperature_unit,
        ATTR.DEVICE_TYPE: DEVICE_TYPE.TEMPERATURE,
        ATTR.STATE_TYPE: STATE_TYPE.MEASUREMENT,
    }

    intellichem_alarm: dict = intellichem.setdefault(GROUP.ALARM, {})

    alarms, offset = getSome("B", buff, offset)  # 37 (32)
    intellichem_alarm[VALUE.FLAGS] = alarms

    intellichem_alarm[VALUE.FLOW_ALARM] = {
        ATTR.NAME: "Flow Alarm",
        ATTR.VALUE: ON_OFF.from_bool(alarms & ALARM_FLAG.FLOW).value,
        ATTR.DEVICE_TYPE: DEVICE_TYPE.ALARM,
    }
    intellichem_alarm[VALUE.PH_HIGH_ALARM] = {
        ATTR.NAME: "pH HIGH Alarm",
        ATTR.VALUE: ON_OFF.from_bool(alarms & ALARM_FLAG.PH_HIGH).value,
        ATTR.DEVICE_TYPE: DEVICE_TYPE.ALARM,
    }
    intellichem_alarm[VALUE.PH_LOW_ALARM] = {
        ATTR.NAME: "pH LOW Alarm",
        ATTR.VALUE: ON_OFF.from_bool(alarms & ALARM_FLAG.PH_LOW).value,
        ATTR.DEVICE_TYPE: DEVICE_TYPE.ALARM,
    }
    intellichem_alarm[VALUE.ORP_HIGH_ALARM] = {
        ATTR.NAME: "ORP HIGH Alarm",
        ATTR.VALUE: ON_OFF.from_bool(alarms & ALARM_FLAG.ORP_HIGH).value,
        ATTR.DEVICE_TYPE: DEVICE_TYPE.ALARM,
    }
    intellichem_alarm[VALUE.ORP_LOW_ALARM] = {
        ATTR.NAME: "ORP LOW Alarm",
        ATTR.VALUE: ON_OFF.from_bool(alarms & ALARM_FLAG.ORP_LOW).value,
        ATTR.DEVICE_TYPE: DEVICE_TYPE.ALARM,
    }
    intellichem_alarm[VALUE.PH_SUPPLY_ALARM] = {
        ATTR.NAME: "pH Supply Alarm",
        ATTR.VALUE: ON_OFF.from_bool(alarms & ALARM_FLAG.PH_SUPPLY).value,
        ATTR.DEVICE_TYPE: DEVICE_TYPE.ALARM,
    }
    intellichem_alarm[VALUE.ORP_SUPPLY_ALARM] = {
        ATTR.NAME: "ORP Supply Alarm",
        ATTR.VALUE: ON_OFF.from_bool(alarms & ALARM_FLAG.ORP_SUPPLY).value,
        ATTR.DEVICE_TYPE: DEVICE_TYPE.ALARM,
    }
    intellichem_alarm[VALUE.PROBE_FAULT_ALARM] = {
        ATTR.NAME: "Probe Fault",
        ATTR.VALUE: ON_OFF.from_bool(alarms & ALARM_FLAG.PROBE_FAULT).value,
        ATTR.DEVICE_TYPE: DEVICE_TYPE.ALARM,
    }

    intellichem_alert: dict = intellichem.setdefault(GROUP.ALERT, {})

    alerts, offset = getSome("B", buff, offset)  # 38 (33)
    intellichem_alert[VALUE.FLAGS] = alerts

    intellichem_alert[VALUE.PH_LOCKOUT] = {
        ATTR.NAME: "pH Lockout",
        ATTR.VALUE: ON_OFF.from_bool(alerts & ALERT_FLAG.PH_LOCKOUT).value,
    }
    intellichem_alert[VALUE.PH_LIMIT] = {
        ATTR.NAME: "pH Dose Limit Reached",
        ATTR.VALUE: ON_OFF.from_bool(alerts & ALERT_FLAG.PH_LIMIT).value,
    }
    intellichem_alert[VALUE.ORP_LIMIT] = {
        ATTR.NAME: "ORP Dose Limit Reached",
        ATTR.VALUE: ON_OFF.from_bool(alerts & ALERT_FLAG.ORP_LIMIT).value,
    }

    dose_flags, offset = getSome("B", buff, offset)  # 39 (34)
    intellichem_dosing[VALUE.FLAGS] = dose_flags

    intellichem_dosing[VALUE.PH_DOSING_STATE] = {
        ATTR.NAME: "pH Dosing State",
        ATTR.VALUE: (dose_flags & DOSE_MASK.PH_STATE) >> 4,
        ATTR.DEVICE_TYPE: DEVICE_TYPE.ENUM,
        ATTR.ENUM_OPTIONS: [state.title for state in DOSE_STATE],
    }
    intellichem_dosing[VALUE.ORP_DOSING_STATE] = {
        ATTR.NAME: "ORP Dosing State",
        ATTR.VALUE: (dose_flags & DOSE_MASK.ORP_STATE) >> 6,
        ATTR.DEVICE_TYPE: DEVICE_TYPE.ENUM,
        ATTR.ENUM_OPTIONS: [state.title for state in DOSE_STATE],
    }

    config_flags, offset = getSome("B", buff, offset)  # 40 (35)
    intellichem_config[VALUE.FLAGS] = config_flags

    vMinor, offset = getSome("B", buff, offset)  # 41 (36)
    vMajor, offset = getSome("B", buff, offset)  # 42 (37)
    intellichem[VALUE.FIRMWARE] = {
        ATTR.NAME: "IntelliChem Firmware",
        ATTR.VALUE: f"{vMajor}.{vMinor:03}",
        ATTR.MAJOR: vMajor,
        ATTR.MINOR: vMinor,
    }

    intellichem_balance: dict = intellichem.setdefault(GROUP.WATER_BALANCE, {})
    balance_flags, offset = getSome("B", buff, offset)  # 43
    intellichem_balance[VALUE.FLAGS] = balance_flags

    # SI <= -0.41
    intellichem_balance[VALUE.CORROSIVE] = {
        ATTR.NAME: "SI Corrosive",
        ATTR.VALUE: ON_OFF.from_bool(balance_flags & BALANCE_FLAG.CORROSIVE).value,
        ATTR.DEVICE_TYPE: DEVICE_TYPE.ALARM,
    }

    # SI >= +0.53
    intellichem_balance[VALUE.SCALING] = {
        ATTR.NAME: "SI Scaling",
        ATTR.VALUE: ON_OFF.from_bool(balance_flags & BALANCE_FLAG.SCALING).value,
        ATTR.DEVICE_TYPE: DEVICE_TYPE.ALARM,
    }

    intellichem[UNKNOWN(offset)], offset = getSome("B", buff, offset)  # 44
    intellichem[UNKNOWN(offset)], offset = getSome("B", buff, offset)  # 45
    intellichem[UNKNOWN(offset)], offset = getSome("B", buff, offset)  # 46


async def async_request_set_chem_data(
    protocol: ScreenLogicProtocol,
    ph_setpoint: int,
    orp_setpoint: int,
    calcium: int,
    alkalinity: int,
    cyanuric: int,
    salt: int,
    max_retries: int,
):
    if (
        response := await async_make_request(
            protocol,
            CODE.SETCHEMDATA_QUERY,
            struct.pack(
                "<7I",
                0,
                ph_setpoint,
                orp_setpoint,
                calcium,
                alkalinity,
                cyanuric,
                salt,
            ),
            max_retries,
        )
    ) != b"":
        raise ScreenLogicResponseError(
            f"Set chem data failed. Unexpected response: {response}"
        )
