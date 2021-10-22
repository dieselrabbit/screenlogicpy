import pytest

from screenlogicpy.requests.login import async_connect_to_gateway
from tests.fake_gateway import (
    FakeScreenLogicTCPProtocol,
    FAKE_GATEWAY_ADDRESS,
    FAKE_GATEWAY_MAC,
    FAKE_GATEWAY_PORT,
)


@pytest.mark.asyncio
async def test_async_gateway_login(event_loop):

    server = await event_loop.create_server(
        lambda: FakeScreenLogicTCPProtocol(), FAKE_GATEWAY_ADDRESS, FAKE_GATEWAY_PORT
    )

    async with server:
        await server.start_serving()
        _, _, mac_address = await async_connect_to_gateway(
            FAKE_GATEWAY_ADDRESS, FAKE_GATEWAY_PORT
        )
        server.close()

    assert mac_address == FAKE_GATEWAY_MAC
