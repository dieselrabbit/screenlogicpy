import asyncio
import pytest
from unittest.mock import patch

from screenlogicpy.const.common import (
    ScreenLogicConnectionError,
    ScreenLogicLoginError,
)
from screenlogicpy.const.msg import CODE
from screenlogicpy.requests.login import (
    async_connect_to_gateway,
    async_create_connection,
    async_gateway_connect,
    async_gateway_login,
    async_get_mac_address,
    create_login_message,
)
from .adapter import FakeTCPProtocolAdapter, SLMessage
from .const_data import (
    FAKE_GATEWAY_ADDRESS,
    FAKE_GATEWAY_MAC,
    FAKE_GATEWAY_PORT,
)


def test_login_create_login_message():
    assert (
        create_login_message()
        == b"\\\x01\x00\x00\x00\x00\x00\x00\x07\x00\x00\x00Android\x00\x10\x00\x00\x000000000000000000\x00\x02\x00\x00\x00"
    )


@pytest.mark.asyncio
async def test_login_async_connect_to_gateway(MockProtocolAdapter):
    async with MockProtocolAdapter:
        transport, protocol, mac_address = await async_connect_to_gateway(
            FAKE_GATEWAY_ADDRESS, FAKE_GATEWAY_PORT
        )
        assert transport
        assert protocol.is_connected

    assert mac_address == FAKE_GATEWAY_MAC


@pytest.mark.asyncio
async def test_login_async_get_mac_address(MockProtocolAdapter):
    async with MockProtocolAdapter:
        mac_address = await async_get_mac_address(
            FAKE_GATEWAY_ADDRESS, FAKE_GATEWAY_PORT
        )

    assert mac_address == FAKE_GATEWAY_MAC


@pytest.mark.asyncio
async def test_login_async_create_connection_error(MockProtocolAdapter):
    async with MockProtocolAdapter:
        with pytest.raises(ScreenLogicConnectionError):
            _, _ = await async_create_connection(
                FAKE_GATEWAY_ADDRESS, FAKE_GATEWAY_PORT + 1
            )


@pytest.mark.asyncio
async def test_login_async_gateway_connect(MockProtocolAdapter):
    async with MockProtocolAdapter:
        transport, protocol = await async_create_connection(
            FAKE_GATEWAY_ADDRESS, FAKE_GATEWAY_PORT
        )
        await async_gateway_connect(transport, protocol, 0)


@pytest.mark.asyncio
async def test_login_async_gateway_connect_error1(MockProtocolAdapter):
    async with MockProtocolAdapter:
        transport, protocol = await async_create_connection(
            FAKE_GATEWAY_ADDRESS, FAKE_GATEWAY_PORT
        )
        transport.close()
        await asyncio.sleep(1)
        with pytest.raises(ScreenLogicConnectionError) as sle:
            await async_gateway_connect(transport, protocol, 0)
        assert sle.value.msg == "Host unexpectedly disconnected."


@pytest.mark.asyncio
async def test_login_async_gateway_connect_error2(MockProtocolAdapter):
    async with MockProtocolAdapter:
        transport, protocol = await async_create_connection(
            FAKE_GATEWAY_ADDRESS, FAKE_GATEWAY_PORT
        )

        def patch_process_message(self: FakeTCPProtocolAdapter, msg: SLMessage):
            self.transport.close()

        with patch.object(
            FakeTCPProtocolAdapter, "process_message", patch_process_message
        ), pytest.raises(ScreenLogicConnectionError) as sre:
            await async_gateway_connect(transport, protocol, 0)
        assert sre.value.msg == "Timeout waiting for response to message code '14'"


@pytest.mark.asyncio
async def test_login_async_gateway_login_error(MockProtocolAdapter):
    async with MockProtocolAdapter:
        transport, protocol = await async_create_connection(
            FAKE_GATEWAY_ADDRESS, FAKE_GATEWAY_PORT
        )
        _ = await async_gateway_connect(transport, protocol, 0)
        transport.close()

        with pytest.raises(ScreenLogicConnectionError) as sle:
            await async_gateway_login(protocol, 0)
        assert sle.value.msg == "Timeout waiting for response to message code '27'"


@pytest.mark.asyncio
async def test_async_login_rejected(MockProtocolAdapter):
    async with MockProtocolAdapter:

        def patch_handle_login_request(self, msg: SLMessage) -> SLMessage:
            return SLMessage(msg.id, CODE.ERROR_LOGIN_REJECTED)

        with patch.object(
            FakeTCPProtocolAdapter, "handle_logon_request", patch_handle_login_request
        ), pytest.raises(ScreenLogicLoginError) as sle:
            await async_connect_to_gateway(
                FAKE_GATEWAY_ADDRESS, FAKE_GATEWAY_PORT, max_retries=0
            )
        assert (
            sle.value.msg
            == "Login Rejected for request code: 27, request: b'\\\\\\x01\\x00\\x00\\x00\\x00\\x00\\x00\\x07\\x00\\x00\\x00Android\\x00\\x10\\x00\\x00\\x000000000000000000\\x00\\x02\\x00\\x00\\x00'"
        )
