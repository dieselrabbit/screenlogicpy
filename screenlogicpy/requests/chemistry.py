# import json
import struct

from ..const import (
    CHEMISTRY,
    CHEM_DOSING_STATE,
    CODE,
    DATA,
    DEVICE_TYPE,
    ON_OFF,
    STATE_TYPE,
    UNIT,
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
    def is_set(bits, mask) -> bool:
        return True if (bits & mask) == mask else False

    chemistry: dict = data.setdefault(DATA.KEY_CHEMISTRY, {})

    offset = 0

    # size of msg?
    chemistry[f"unknown_at_offset_{offset:02}"], offset = getSome(
        "I", buff, offset
    )  # byte offset 0

    # unknown value
    chemistry[f"unknown_at_offset_{offset:02}"], offset = getSome(
        "B", buff, offset
    )  # byte offset 4

    pH, offset = getSome(">H", buff, offset)  # 5
    chemistry["current_ph"] = {
        "name": "Current pH",
        "value": (pH / 100),
        "unit": UNIT.PH,
        "state_type": STATE_TYPE.MEASUREMENT,
    }

    orp, offset = getSome(">H", buff, offset)  # 7
    chemistry["current_orp"] = {
        "name": "Current ORP",
        "value": orp,
        "unit": UNIT.MILLIVOLT,
        "state_type": STATE_TYPE.MEASUREMENT,
    }

    pHSetpoint, offset = getSome(">H", buff, offset)  # 9
    chemistry["ph_setpoint"] = {
        "name": "pH Setpoint",
        "value": (pHSetpoint / 100),
        "unit": UNIT.PH,
    }

    orpSetpoint, offset = getSome(">H", buff, offset)  # 11
    chemistry["orp_setpoint"] = {
        "name": "ORP Setpoint",
        "value": orpSetpoint,
        "unit": UNIT.MILLIVOLT,
    }

    pHDoseTime, offset = getSome(">I", buff, offset)  # 13
    chemistry["ph_last_dose_time"] = {
        "name": "Last pH Dose Time",
        "value": pHDoseTime,
        "unit": UNIT.SECOND,
        "device_type": DEVICE_TYPE.DURATION,
        "state_type": STATE_TYPE.TOTAL_INCREASING,
    }

    orpDoseTime, offset = getSome(">I", buff, offset)  # 17
    chemistry["orp_last_dose_time"] = {
        "name": "Last ORP Dose Time",
        "value": orpDoseTime,
        "unit": UNIT.SECOND,
        "device_type": DEVICE_TYPE.DURATION,
        "state_type": STATE_TYPE.TOTAL_INCREASING,
    }

    pHDoseVolume, offset = getSome(">H", buff, offset)  # 21
    chemistry["ph_last_dose_volume"] = {
        "name": "Last pH Dose Volume",
        "value": pHDoseVolume,
        "unit": UNIT.MILLILITER,
        "device_type": DEVICE_TYPE.VOLUME,
        "state_type": STATE_TYPE.TOTAL_INCREASING,
    }

    orpDoseVolume, offset = getSome(">H", buff, offset)  # 23
    chemistry["orp_last_dose_volume"] = {
        "name": "Last ORP Dose Volume",
        "value": orpDoseVolume,
        "unit": UNIT.MILLILITER,
        "device_type": DEVICE_TYPE.VOLUME,
        "state_type": STATE_TYPE.TOTAL_INCREASING,
    }

    pHSupplyLevel, offset = getSome("B", buff, offset)  # 25
    chemistry["ph_supply_level"] = {
        "name": "pH Supply Level",
        "value": pHSupplyLevel,
        "state_type": STATE_TYPE.MEASUREMENT,
    }

    orpSupplyLevel, offset = getSome("B", buff, offset)  # 26 (21)
    chemistry["orp_supply_level"] = {
        "name": "ORP Supply Level",
        "value": orpSupplyLevel,
        "state_type": STATE_TYPE.MEASUREMENT,
    }

    saturation, offset = getSome("B", buff, offset)  # 27
    chemistry["saturation"] = {
        "name": "Saturation Index",
        "value": (saturation - 256) / 100
        if is_set(saturation, 0x80)
        else saturation / 100,
        "unit": UNIT.SATURATION_INDEX,
        "state_type": STATE_TYPE.MEASUREMENT,
    }

    cal, offset = getSome(">H", buff, offset)  # 28
    chemistry["calcium_harness"] = {
        "name": "Calcium Hardness",
        "value": cal,
        "unit": UNIT.PARTS_PER_MILLION,
    }

    cya, offset = getSome(">H", buff, offset)  # 30
    chemistry["cya"] = {
        "name": "Cyanuric Acid",
        "value": cya,
        "unit": "ppm",
    }

    alk, offset = getSome(">H", buff, offset)  # 32
    chemistry["total_alkalinity"] = {
        "name": "Total Alkalinity",
        "value": alk,
        "unit": UNIT.PARTS_PER_MILLION,
    }

    saltPPM, offset = getSome("B", buff, offset)  # 34
    chemistry["salt_tds_ppm"] = {
        "name": "Salt/TDS",
        "value": (saltPPM * 50),
        "unit": UNIT.PARTS_PER_MILLION,
    }

    # Probe temp unit is Celsius?
    probIsC, offset = getSome("B", buff, offset)  # 35
    chemistry["probe_is_celsius"] = probIsC

    temperature_unit = getTemperatureUnit(data)

    waterTemp, offset = getSome("B", buff, offset)  # 36
    chemistry["ph_probe_water_temp"] = {
        "name": "pH Probe Water Temperature",
        "value": waterTemp,
        "unit": temperature_unit,
        "device_type": DEVICE_TYPE.TEMPERATURE,
        "state_type": STATE_TYPE.MEASUREMENT,
    }

    alerts = chemistry.setdefault(DATA.KEY_ALERTS, {})

    alarms, offset = getSome("B", buff, offset)  # 37 (32)
    alerts["_raw"] = alarms

    alerts["flow_alarm"] = {
        "name": "Flow Alarm",
        "value": ON_OFF.from_bool(is_set(alarms, CHEMISTRY.FLAG_ALARM_FLOW)),
        "device_type": DEVICE_TYPE.ALARM,
    }
    alerts["ph_alarm"] = {
        "name": "pH Alarm",
        "value": ON_OFF.from_bool(is_set(alarms, CHEMISTRY.FLAG_ALARM_PH)),
        "device_type": DEVICE_TYPE.ALARM,
    }
    alerts["orp_alarm"] = {
        "name": "ORP Alarm",
        "value": ON_OFF.from_bool(is_set(alarms, CHEMISTRY.FLAG_ALARM_ORP)),
        "device_type": DEVICE_TYPE.ALARM,
    }
    alerts["ph_supply_alarm"] = {
        "name": "pH Supply Alarm",
        "value": ON_OFF.from_bool(is_set(alarms, CHEMISTRY.FLAG_ALARM_PH_SUPPLY)),
        "device_type": DEVICE_TYPE.ALARM,
    }
    alerts["orp_supply_alarm"] = {
        "name": "ORP Supply Alarm",
        "value": ON_OFF.from_bool(is_set(alarms, CHEMISTRY.FLAG_ALARM_ORP_SUPPLY)),
        "device_type": DEVICE_TYPE.ALARM,
    }
    alerts["probe_fault_alarm"] = {
        "name": "Probe Fault",
        "value": ON_OFF.from_bool(is_set(alarms, CHEMISTRY.FLAG_ALARM_PROBE_FAULT)),
        "device_type": DEVICE_TYPE.ALARM,
    }

    notifications = chemistry.setdefault(DATA.KEY_NOTIFICATIONS, {})

    warnings, offset = getSome("B", buff, offset)  # 38 (33)
    notifications["_raw"] = warnings

    notifications["ph_lockout"] = {
        "name": "pH Lockout",
        "value": ON_OFF.from_bool(is_set(warnings, CHEMISTRY.FLAG_WARNING_PH_LOCKOUT)),
    }
    notifications["ph_limit"] = {
        "name": "pH Daily Limit Reached",
        "value": ON_OFF.from_bool(is_set(warnings, CHEMISTRY.FLAG_WARNING_PH_LIMIT)),
    }
    notifications["orp_limit"] = {
        "name": "ORP Daily Limit Reached",
        "value": ON_OFF.from_bool(is_set(warnings, CHEMISTRY.FLAG_WARNING_ORP_LIMIT)),
    }

    status, offset = getSome("B", buff, offset)  # 39 (34)
    chemistry["status"] = status
    # notifications["corrosive"] = {
    #    "name": "Corrosive",
    #    "value": ON_OFF.from_bool(is_set(status, CHEMISTRY.FLAG_STATUS_CORROSIVE)),
    # }
    # notifications["scaling"] = {
    #    "name": "Scaling",
    #    "value": ON_OFF.from_bool(is_set(status, CHEMISTRY.FLAG_STATUS_SCALING)),
    # }

    chemistry["ph_dosing_state"] = {
        "name": "pH Dosing State",
        "value": (status & CHEMISTRY.MASK_STATUS_PH_DOSING) >> 4,
        "device_type": DEVICE_TYPE.ENUM,
        "enum_options": [v for v in CHEM_DOSING_STATE.NAME_FOR_NUM.values()],
    }
    chemistry["orp_dosing_state"] = {
        "name": "ORP Dosing State",
        "value": (status & CHEMISTRY.MASK_STATUS_ORP_DOSING) >> 6,
        "device_type": DEVICE_TYPE.ENUM,
        "enum_options": [v for v in CHEM_DOSING_STATE.NAME_FOR_NUM.values()],
    }

    flags, offset = getSome("B", buff, offset)  # 40 (35)
    chemistry["flags"] = flags

    vMinor, offset = getSome("B", buff, offset)  # 41 (36)
    vMajor, offset = getSome("B", buff, offset)  # 42 (37)
    chemistry["firmware"] = {
        "name": "IntelliChem Firmware Version",
        "value": f"{vMajor}.{vMinor:03}",
    }

    chemistry[f"unknown_at_offset_{offset:02}"], offset = getSome("B", buff, offset)
    chemistry[f"unknown_at_offset_{offset:02}"], offset = getSome("B", buff, offset)
    chemistry[f"unknown_at_offset_{offset:02}"], offset = getSome("B", buff, offset)
    chemistry[f"unknown_at_offset_{offset:02}"], offset = getSome("B", buff, offset)


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
    return (
        await async_make_request(
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
        == b""
    )
