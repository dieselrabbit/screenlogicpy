"""Discovery for screenlogic gateways."""

import asyncio
import logging
import socket
import struct

from .connection import GatewayInfo
from .exceptions import ScreenLogicError
from .messages import Payload

DISCOVERY_PAYLOAD = struct.pack("<8b", 1, 0, 0, 0, 0, 0, 0, 0)
DISCOVERY_RESPONSE_FORMAT = "<I4BH2B28s"
DISCOVERY_RESPONSE_SIZE = struct.calcsize(DISCOVERY_RESPONSE_FORMAT)
DISCOVERY_ADDRESS = "255.255.255.255"
DISCOVERY_PORT = 1444
DISCOVERY_CHKSUM = 2
DISCOVERY_TIMEOUT = 1

_LOGGER = logging.getLogger(__name__)


def create_broadcast_socket() -> socket.socket:
    """Create a broadcast soscket for discovery."""
    addressfamily = socket.AF_INET
    udp_sock = socket.socket(addressfamily, socket.SOCK_DGRAM)
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udp_sock.bind(("", 0))
    return udp_sock


def process_response(data) -> GatewayInfo:
    """Process a discovery response."""

    pl: Payload = Payload(data)

    chk: int = pl.next_uint32()

    if chk != DISCOVERY_CHKSUM:
        raise ScreenLogicError(
            f"ScreenLogic Discovery: Unexpected response checksum: '{chk}'"
        )

    address: str = ".".join([str(pl.next_uint8()) for _ in range(4)])
    port: int = pl.next_uint16()
    gtype: int = pl.next_uint8()
    gsubtype: int = pl.next_uint8()

    bname = b""
    while (bchr := pl.next("<s")[0]) != b"\x00":
        bname += bchr
    name: str = bname.decode("utf-8")

    return GatewayInfo(
        address,
        port,
        gtype,
        gsubtype,
        name,
    )


class ScreenLogicDiscoveryProtocol:
    """Implement ScreenLogic discovery protocol."""

    hosts: list[GatewayInfo]

    def __init__(self):
        """Init protocol."""
        self.transport = None
        self.hosts = []

    def connection_lost(self, _):
        """Connection lost."""

    def connection_made(self, transport):
        """Connection made."""
        self.transport = transport

    def datagram_received(self, data, _):
        """Response recieved."""
        # try:
        self.hosts.append(process_response(data))
        # except Exception as ex:  # pylint: disable=broad-except
        #    _LOGGER.warning(ex)

    def error_received(self, exc):
        """Error received."""


async def async_discover():
    """Discover screenlogic gateways."""
    loop = asyncio.get_event_loop()
    udp_sock = create_broadcast_socket()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: ScreenLogicDiscoveryProtocol(),  # pylint: disable=unnecessary-lambda
        sock=udp_sock,
    )
    try:
        transport.sendto(DISCOVERY_PAYLOAD, (DISCOVERY_ADDRESS, DISCOVERY_PORT))
        await asyncio.sleep(DISCOVERY_TIMEOUT)
    finally:
        transport.close()
    return protocol.hosts
