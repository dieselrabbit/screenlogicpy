import asyncio
import time
from screenlogicpy.discovery import async_discover, discover
from tests.fake_gateway import fake_ScreenLogicGateway


def test_gateway_discovery():
    _ = fake_ScreenLogicGateway(request=False)

    time.sleep(2)

    hosts = discover()

    assert len(hosts) > 0


def test_asyncio_gateway_discovery():
    _ = fake_ScreenLogicGateway(request=False)

    time.sleep(2)

    hosts = asyncio.run(async_discover())

    assert len(hosts) > 0
