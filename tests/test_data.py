from unittest.mock import MagicMock, mock_open, patch

from screenlogicpy.data import (
    ScreenLogicResponseCollection,
    ScreenLogicResponseSet,
    build_response_collection,
    export_response_collection,
    import_response_collection,
)
from screenlogicpy.requests.gateway import decode_version
from screenlogicpy.requests.config import decode_pool_config
from screenlogicpy.requests.status import decode_pool_status
from screenlogicpy.requests.pump import decode_pump_status
from screenlogicpy.requests.chemistry import decode_chemistry
from screenlogicpy.requests.scg import decode_scg_config


def test_validate_complete(response_collection: ScreenLogicResponseCollection):
    data = {}
    decode_version(response_collection.version.raw, data)
    decode_pool_config(response_collection.config.raw, data)
    decode_pool_status(response_collection.status.raw, data)
    for idx, pump in enumerate(response_collection.pumps):
        decode_pump_status(pump.raw, data, idx)
    decode_chemistry(response_collection.chemistry.raw, data)
    decode_scg_config(response_collection.scg.raw, data)
    assert data == response_collection.decoded_complete


TEST_RAW_VERSION = b"\x19\x00\x00\x00POOL: 5.2 Build 736.0 Rel\x00\x00\x00\x02\x00\x00\x00\x05\x00\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00\x0c\x00\x00\x00"

TEST_RAW_PUMP_0 = b"\x03\x00\x00\x00\x01\x00\x00\x00\t\x05\x00\x00\xbd\n\x00\x00\x00\x00\x00\x00>\x00\x00\x00\xff\x00\x00\x00\x06\x00\x00\x00?\x00\x00\x00\x00\x00\x00\x00\t\x00\x00\x00H\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00z\r\x00\x00\x01\x00\x00\x00\x82\x00\x00\x00K\x00\x00\x00\x00\x00\x00\x00\x0c\x00\x00\x00H\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x1e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x1e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x1e\x00\x00\x00\x00\x00\x00\x00"

TEST_RAW_PUMP_1 = b"\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00\x02\x00\x00\x00\x8c\n\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x1e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x1e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x1e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x1e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x1e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x1e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x1e\x00\x00\x00\x00\x00\x00\x00"

TEST_DECODED_VERSION = {
    "adapter": {
        "firmware": {
            "name": "Protocol Adapter Firmware",
            "value": "POOL: 5.2 Build 736.0 Rel",
        }
    }
}

TEST_DECODED_PUMP_0 = {
    "pump": {
        0: {
            "type": 3,
            "state": {"name": "Default Pump", "value": 1},
            "watts_now": {
                "name": "Default Pump Watts Now",
                "value": 1289,
                "unit": "W",
                "device_type": "power",
                "state_type": "measurement",
            },
            "rpm_now": {
                "name": "Default Pump RPM Now",
                "value": 2749,
                "unit": "rpm",
                "state_type": "measurement",
            },
            "unknown_at_offset_16": 0,
            "gpm_now": {
                "name": "Default Pump GPM Now",
                "value": 62,
                "unit": "gpm",
                "state_type": "measurement",
            },
            "unknown_at_offset_24": 255,
            "preset": {
                0: {"device_id": 6, "setpoint": 63, "is_rpm": 0},
                1: {"device_id": 9, "setpoint": 72, "is_rpm": 0},
                2: {"device_id": 1, "setpoint": 3450, "is_rpm": 1},
                3: {"device_id": 130, "setpoint": 75, "is_rpm": 0},
                4: {"device_id": 12, "setpoint": 72, "is_rpm": 0},
                5: {"device_id": 0, "setpoint": 30, "is_rpm": 0},
                6: {"device_id": 0, "setpoint": 30, "is_rpm": 0},
                7: {"device_id": 0, "setpoint": 30, "is_rpm": 0},
            },
        }
    }
}

TEST_DECODED_PUMP_1 = {
    "pump": {
        1: {
            "type": 3,
            "state": {"name": "Default Pump", "value": 0},
            "watts_now": {
                "name": "Default Pump Watts Now",
                "value": 0,
                "unit": "W",
                "device_type": "power",
                "state_type": "measurement",
            },
            "rpm_now": {
                "name": "Default Pump RPM Now",
                "value": 0,
                "unit": "rpm",
                "state_type": "measurement",
            },
            "unknown_at_offset_16": 0,
            "gpm_now": {
                "name": "Default Pump GPM Now",
                "value": 0,
                "unit": "gpm",
                "state_type": "measurement",
            },
            "unknown_at_offset_24": 255,
            "preset": {
                0: {"device_id": 2, "setpoint": 2700, "is_rpm": 1},
                1: {"device_id": 0, "setpoint": 30, "is_rpm": 0},
                2: {"device_id": 0, "setpoint": 30, "is_rpm": 0},
                3: {"device_id": 0, "setpoint": 30, "is_rpm": 0},
                4: {"device_id": 0, "setpoint": 30, "is_rpm": 0},
                5: {"device_id": 0, "setpoint": 30, "is_rpm": 0},
                6: {"device_id": 0, "setpoint": 30, "is_rpm": 0},
                7: {"device_id": 0, "setpoint": 30, "is_rpm": 0},
            },
        }
    }
}

TEST_DATA = {
    "adapter": {
        "firmware": {
            "name": "Protocol Adapter Firmware",
            "value": "POOL: 5.2 Build 736.0 Rel",
        }
    },
    "pump": {
        0: {
            "type": 3,
            "state": {"name": "Default Pump", "value": 1},
            "watts_now": {
                "name": "Default Pump Watts Now",
                "value": 1289,
                "unit": "W",
                "device_type": "power",
                "state_type": "measurement",
            },
            "rpm_now": {
                "name": "Default Pump RPM Now",
                "value": 2749,
                "unit": "rpm",
                "state_type": "measurement",
            },
            "unknown_at_offset_16": 0,
            "gpm_now": {
                "name": "Default Pump GPM Now",
                "value": 62,
                "unit": "gpm",
                "state_type": "measurement",
            },
            "unknown_at_offset_24": 255,
            "preset": {
                0: {"device_id": 6, "setpoint": 63, "is_rpm": 0},
                1: {"device_id": 9, "setpoint": 72, "is_rpm": 0},
                2: {"device_id": 1, "setpoint": 3450, "is_rpm": 1},
                3: {"device_id": 130, "setpoint": 75, "is_rpm": 0},
                4: {"device_id": 12, "setpoint": 72, "is_rpm": 0},
                5: {"device_id": 0, "setpoint": 30, "is_rpm": 0},
                6: {"device_id": 0, "setpoint": 30, "is_rpm": 0},
                7: {"device_id": 0, "setpoint": 30, "is_rpm": 0},
            },
        },
        1: {
            "type": 3,
            "state": {"name": "Default Pump", "value": 0},
            "watts_now": {
                "name": "Default Pump Watts Now",
                "value": 0,
                "unit": "W",
                "device_type": "power",
                "state_type": "measurement",
            },
            "rpm_now": {
                "name": "Default Pump RPM Now",
                "value": 0,
                "unit": "rpm",
                "state_type": "measurement",
            },
            "unknown_at_offset_16": 0,
            "gpm_now": {
                "name": "Default Pump GPM Now",
                "value": 0,
                "unit": "gpm",
                "state_type": "measurement",
            },
            "unknown_at_offset_24": 255,
            "preset": {
                0: {"device_id": 2, "setpoint": 2700, "is_rpm": 1},
                1: {"device_id": 0, "setpoint": 30, "is_rpm": 0},
                2: {"device_id": 0, "setpoint": 30, "is_rpm": 0},
                3: {"device_id": 0, "setpoint": 30, "is_rpm": 0},
                4: {"device_id": 0, "setpoint": 30, "is_rpm": 0},
                5: {"device_id": 0, "setpoint": 30, "is_rpm": 0},
                6: {"device_id": 0, "setpoint": 30, "is_rpm": 0},
                7: {"device_id": 0, "setpoint": 30, "is_rpm": 0},
            },
        },
    },
}

TEST_LAST = {
    "version": TEST_RAW_VERSION,
    "pumps": {
        0: TEST_RAW_PUMP_0,
        1: TEST_RAW_PUMP_1,
    },
}

TEST_RC = ScreenLogicResponseCollection(
    TEST_DATA,
    version=ScreenLogicResponseSet(TEST_RAW_VERSION, TEST_DECODED_VERSION),
    pumps=[
        ScreenLogicResponseSet(TEST_RAW_PUMP_0, TEST_DECODED_PUMP_0),
        ScreenLogicResponseSet(TEST_RAW_PUMP_1, TEST_DECODED_PUMP_1),
    ],
)


def test_data_build_response_collection():
    rc = build_response_collection(TEST_LAST, TEST_DATA)
    assert rc == TEST_RC


def test_data_import_export_response_collection():
    written: str = ""

    def write(data):
        nonlocal written
        written += data

    mo: MagicMock = mock_open()
    handle = mo()
    handle.write.side_effect = write
    with patch("screenlogicpy.data.open", mo):
        export_response_collection(TEST_RC, "filename")
    mo.assert_called_with("filename", "w", encoding="utf-8")

    assert written

    with patch("screenlogicpy.data.open", mock_open(read_data=written)) as mo2:
        rc = import_response_collection("filename")
    mo2.assert_called_once_with("filename", "r", encoding="utf-8")
    assert rc == TEST_RC
