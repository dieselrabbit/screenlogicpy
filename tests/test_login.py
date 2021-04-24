import pytest
import threading

from screenlogicpy.requests.login import connect_to_gateway
from tests.fake_gateway import fake_ScreenLogicGateway


@pytest.fixture()
def start_fake_request_gateway():
    fake_gateway = fake_ScreenLogicGateway(requests=True)
    with fake_gateway as _:
        request_thread = threading.Thread(target=fake_gateway.start_request_server)
        request_thread.daemon = True
        request_thread.start()
        yield fake_gateway


def test_gateway_login(start_fake_request_gateway):
    soc, mac = connect_to_gateway("127.0.0.1", "6448")
    assert soc
