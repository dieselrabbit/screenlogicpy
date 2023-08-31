import asyncio
import pytest_asyncio

from .const_data import (
    FAKE_GATEWAY_ADDRESS,
    FAKE_GATEWAY_PORT,
    FAKE_CONNECT_INFO,
)
from .fake_gateway import (
    DisconnectingFakeScreenLogicTCPProtocol,
    FailingFakeScreenLogicTCPProtocol,
    FakeScreenLogicTCPProtocol,
)
from screenlogicpy import ScreenLogicGateway


@pytest_asyncio.fixture()
async def MockProtocolAdapter(event_loop: asyncio.AbstractEventLoop):
    server = await event_loop.create_server(
        lambda: FakeScreenLogicTCPProtocol(),
        FAKE_GATEWAY_ADDRESS,
        FAKE_GATEWAY_PORT,
        reuse_address=True,
    )

    async with server:
        yield server
        print("Closing Server")
        server.close()


@pytest_asyncio.fixture()
async def FailingMockProtocolAdapter(event_loop: asyncio.AbstractEventLoop):
    server = await event_loop.create_server(
        lambda: FailingFakeScreenLogicTCPProtocol(),
        FAKE_GATEWAY_ADDRESS,
        FAKE_GATEWAY_PORT,
    )

    async with server:
        await server.start_serving()
        yield server
        server.close()


@pytest_asyncio.fixture()
async def MockDisconnectingProtocolAdapter(event_loop: asyncio.AbstractEventLoop):
    server = await event_loop.create_server(
        lambda: DisconnectingFakeScreenLogicTCPProtocol(),
        FAKE_GATEWAY_ADDRESS,
        FAKE_GATEWAY_PORT,
        reuse_address=True,
    )

    async with server:
        yield server
        print("Closing Server")
        server.close()


@pytest_asyncio.fixture()
async def MockConnectedGateway(MockProtocolAdapter):
    async with MockProtocolAdapter:
        gateway = ScreenLogicGateway()
        await gateway.async_connect(**FAKE_CONNECT_INFO)
        assert gateway.is_connected
        await gateway.async_update()
        yield gateway
