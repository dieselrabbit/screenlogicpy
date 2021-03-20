# import json
import struct
from ..const import code, DEVICE_TYPE, UNIT
from .utility import sendRecieveMessage, getSome


def request_chemistry(gateway_socket, data):
    response = sendRecieveMessage(
        gateway_socket, code.CHEMISTRY_QUERY, struct.pack("<I", 0)
    )
    decode_chemistry(response, data)


# pylint: disable=unused-variable
def decode_chemistry(buff, data):
    # print(buff)

    if "chemistry" not in data:
        data["chemistry"] = {}

    chemistry = data["chemistry"]

    unittxt = (
        UNIT.CELSIUS
        if "config" in data
        and "is_celcius" in data["config"]
        and data["config"]["is_celcius"]["value"]
        else UNIT.FAHRENHEIHT
    )

    size, offset = getSome("I", buff, 0)  # 0

    # if 'unknown' not in chemistry:
    #    chemistry['unknown'] = {}

    # unknown = chemistry['unknown']

    # skip an unknown value
    unknown1, offset = getSome("B", buff, offset)  # 4
    # unknown['unknown1'] = unknown1

    pH, offset = getSome(">H", buff, offset)  # 5
    chemistry["current_ph"] = {"name": "Current pH", "value": (pH / 100), "unit": "pH"}

    orp, offset = getSome(">H", buff, offset)  # 7
    chemistry["current_orp"] = {"name": "Current ORP", "value": orp, "unit": "mV"}

    pHSetpoint, offset = getSome(">H", buff, offset)  # 9
    chemistry["ph_setpoint"] = {
        "name": "pH Setpoint",
        "value": (pHSetpoint / 100),
        "unit": "pH",
    }

    orpSetpoint, offset = getSome(">H", buff, offset)  # 11
    chemistry["orp_setpoint"] = {
        "name": "ORP Setpoint",
        "value": orpSetpoint,
        "unit": "mV",
    }

    # fast forward 12 bytes
    # Seems to be '>I' x2 and '>H' x2
    # Values change when pH and ORP dosing but I was unable to decode
    offset += 12

    pHSupplyLevel, offset = getSome("B", buff, offset)  # 25
    chemistry["ph_supply_level"] = {"name": "pH Supply Level", "value": pHSupplyLevel}

    orpSupplyLevel, offset = getSome("B", buff, offset)  # 26
    chemistry["orp_supply_level"] = {
        "name": "ORP Supply Level",
        "value": orpSupplyLevel,
    }

    saturation, offset = getSome("B", buff, offset)  # 27
    saturation -= 256
    chemistry["saturation"] = {
        "name": "Saturation Index",
        "value": (saturation / 100),
        "unit": "lsi",
    }

    cal, offset = getSome(">H", buff, offset)  # 28
    chemistry["calcium_harness"] = {
        "name": "Calcium Hardness",
        "value": cal,
        "unit": "ppm",
    }

    cya, offset = getSome(">H", buff, offset)  # 30
    chemistry["cya"] = {"name": "Cyanuric Acid", "value": cya, "unit": "ppm"}

    alk, offset = getSome(">H", buff, offset)  # 32
    chemistry["total_alkalinity"] = {
        "name": "Total Alkalinity",
        "value": alk,
        "unit": "ppm",
    }

    saltPPM, offset = getSome("H", buff, offset)  # 34
    chemistry["salt_ppm"] = {"name": "Salt", "value": (saltPPM * 50), "unit": "ppm"}

    waterTemp, offset = getSome("B", buff, offset)  # 36
    chemistry["current_water_temperature"] = {
        "name": "Current Water Temperature",
        "value": waterTemp,
        "unit": unittxt,
        "device_type": DEVICE_TYPE.TEMPERATURE,
    }

    flow, offset = getSome("B", buff, offset)  # 37
    chemistry["flow_alarm"] = {"name": "Flow Alarm", "value": flow & 1}
    # unknown['flow?'] = flow & 1

    unknown3, offset = getSome("B", buff, offset)  # 37
    # unknown['unknown3'] = unknown3

    corosive, offset = getSome("B", buff, offset)  # 39
    # unknown['corosive?'] = corosivness
    chemistry["corosive"] = {"name": "Corosive", "value": corosive & 1}

    last1, offset = getSome("B", buff, offset)  # 40
    # unknown['last1'] = last1
    last2, offset = getSome("B", buff, offset)  # 41
    # unknown['last2'] = last2

    # print(json.dumps(data, indent=4))
