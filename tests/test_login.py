import asyncio
import pytest
from unittest.mock import patch

from screenlogicpy.const.common import (
    ScreenLogicConnectionError,
    ScreenLogicLoginError,
)
from screenlogicpy.const.msg import CODE
from screenlogicpy.gateway import ScreenLogicGateway
from screenlogicpy.requests.login import async_connect_to_gateway, async_get_mac_address
from screenlogicpy.requests.utility import encodeMessageString
from tests.const_data import (
    FAKE_CONNECT_INFO,
    FAKE_GATEWAY_ADDRESS,
    FAKE_GATEWAY_MAC,
    FAKE_GATEWAY_PORT,
)
from tests.fake_gateway import (
    error_resp,
    expected_resp,
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


@pytest.mark.asyncio
async def test_async_login_timeout(
    event_loop: asyncio.AbstractEventLoop, MockProtocolAdapter
):
    async with MockProtocolAdapter:

        def req_fut(result=None):
            nonlocal event_loop
            fut = event_loop.create_future()
            if result:
                fut.set_result(result)
            return fut

        with patch(
            "screenlogicpy.requests.login.ScreenLogicProtocol.await_send_message",
            side_effect=(
                req_fut(
                    expected_resp(
                        CODE.CHALLENGE_QUERY, encodeMessageString(FAKE_GATEWAY_MAC)
                    )
                ),
                req_fut(),
                req_fut(),
            ),
        ) as mockRequest, patch("screenlogicpy.const.msg.COM_RETRY_WAIT", 1):
            gateway = ScreenLogicGateway()
            with pytest.raises(ScreenLogicConnectionError) as e_info:
                await gateway.async_connect(**FAKE_CONNECT_INFO)
            assert "Timeout" in e_info.value.msg
            assert mockRequest.call_count == 3


@pytest.mark.asyncio
async def test_async_login_rejected(
    event_loop: asyncio.AbstractEventLoop, MockProtocolAdapter
):
    async with MockProtocolAdapter:

        def req_fut(result=None):
            nonlocal event_loop
            fut = event_loop.create_future()
            if result:
                fut.set_result(result)
            return fut

        with patch(
            "screenlogicpy.requests.login.ScreenLogicProtocol.await_send_message",
            side_effect=(
                req_fut(
                    expected_resp(
                        CODE.CHALLENGE_QUERY, encodeMessageString(FAKE_GATEWAY_MAC)
                    )
                ),
                req_fut(error_resp(CODE.LOCALLOGIN_QUERY)),
            ),
        ) as mockRequest, patch("screenlogicpy.const.msg.COM_RETRY_WAIT", 1):
            gateway = ScreenLogicGateway()
            with pytest.raises(ScreenLogicLoginError) as e_info:
                await gateway.async_connect(**FAKE_CONNECT_INFO)
            assert "Rejected" in e_info.value.msg
            assert mockRequest.call_count == 2
