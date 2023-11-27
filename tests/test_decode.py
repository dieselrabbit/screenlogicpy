import pytest

from screenlogicpy.data import ScreenLogicResponseCollection
from screenlogicpy.requests.config import decode_pool_config
from screenlogicpy.requests.status import decode_pool_status
from screenlogicpy.requests.pump import decode_pump_status
from screenlogicpy.requests.chemistry import decode_chemistry
from screenlogicpy.requests.scg import decode_scg_config
from screenlogicpy.requests.utility import makeMessage, takeMessages
from screenlogicpy.requests.gateway import decode_version

from tests.conftest import load_response_collections


def get_rc_id(rc_tup: tuple[str, ScreenLogicResponseCollection]):
    return rc_tup[0]


@pytest.fixture(params=load_response_collections(), ids=get_rc_id)
def response_collection(request):
    return request.param[1]


class TestDecode:
    def test_decode_version(self, response_collection: ScreenLogicResponseCollection):
        data = {}
        decode_version(response_collection.version.raw, data)

        assert data == response_collection.version.decoded

    def test_decode_config(self, response_collection: ScreenLogicResponseCollection):
        data = {}
        decode_pool_config(response_collection.config.raw, data)

        assert data == response_collection.config.decoded

    def test_decode_status(self, response_collection: ScreenLogicResponseCollection):
        data = {}
        decode_pool_status(response_collection.status.raw, data)

        assert data == response_collection.status.decoded

    def test_decode_pump(self, response_collection: ScreenLogicResponseCollection):
        for pump_num, pump_response in enumerate(response_collection.pumps):
            data = {}
            decode_pump_status(pump_response.raw, data, pump_num)

            assert data == pump_response.decoded

    def test_decode_chemistry(self, response_collection: ScreenLogicResponseCollection):
        data = {}
        decode_chemistry(response_collection.chemistry.raw, data)

        assert data == response_collection.chemistry.decoded

    def test_decode_scg(self, response_collection: ScreenLogicResponseCollection):
        data = {}
        decode_scg_config(response_collection.scg.raw, data)

        assert data == response_collection.scg.decoded

    def test_takeMessages(self, response_collection: ScreenLogicResponseCollection):
        mID1 = 27
        mCD1 = 12593
        mDT1 = response_collection.chemistry.raw
        mID2 = 28
        mCD2 = 12573
        mDT2 = response_collection.scg.raw

        joined = makeMessage(mID1, mCD1, mDT1) + makeMessage(mID2, mCD2, mDT2)
        messages = takeMessages(joined)

        assert messages[0][0] == mID1
        assert messages[0][1] == mCD1
        assert messages[0][2] == mDT1

        assert messages[1][0] == mID2
        assert messages[1][1] == mCD2
        assert messages[1][2] == mDT2
