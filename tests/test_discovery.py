import pytest
import socket
import struct

from screenlogicpy.discovery import async_discover, process_discovery_response
from .const_data import (
    FAKE_CONNECT_INFO,
    FAKE_GATEWAY_ADDRESS,
    FAKE_GATEWAY_CHK,
    FAKE_GATEWAY_DISCOVERY_PORT,
    FAKE_GATEWAY_NAME,
    FAKE_GATEWAY_PORT,
    FAKE_GATEWAY_TYPE,
    FAKE_GATEWAY_SUB_TYPE,
)
from .fake_gateway import FakeScreenLogicUDPProtocol


@pytest.mark.asyncio
async def test_async_discovery(event_loop):

    _udp_sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    _udp_sock.bind(("", FAKE_GATEWAY_DISCOVERY_PORT))

    transport, protocol = await event_loop.create_datagram_endpoint(
        lambda: FakeScreenLogicUDPProtocol(),
        sock=_udp_sock,
    )

    hosts = await async_discover()

    transport.close()

    assert len(hosts) > 0


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
