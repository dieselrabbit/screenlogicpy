import pytest
import struct

from screenlogicpy.discovery import async_discover, process_discovery_response
from screenlogicpy.const.common import (
    SL_GATEWAY_IP,
    SL_GATEWAY_NAME,
    SL_GATEWAY_PORT,
    SL_GATEWAY_SUBTYPE,
    SL_GATEWAY_TYPE,
)
from .const_data import (
    FAKE_CONNECT_INFO,
    FAKE_GATEWAY_ADDRESS,
    FAKE_GATEWAY_CHK,
    FAKE_GATEWAY_NAME,
    FAKE_GATEWAY_PORT,
    FAKE_GATEWAY_TYPE,
    FAKE_GATEWAY_SUB_TYPE,
)
from .adapter import FakeUDPProtocolAdapter


@pytest.mark.asyncio
async def test_async_discovery(FakeDiscoveryAdapter: FakeUDPProtocolAdapter):

    server = FakeDiscoveryAdapter
    hosts = await async_discover()

    server.transport.close()

    assert len(hosts) > 0

    host = hosts[0]

    assert host[SL_GATEWAY_IP] == FAKE_GATEWAY_ADDRESS
    assert host[SL_GATEWAY_PORT] == FAKE_GATEWAY_PORT
    assert host[SL_GATEWAY_TYPE] == FAKE_GATEWAY_TYPE
    assert host[SL_GATEWAY_SUBTYPE] == FAKE_GATEWAY_SUB_TYPE
    assert host[SL_GATEWAY_NAME] == FAKE_GATEWAY_NAME


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
