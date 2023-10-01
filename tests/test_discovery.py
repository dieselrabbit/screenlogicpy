import pytest
import struct
from typing import Any
from unittest.mock import patch

from screenlogicpy import ScreenLogicError
from screenlogicpy.const.common import (
    SL_GATEWAY_IP,
    SL_GATEWAY_NAME,
    SL_GATEWAY_PORT,
    SL_GATEWAY_SUBTYPE,
    SL_GATEWAY_TYPE,
)
from screenlogicpy.discovery import async_discover, process_discovery_response

from .adapter import FakeUDPProtocolAdapter
from .const_data import (
    FAKE_CONNECT_INFO,
    FAKE_GATEWAY_ADDRESS,
    FAKE_GATEWAY_CHK,
    FAKE_GATEWAY_NAME,
    FAKE_GATEWAY_PORT,
    FAKE_GATEWAY_TYPE,
    FAKE_GATEWAY_SUB_TYPE,
)


def test_process_discovery_response():
    ip1, ip2, ip3, ip4 = FAKE_GATEWAY_ADDRESS.split(".")
    response = struct.pack(
        f"<I4BH2B{len(FAKE_GATEWAY_NAME)}s",
        FAKE_GATEWAY_CHK,
        int(ip1),
        int(ip2),
        int(ip3),
        int(ip4),
        FAKE_GATEWAY_PORT,
        FAKE_GATEWAY_TYPE,
        FAKE_GATEWAY_SUB_TYPE,
        bytes(FAKE_GATEWAY_NAME, "UTF-8"),
    )
    data = process_discovery_response(response)
    assert data == FAKE_CONNECT_INFO


def test_discovery_process_discovery_response_error_chk():
    ip1, ip2, ip3, ip4 = FAKE_GATEWAY_ADDRESS.split(".")
    response = struct.pack(
        f"<I4BH2B{len(FAKE_GATEWAY_NAME)}s",
        FAKE_GATEWAY_CHK + 1,
        int(ip1),
        int(ip2),
        int(ip3),
        int(ip4),
        FAKE_GATEWAY_PORT,
        FAKE_GATEWAY_TYPE,
        FAKE_GATEWAY_SUB_TYPE,
        bytes(FAKE_GATEWAY_NAME, "UTF-8"),
    )
    with pytest.raises(ScreenLogicError) as sle:
        _ = process_discovery_response(response)
    assert sle.value.msg == "ScreenLogic Discovery: Unexpected response checksum: '3'"


@pytest.mark.asyncio
async def test_discovery_async_discover(MockDiscoveryAdapter: FakeUDPProtocolAdapter):

    server = MockDiscoveryAdapter
    hosts = await async_discover()

    server.transport.close()

    assert len(hosts) > 0

    host = hosts[0]

    assert host[SL_GATEWAY_IP] == FAKE_GATEWAY_ADDRESS
    assert host[SL_GATEWAY_PORT] == FAKE_GATEWAY_PORT
    assert host[SL_GATEWAY_TYPE] == FAKE_GATEWAY_TYPE
    assert host[SL_GATEWAY_SUBTYPE] == FAKE_GATEWAY_SUB_TYPE
    assert host[SL_GATEWAY_NAME] == FAKE_GATEWAY_NAME


@pytest.mark.asyncio
async def test_discovery_async_discover_error(
    MockDiscoveryAdapter: FakeUDPProtocolAdapter,
    caplog,
):
    response = struct.pack(
        "<I3B",
        FAKE_GATEWAY_CHK,
        int(127),
        int(0),
        int(0),
    )

    def patch_datagram_received(self, data: bytes, addr: tuple[str | Any, int]) -> None:
        if struct.unpack("<8b", data) == (1, 0, 0, 0, 0, 0, 0, 0):
            self.transport.sendto(response, addr)

    with patch.object(
        FakeUDPProtocolAdapter, "datagram_received", patch_datagram_received
    ):
        await async_discover()
        assert "WARNING  screenlogicpy.discovery:discovery.py" in caplog.text
