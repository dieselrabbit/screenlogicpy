import asyncio
import pytest
import socket
import struct
from unittest.mock import MagicMock, NonCallableMagicMock, patch

from screenlogicpy.discovery import (
    DISCOVERY_PAYLOAD,
    DISCOVERY_ADDRESS,
    DISCOVERY_PORT,
    ScreenLogicDiscoveryProtocol,
    async_discover,
    create_broadcast_socket,
    process_response,
)
from screenlogicpy.connection import GatewayInfo

GW_ADDR_TPL = (111, 222, 33, 4)
GW_ADDR_STR = ".".join([str(i) for i in GW_ADDR_TPL])
GW_PORT = 80
GW_TYPE = 2
GW_SUBTYPE = 12
GW_NAME_B = b"Pentair: AA-BB-CC"
GW_NAME_STR = GW_NAME_B.decode("utf-8")
GW_DATA = b"\x02\x00\x00\x00o\xde!\x04P\x00\x02\x0cPentair: AA-BB-CC\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"


def test_create_socket():
    with patch("socket.socket", spec=True) as sockpatch:
        mocksock: NonCallableMagicMock = create_broadcast_socket()
        sockpatch.assert_called_with(socket.AF_INET, socket.SOCK_DGRAM)
        assert mocksock
        mocksock.setsockopt.assert_called_with(
            socket.SOL_SOCKET, socket.SO_BROADCAST, 1
        )
        mocksock.bind.assert_called_with(("", 0))


def test_process_response():
    data = struct.pack(
        "<I4BH2B28s", 2, *GW_ADDR_TPL, GW_PORT, GW_TYPE, GW_SUBTYPE, GW_NAME_B
    )
    assert data == GW_DATA
    gwinfo = process_response(data)
    assert gwinfo.address == GW_ADDR_STR
    assert gwinfo.port == GW_PORT
    assert gwinfo.type == GW_TYPE
    assert gwinfo.subtype == GW_SUBTYPE
    assert gwinfo.name == GW_NAME_STR
    assert gwinfo.mac == None


@pytest.mark.asyncio
async def test_async_discover():
    TEST_GATEWAYINFO = GatewayInfo(
        GW_ADDR_STR, GW_PORT, GW_TYPE, GW_SUBTYPE, GW_NAME_STR
    )
    MOCK_TRANSPORT = NonCallableMagicMock(spec=asyncio.DatagramTransport)
    MOCK_PROTOCOL = NonCallableMagicMock(
        spec=ScreenLogicDiscoveryProtocol, hosts=[TEST_GATEWAYINFO]
    )
    with patch(
        "asyncio.get_event_loop", return_value=MagicMock(spec=asyncio.BaseEventLoop)
    ) as loop_mock, patch(
        "screenlogicpy.discovery.create_broadcast_socket",
        return_value=MagicMock(spec=socket.socket),
    ), patch(
        "screenlogicpy.discovery.DISCOVERY_TIMEOUT", 0.1
    ):
        loop_inst = loop_mock.return_value
        loop_inst.create_datagram_endpoint.return_value = (
            MOCK_TRANSPORT,
            MOCK_PROTOCOL,
        )
        hosts = await async_discover()
        assert hosts
        assert hosts[0] == TEST_GATEWAYINFO
        MOCK_TRANSPORT.sendto.assert_called_with(
            DISCOVERY_PAYLOAD, (DISCOVERY_ADDRESS, DISCOVERY_PORT)
        )
