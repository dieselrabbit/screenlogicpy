import asyncio
import logging
import struct
from typing import Callable

from ..const.common import ScreenLogicConnectionError
from ..const.msg import CODE, COM_MAX_RETRIES, COM_TIMEOUT
from .protocol import ScreenLogicProtocol
from .request import async_make_request
from .utility import asyncio_timeout, decodeMessageString, encodeMessageString

_LOGGER = logging.getLogger(__name__)


def create_login_message() -> bytes:
    # these constants are only for this message.
    schema = 348
    connectionType = 0
    clientVersion = encodeMessageString("Android")
    pid = 2
    password = "0000000000000000"  # passwd must be <= 16 chars. empty is not OK.
    passwd = encodeMessageString(password)
    fmt = f"<II{len(clientVersion)}s{len(passwd)}sxI"
    return struct.pack(fmt, schema, connectionType, clientVersion, passwd, pid)


async def async_get_mac_address(
    gateway_ip: str, gateway_port: int, max_retries: int = COM_MAX_RETRIES
) -> str:
    """Connect to a screenlogic gateway and return the mac address only."""
    transport, protocol = await async_create_connection(gateway_ip, gateway_port)
    mac = await async_gateway_connect(transport, protocol, max_retries)
    if transport and not transport.is_closing():
        transport.close()
    return mac


async def async_create_connection(
    gateway_ip: str, gateway_port: int, connection_lost_callback: Callable = None
) -> tuple[asyncio.Transport, ScreenLogicProtocol]:
    try:
        loop = asyncio.get_running_loop()

        # on_con_lost = loop.create_future()
        _LOGGER.debug("Creating connection")
        async with asyncio_timeout(COM_TIMEOUT):
            return await loop.create_connection(
                lambda: ScreenLogicProtocol(loop, connection_lost_callback),
                gateway_ip,
                gateway_port,
            )
    except asyncio.TimeoutError as to_ex:
        _LOGGER.debug("Timeout attempting to connect to host")
        raise ScreenLogicConnectionError(
            f"Failed to connect to host at {gateway_ip}:{gateway_port}"
        ) from to_ex
    except OSError as os_ex:
        _LOGGER.debug(f"Error attempting to connect to host: {str(os_ex)}")
        raise ScreenLogicConnectionError(
            f"Failed to connect to host at {gateway_ip}:{gateway_port}"
        ) from os_ex


async def async_gateway_connect(
    transport: asyncio.Transport, protocol: ScreenLogicProtocol, max_retries: int
) -> str:
    connectString = b"CONNECTSERVERHOST\r\n\r\n"  # as bytes, not string
    try:
        # Connect ping
        _LOGGER.debug("Pinging protocol adapter")
        transport.write(connectString)
    except Exception as ex:
        raise ScreenLogicConnectionError("Error sending connect ping") from ex

    await asyncio.sleep(0.25)
    if not protocol.is_connected:
        raise ScreenLogicConnectionError("Host unexpectedly disconnected.")

    _LOGGER.debug("Sending challenge")
    # mac address
    return decodeMessageString(
        await async_make_request(
            protocol, CODE.CHALLENGE_QUERY, max_retries=max_retries
        )
    )


async def async_gateway_login(protocol: ScreenLogicProtocol, max_retries: int) -> bool:
    _LOGGER.debug("Logging in")
    return (
        await async_make_request(
            protocol, CODE.LOCALLOGIN_QUERY, create_login_message(), max_retries
        )
        is not None
    )


async def async_connect_to_gateway(
    gateway_ip,
    gateway_port,
    connection_lost_callback: Callable = None,
    max_retries: int = COM_MAX_RETRIES,
) -> tuple[asyncio.Transport, ScreenLogicProtocol, str]:
    transport, protocol = await async_create_connection(
        gateway_ip, gateway_port, connection_lost_callback
    )
    mac_address = await async_gateway_connect(transport, protocol, max_retries)
    if await async_gateway_login(protocol, max_retries):
        return transport, protocol, mac_address
