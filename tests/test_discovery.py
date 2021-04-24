import asyncio
import pytest
import threading

from screenlogicpy.discovery import async_discover, discover
from tests.fake_gateway import fake_ScreenLogicGateway


@pytest.fixture(scope="module")
def start_fake_discovery_gateway():
    fake_gateway = fake_ScreenLogicGateway(discovery=True)
    with fake_gateway as _:
        discovery_thread = threading.Thread(target=fake_gateway.start_discovery_server)
        discovery_thread.daemon = True
        discovery_thread.start()
        yield fake_gateway


def test_gateway_discovery(start_fake_discovery_gateway):

    hosts = discover()

    assert len(hosts) > 0


def test_asyncio_gateway_discovery(start_fake_discovery_gateway):

    hosts = asyncio.run(async_discover())

    assert len(hosts) > 0
