import asyncio
import logging
import struct
from typing import Callable

from ..const import CODE, MESSAGE, ScreenLogicError
from .protocol import ScreenLogicProtocol
from .utility import encodeMessageString, decodeMessageString

_LOGGER = logging.getLogger(__name__)


def create_login_message():
    # these constants are only for this message.
    schema = 348
    connectionType = 0
    clientVersion = encodeMessageString("Android")
    pid = 2
    password = "0000000000000000"  # passwd must be <= 16 chars. empty is not OK.
    passwd = encodeMessageString(password)
    fmt = "<II" + str(len(clientVersion)) + "s" + str(len(passwd)) + "sxI"
    return struct.pack(fmt, schema, connectionType, clientVersion, passwd, pid)


async def async_create_connection(
    gateway_ip, gateway_port, connection_lost_callback: Callable = None
):
    try:
        loop = asyncio.get_running_loop()

        # on_con_lost = loop.create_future()
        _LOGGER.debug("Creating connection")
        transport, protocol = await asyncio.wait_for(
            loop.create_connection(
                lambda: ScreenLogicProtocol(loop, connection_lost_callback),
                gateway_ip,
                gateway_port,
            ),
            MESSAGE.COM_TIMEOUT,
        )
        return transport, protocol
    except asyncio.TimeoutError:
        raise ScreenLogicError(
            f"Failed to connect to host at {gateway_ip}:{gateway_port}"
        )


async def async_gateway_connect(
    transport: asyncio.Transport, protocol: ScreenLogicProtocol
) -> str:
    connectString = b"CONNECTSERVERHOST\r\n\r\n"  # as bytes, not string
    try:
        # Connect ping
        _LOGGER.debug("Pinging protocol adapter")
        transport.write(connectString)
    except Exception as ex:
        raise ScreenLogicError("Error sending connect ping") from ex

    await asyncio.sleep(0.25)

    try:
        _LOGGER.debug("Sending challenge")
        await asyncio.wait_for(
            (request := protocol.await_send_message(CODE.CHALLENGE_QUERY)),
            MESSAGE.COM_TIMEOUT,
        )
        if not request.cancelled():
            # mac address
            return decodeMessageString(request.result())
    except asyncio.TimeoutError:
        raise ScreenLogicError("Host failed to respond to challenge")


async def async_gateway_login(protocol: ScreenLogicProtocol) -> bool:
    try:
        _LOGGER.debug("Logging in")
        await asyncio.wait_for(
            (
                request := protocol.await_send_message(
                    CODE.LOCALLOGIN_QUERY, create_login_message()
                )
            ),
            MESSAGE.COM_TIMEOUT,
        )
        return not request.cancelled()
    except asyncio.TimeoutError:
        raise ScreenLogicError("Failed to logon to gateway")


async def async_connect_to_gateway(
    gateway_ip, gateway_port, connection_lost_callback: Callable = None
):
    transport, protocol = await async_create_connection(
        gateway_ip, gateway_port, connection_lost_callback
    )
    mac_address = await async_gateway_connect(transport, protocol)
    if await async_gateway_login(protocol):
        return transport, protocol, mac_address
