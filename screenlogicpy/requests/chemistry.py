# import json
import asyncio
import struct

from ..const import (
    CHEMISTRY,
    CODE,
    DATA,
    DEVICE_TYPE,
    MESSAGE,
    ON_OFF,
    ScreenLogicWarning,
)
from .protocol import ScreenLogicProtocol
from .utility import getSome, getTemperatureUnit, packResponse


async def async_request_chemistry(protocol: ScreenLogicProtocol, data: dict):
    try:
        await asyncio.wait_for(
            (
                request := protocol.await_send_message(
                    CODE.CHEMISTRY_QUERY, struct.pack("<I", 0)
                )
            ),
            MESSAGE.COM_TIMEOUT,
        )
        if not request.cancelled():
            return packResponse(
                *decode_chemistry(request.result(), getTemperatureUnit(data))
            )
    except asyncio.TimeoutError:
        raise ScreenLogicWarning("Timeout polling chemistry status")


# pylint: disable=unused-variable
def decode_chemistry(buff, temp_unit):
    def is_set(bits, mask) -> bool:
        return True if (bits & mask) == mask else False

    data = {}

    chemistry: dict = data.setdefault(DATA.KEY_CHEMISTRY, {})

    offset = 0

    # size of msg?
    chemistry[f"unknown_at_offset_{offset:02}"], offset = getSome("I", buff, offset)

    # unknown value
    chemistry[f"unknown_at_offset_{offset:02}"], offset = getSome("B", buff, offset)

    pH, offset = getSome(">H", buff, offset)  # 1
    chemistry["current_ph"] = {"name": "Current pH", "value": (pH / 100), "unit": "pH"}

    orp, offset = getSome(">H", buff, offset)  # 3
    chemistry["current_orp"] = {"name": "Current ORP", "value": orp, "unit": "mV"}

    pHSetpoint, offset = getSome(">H", buff, offset)  # 5
    chemistry["ph_setpoint"] = {
        "name": "pH Setpoint",
        "value": (pHSetpoint / 100),
        "unit": "pH",
    }

    orpSetpoint, offset = getSome(">H", buff, offset)  # 7
    chemistry["orp_setpoint"] = {
        "name": "ORP Setpoint",
        "value": orpSetpoint,
        "unit": "mV",
    }

    pHDoseTime, offset = getSome(">I", buff, offset)  # 9
    chemistry["ph_last_dose_time"] = {
        "name": "Last pH Dose Time",
        "value": pHDoseTime,
        "unit": "Sec",
    }

    orpDoseTime, offset = getSome(">I", buff, offset)  # 13
    chemistry["orp_last_dose_time"] = {
        "name": "Last ORP Dose Time",
        "value": orpDoseTime,
        "unit": "Sec",
    }

    pHDoseVolume, offset = getSome(">H", buff, offset)  # 17
    chemistry["ph_last_dose_volume"] = {
        "name": "Last pH Dose Volume",
        "value": pHDoseVolume,
        "unit": "mL",
    }

    orpDoseVolume, offset = getSome(">H", buff, offset)  # 19
    chemistry["orp_last_dose_volume"] = {
        "name": "Last ORP Dose Volume",
        "value": orpDoseVolume,
        "unit": "mL",
    }

    pHSupplyLevel, offset = getSome("B", buff, offset)  # 21 (20)
    chemistry["ph_supply_level"] = {"name": "pH Supply Level", "value": pHSupplyLevel}

    orpSupplyLevel, offset = getSome("B", buff, offset)  # 22 (21)
    chemistry["orp_supply_level"] = {
        "name": "ORP Supply Level",
        "value": orpSupplyLevel,
    }

    saturation, offset = getSome("B", buff, offset)  # 23
    chemistry["saturation"] = {
        "name": "Saturation Index",
        "value": (saturation - 256) / 100
        if is_set(saturation, 0x80)
        else saturation / 100,
        "unit": "lsi",
    }

    cal, offset = getSome(">H", buff, offset)  # 24
    chemistry["calcium_harness"] = {
        "name": "Calcium Hardness",
        "value": cal,
        "unit": "ppm",
    }

    cya, offset = getSome(">H", buff, offset)  # 26
    chemistry["cya"] = {"name": "Cyanuric Acid", "value": cya, "unit": "ppm"}

    alk, offset = getSome(">H", buff, offset)  # 28
    chemistry["total_alkalinity"] = {
        "name": "Total Alkalinity",
        "value": alk,
        "unit": "ppm",
    }

    saltPPM, offset = getSome("B", buff, offset)  # 30
    chemistry["salt_tds_ppm"] = {
        "name": "Salt/TDS",
        "value": (saltPPM * 50),
        "unit": "ppm",
    }

    # Probe temp unit is Celsius?
    probIsC, offset = getSome("B", buff, offset)
    chemistry["probe_is_celsius"] = probIsC

    waterTemp, offset = getSome("B", buff, offset)  # 32
    chemistry["ph_probe_water_temp"] = {
        "name": "pH Probe Water Temperature",
        "value": waterTemp,
        "unit": temp_unit,
        "device_type": DEVICE_TYPE.TEMPERATURE,
    }

    alerts = chemistry.setdefault(DATA.KEY_ALERTS, {})

    alarms, offset = getSome("B", buff, offset)  # 33 (32)
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

    unkPos = offset
    warnings, offset = getSome("B", buff, offset)  # 34
    chemistry[f"unknown_at_offset_{unkPos:02}"] = warnings

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

    status, offset = getSome("B", buff, offset)  # 35 (34)
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
    }
    chemistry["orp_dosing_state"] = {
        "name": "ORP Dosing State",
        "value": (status & CHEMISTRY.MASK_STATUS_ORP_DOSING) >> 6,
    }

    flags, offset = getSome("B", buff, offset)  # 36 (35)
    chemistry["flags"] = flags

    vMinor, offset = getSome("B", buff, offset)  # 37 (36)
    vMajor, offset = getSome("B", buff, offset)  # 38 (37)
    chemistry["firmware"] = {
        "name": "IntelliChem Firmware Version",
        "value": f"{vMajor}.{vMinor:03}",
    }

    chemistry[f"unknown_at_offset_{offset:02}"], offset = getSome("B", buff, offset)
    chemistry[f"unknown_at_offset_{offset:02}"], offset = getSome("B", buff, offset)
    chemistry[f"unknown_at_offset_{offset:02}"], offset = getSome("B", buff, offset)
    chemistry[f"unknown_at_offset_{offset:02}"], offset = getSome("B", buff, offset)

    return buff, data
