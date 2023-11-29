"""Discovery for screenlogic gateways."""
import asyncio
import logging
import socket
import struct

from .const.common import (  # pylint: disable=relative-beyond-top-level
    SL_GATEWAY_IP,
    SL_GATEWAY_NAME,
    SL_GATEWAY_PORT,
    SL_GATEWAY_SUBTYPE,
    SL_GATEWAY_TYPE,
    ScreenLogicError,
)
from .requests.utility import getSome

DISCOVERY_PAYLOAD = struct.pack("<8b", 1, 0, 0, 0, 0, 0, 0, 0)
DISCOVERY_RESPONSE_FORMAT = "<I4BH2B"
DISCOVERY_RESPONSE_SIZE = struct.calcsize(DISCOVERY_RESPONSE_FORMAT)
DISCOVERY_ADDRESS = "255.255.255.255"
DISCOVERY_PORT = 1444
DISCOVERY_CHKSUM = 2
DISCOVERY_TIMEOUT = 1

_LOGGER = logging.getLogger(__name__)


def create_broadcast_socket():
    """Create a broadcast soscket for discovery."""
    addressfamily = socket.AF_INET
    udp_sock = socket.socket(addressfamily, socket.SOCK_DGRAM)
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udp_sock.bind(("", 0))
    return udp_sock


def process_discovery_response(data):
    """Process a discovery response."""

    chk, offset = getSome("I", data, 0)

    if chk != DISCOVERY_CHKSUM:
        raise ScreenLogicError(
            f"ScreenLogic Discovery: Unexpected response checksum: '{chk}'"
        )

    ip1, offset = getSome("B", data, offset)
    ip2, offset = getSome("B", data, offset)
    ip3, offset = getSome("B", data, offset)
    ip4, offset = getSome("B", data, offset)

    gateway_ip = f"{str(ip1)}.{str(ip2)}.{str(ip3)}.{str(ip4)}"

    gateway_port, offset = getSome("H", data, offset)

    gateway_type, offset = getSome("B", data, offset)

    gateway_subtype, offset = getSome("B", data, offset)

    gateway_name, offset = getSome(f"{len(data) - offset}s", data, offset)

    return {
        SL_GATEWAY_IP: gateway_ip,
        SL_GATEWAY_PORT: gateway_port,
        SL_GATEWAY_TYPE: gateway_type,
        SL_GATEWAY_SUBTYPE: gateway_subtype,
        SL_GATEWAY_NAME: gateway_name.decode("utf-8").strip("\0"),
    }


class ScreenLogicDiscoveryProtocol:
    """Implement ScreenLogic discovery protocol."""

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
        try:
            self.hosts.append(process_discovery_response(data))
        except Exception as ex:  # pylint: disable=broad-except
            _LOGGER.warning(ex)

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
