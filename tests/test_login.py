import pytest

from screenlogicpy.requests.login import async_connect_to_gateway, async_get_mac_address
from tests.fake_gateway import (
    FAKE_GATEWAY_ADDRESS,
    FAKE_GATEWAY_MAC,
    FAKE_GATEWAY_PORT,
)


@pytest.mark.asyncio
async def test_async_gateway_login(MockProtocolAdapter):
    async with MockProtocolAdapter:
        _, _, mac_address = await async_connect_to_gateway(
            FAKE_GATEWAY_ADDRESS, FAKE_GATEWAY_PORT
        )

    assert mac_address == FAKE_GATEWAY_MAC


@pytest.mark.asyncio
async def test_async_get_mac_address(MockProtocolAdapter):
    async with MockProtocolAdapter:
        mac_address = await async_get_mac_address(
            FAKE_GATEWAY_ADDRESS, FAKE_GATEWAY_PORT
        )

    assert mac_address == FAKE_GATEWAY_MAC
