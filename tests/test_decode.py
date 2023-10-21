from dataclasses import astuple
import pytest

from screenlogicpy.requests.config import decode_pool_config
from screenlogicpy.requests.status import decode_pool_status
from screenlogicpy.requests.pump import decode_pump_status
from screenlogicpy.requests.chemistry import decode_chemistry
from screenlogicpy.requests.scg import decode_scg_config
from screenlogicpy.requests.utility import makeMessage, takeMessages
from screenlogicpy.requests.gateway import decode_version

from .data_sets import TEST_DATA_COLLECTIONS, TESTING_DATA_COLLECTION as TDC


@pytest.mark.parametrize(
    "buffer, expected",
    [astuple(col.version) for col in TEST_DATA_COLLECTIONS if col.version],
)
def test_decode_version(buffer, expected):
    data = {}
    decode_version(buffer, data)

    assert data == expected


@pytest.mark.parametrize(
    "buffer, expected",
    [astuple(col.config) for col in TEST_DATA_COLLECTIONS if col.config],
)
def test_decode_config(buffer, expected):
    data = {}
    decode_pool_config(buffer, data)

    assert data == expected

    decode_pool_config(buffer, data)

    assert data == expected


@pytest.mark.parametrize(
    "buffer, expected",
    [astuple(col.status) for col in TEST_DATA_COLLECTIONS if col.status],
)
def test_decode_status(buffer, expected):
    data = {}
    decode_pool_status(buffer, data)

    assert data == expected


@pytest.mark.parametrize(
    "buffer, expected",
    [astuple(pump) for col in TEST_DATA_COLLECTIONS for pump in col.pumps if col.pumps],
)
def test_decode_pump(buffer, expected):
    data = {}
    decode_pump_status(buffer, data, 0)

    assert data == expected


@pytest.mark.parametrize(
    "buffer, expected",
    [astuple(col.chemistry) for col in TEST_DATA_COLLECTIONS if col.chemistry],
)
def test_decode_chemistry(buffer, expected):
    data = {}
    decode_chemistry(buffer, data)

    assert data == expected


@pytest.mark.parametrize(
    "buffer, expected",
    [astuple(col.scg) for col in TEST_DATA_COLLECTIONS if col.scg],
)
def test_decode_scg(buffer, expected):
    data = {}
    decode_scg_config(buffer, data)

    assert data == expected


def test_takeMessages():
    mID1 = 27
    mCD1 = 12593
    mDT1 = TDC.chemistry.raw
    mID2 = 28
    mCD2 = 12573
    mDT2 = TDC.scg.raw

    joined = makeMessage(mID1, mCD1, mDT1) + makeMessage(mID2, mCD2, mDT2)
    messages = takeMessages(joined)

    assert messages[0][0] == mID1
    assert messages[0][1] == mCD1
    assert messages[0][2] == mDT1

    assert messages[1][0] == mID2
    assert messages[1][1] == mCD2
    assert messages[1][2] == mDT2
