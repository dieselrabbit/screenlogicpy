import asyncio
import pytest
from unittest.mock import patch

from screenlogicpy import ScreenLogicGateway
from screenlogicpy.const.common import ScreenLogicConnectionError
from screenlogicpy.const.msg import CODE
from screenlogicpy.requests.request import async_make_request

from .adapter import FakeTCPProtocolAdapter, SLMessage
from .const_data import FAKE_CONNECT_INFO


@pytest.mark.asyncio
async def test_request_connection_lost(
    event_loop: asyncio.AbstractEventLoop, MockProtocolAdapter: asyncio.Server
):
    def disconnecting_ping(self: FakeTCPProtocolAdapter, msg: SLMessage):
        self.transport.abort()

    with patch.object(
        FakeTCPProtocolAdapter, "handle_ping_request", disconnecting_ping
    ):
        async with MockProtocolAdapter:
            gateway = ScreenLogicGateway()
            await gateway.async_connect(**FAKE_CONNECT_INFO)
            assert gateway.is_connected
            with pytest.raises(
                ScreenLogicConnectionError,
                match="Unable to make request. No active connection",
            ):
                await async_make_request(gateway._protocol, CODE.PING_QUERY)
