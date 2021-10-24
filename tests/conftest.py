import asyncio
import pytest

from .const_data import (
    FAKE_GATEWAY_ADDRESS,
    FAKE_GATEWAY_PORT,
    FAKE_CONNECT_INFO,
)
from .fake_gateway import FakeScreenLogicTCPProtocol
from screenlogicpy import ScreenLogicGateway


@pytest.fixture()
async def MockProtocolAdapter():
    server = await asyncio.get_event_loop().create_server(
        lambda: FakeScreenLogicTCPProtocol(), FAKE_GATEWAY_ADDRESS, FAKE_GATEWAY_PORT
    )

    async with server:
        await server.start_serving()
        yield server
        server.close()


@pytest.fixture()
async def MockConnectedGateway(
    event_loop: asyncio.AbstractEventLoop, MockProtocolAdapter
):
    async with MockProtocolAdapter:
        gateway = ScreenLogicGateway(**FAKE_CONNECT_INFO)
        await gateway.async_connect()
        assert gateway.is_connected
        await gateway.async_update()
        yield gateway
