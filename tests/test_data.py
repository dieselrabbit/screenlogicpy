from screenlogicpy.data import ScreenLogicResponseCollection
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


def test_tuple_conversion():
    int_tuple: tuple = (1, 2, 3)
    string: str = repr(int_tuple)
    evaled = eval(string)
    assert evaled == int_tuple
