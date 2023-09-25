import pytest

from screenlogicpy.requests.gateway import decode_version
from screenlogicpy.requests.config import decode_pool_config
from screenlogicpy.requests.status import decode_pool_status
from screenlogicpy.requests.pump import decode_pump_status
from screenlogicpy.requests.chemistry import decode_chemistry
from screenlogicpy.requests.scg import decode_scg_config

# from screenlogicpy.requests.lights import decode_color_update

from tests.data_sets import ScreenLogicResponseCollection, TEST_DATA_COLLECTIONS


@pytest.mark.parametrize(
    "collection",
    TEST_DATA_COLLECTIONS,
)
def test_validate_complete(collection: ScreenLogicResponseCollection):
    data = {}
    if collection.version:
        decode_version(collection.version.raw, data)
    decode_pool_config(collection.config.raw, data)
    decode_pool_status(collection.status.raw, data)
    for idx, pump in enumerate(collection.pumps):
        decode_pump_status(pump.raw, data, idx)
    if collection.chemistry:
        decode_chemistry(collection.chemistry.raw, data)
    if collection.scg:
        decode_scg_config(collection.scg.raw, data)

def test_tuple_conversion():
    int_tuple: tuple = (1, 2, 3)
    string: str = repr(int_tuple)
    evaled = eval(string)
    assert evaled == int_tuple