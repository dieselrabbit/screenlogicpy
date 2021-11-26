from .const_data import (
    EXPECTED_CONFIG_DATA,
    EXPECTED_STATUS_DATA,
    EXPECTED_PUMP_DATA,
    EXPECTED_CHEMISTRY_DATA,
    EXPECTED_SCG_DATA,
    FAKE_CONFIG_RESPONSE,
    FAKE_STATUS_RESPONSE,
    FAKE_PUMP_RESPONSE,
    FAKE_CHEMISTRY_RESPONSE,
    FAKE_SCG_RESPONSE,
)
from screenlogicpy.requests.config import decode_pool_config
from screenlogicpy.requests.status import decode_pool_status
from screenlogicpy.requests.pump import decode_pump_status
from screenlogicpy.requests.chemistry import decode_chemistry
from screenlogicpy.requests.scg import decode_scg_config
from screenlogicpy.requests.utility import makeMessage, takeMessages


def test_decode_config():
    data = {}
    decode_pool_config(FAKE_CONFIG_RESPONSE, data)

    assert data == EXPECTED_CONFIG_DATA


def test_decode_status():
    data = {}
    decode_pool_status(FAKE_STATUS_RESPONSE, data)

    assert data == EXPECTED_STATUS_DATA


def test_decode_pump():
    data = {}
    decode_pump_status(FAKE_PUMP_RESPONSE, data, 0)

    assert data == EXPECTED_PUMP_DATA


def test_decode_chemistry():
    data = {}
    decode_chemistry(FAKE_CHEMISTRY_RESPONSE, data)

    assert data == EXPECTED_CHEMISTRY_DATA


def test_decode_scg():
    data = {}
    decode_scg_config(FAKE_SCG_RESPONSE, data)

    assert data == EXPECTED_SCG_DATA


def test_takeMessages():
    mID1 = 27
    mCD1 = 12593
    mDT1 = FAKE_CHEMISTRY_RESPONSE
    mID2 = 28
    mCD2 = 12573
    mDT2 = FAKE_SCG_RESPONSE

    joined = makeMessage(mID1, mCD1, mDT1) + makeMessage(mID2, mCD2, mDT2)
    messages = takeMessages(joined)

    assert messages[0][0] == mID1
    assert messages[0][1] == mCD1
    assert messages[0][2] == mDT1

    assert messages[1][0] == mID2
    assert messages[1][1] == mCD2
    assert messages[1][2] == mDT2
