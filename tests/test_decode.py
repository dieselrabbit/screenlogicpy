from dataclasses import astuple
import pytest

from screenlogicpy.data import ScreenLogicResponseCollection
from screenlogicpy.requests.config import decode_pool_config
from screenlogicpy.requests.status import decode_pool_status
from screenlogicpy.requests.pump import decode_pump_status
from screenlogicpy.requests.chemistry import decode_chemistry
from screenlogicpy.requests.scg import decode_scg_config
from screenlogicpy.requests.utility import makeMessage, takeMessages
from screenlogicpy.requests.gateway import decode_version

from .conftest import DEFAULT_RESPONSE, load_response_collection
from .data_sets import TEST_DATA_COLLECTIONS, TESTING_DATA_COLLECTION as TDC


@pytest.mark.parametrize(
    "response_collection", load_response_collection([DEFAULT_RESPONSE])
)
def test_decode_version(response_collection: ScreenLogicResponseCollection):
    data = {}
    decode_version(response_collection.version.raw, data)

    assert data == response_collection.version.decoded


@pytest.mark.parametrize(
    "response_collection", load_response_collection([DEFAULT_RESPONSE])
)
def test_decode_config(response_collection: ScreenLogicResponseCollection):
    data = {}
    decode_pool_config(response_collection.config.raw, data)

    assert data == response_collection.config.decoded


@pytest.mark.parametrize(
    "response_collection", load_response_collection([DEFAULT_RESPONSE])
)
def test_decode_status(response_collection: ScreenLogicResponseCollection):
    data = {}
    decode_pool_status(response_collection.status.raw, data)

    assert data == response_collection.status.decoded


@pytest.mark.parametrize(
    "response_collection", load_response_collection([DEFAULT_RESPONSE])
)
def test_decode_pump(response_collection: ScreenLogicResponseCollection):
    data = {}
    for pump_response in response_collection.pumps:
        decode_pump_status(pump_response.raw, data, 0)

        assert data == pump_response.decoded


@pytest.mark.parametrize(
    "response_collection", load_response_collection([DEFAULT_RESPONSE])
)
def test_decode_chemistry(response_collection: ScreenLogicResponseCollection):
    data = {}
    decode_chemistry(response_collection.chemistry.raw, data)

    assert data == response_collection.chemistry.decoded


@pytest.mark.parametrize(
    "response_collection", load_response_collection([DEFAULT_RESPONSE])
)
def test_decode_scg(response_collection: ScreenLogicResponseCollection):
    data = {}
    decode_scg_config(response_collection.scg.raw, data)

    assert data == response_collection.scg.decoded


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
