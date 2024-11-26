import asyncio
import itertools
import logging
import struct
from dataclasses import astuple
from typing import Callable, Generator

from .devices import *
from .messages import *
from .messages.login import CONNECT_PING
from .exceptions import *

__all__ = [
    "Connection",
    "GatewayInfo",
    "ScreenLogicProtocol",
    "Transaction",
    "connect_for_mac",
]

_LOGGER = logging.getLogger(__name__)

# Protocol adapter closes the connection if it doesn't hear
# from the client for 10 minutes, but we'll go ahead an make
# sure it hears something from us well before then.
COM_KEEPALIVE = 30  # 0  # Seconds = 5 minutes
COM_MAX_RETRIES = 1
COM_RETRY_WAIT = 1
COM_TIMEOUT = 2


class ScreenLogicProtocol(asyncio.Protocol):
    """asyncio.Protocol for handling communication with a ScreenLogic gateway (protocol adapter)."""

    _loop: asyncio.BaseEventLoop = None
    _transport: asyncio.Transport = None
    _connected: bool = False
    _message_received_cb: Callable[[BaseResponse], None] | None = None
    _connection_lost_cb: Callable[[bool], None] | None = None
    _buffer: bytearray
    _closed: asyncio.Future
    _closing: bool = False
    _active_requests: dict[int, asyncio.Future]
    _send_all: bool = True

    def __init__(
        self,
        loop,
        message_received_cb: Callable[[BaseResponse], None] = None,
        connection_lost_cb: Callable[[bool], None] = None,
    ) -> None:
        self._loop = loop
        self._message_received_cb = message_received_cb
        self._connection_lost_cb = connection_lost_cb

    @property
    def is_connected(self):
        """Return if protocol is currently connected."""
        return self._connected

    def connection_made(self, transport: asyncio.Transport) -> None:
        """Called when connection is made."""
        self._connected = True
        _LOGGER.debug("Connected to server")
        self._transport = transport
        self._closed = self._loop.create_future()
        self._active_requests = {}
        self._buffer = bytearray()

    def send_data(self, data: bytes) -> bool:
        """Send raw bytes data via the transport and return if successfully written."""
        # _LOGGER.debug("Sending: %i, %i, %s", messageID, messageCode, messageData)
        if self._transport and not self._transport.is_closing():
            self._transport.write(data)
            return True
        return False

    def await_send_message(self, message: BaseRequest) -> asyncio.Future:
        """Send a ScreenLogicMessage via the transport and return an awaitable for the response."""
        fut = self._begin_transaction(message.id)
        _LOGGER.debug(f"SEND #{message.id}, {message.code}, {message.payload.bytes}")
        if not self.send_data(message.to_bytes()):
            fut.cancel("send_data failed")
        return fut

    def data_received(self, data: bytes) -> None:
        """Called with data is received."""

        def complete_messages(
            data: bytes,
        ) -> Generator[BaseResponse, None, None]:
            """Return only complete ScreenLogic messages."""

            # Some pool configurations can require SL messages larger than can
            # come through in a single call to data_received(), so lets wait until
            # we have at least enough data to make a complete message before we
            # process and pass it on. Conversely, multiple SL messages may come in
            # a single call to data_received() so we collect all complete messages
            # before sending on.

            self._buffer.extend(data)
            while len(self._buffer) >= HEADER_LENGTH:
                size = struct.unpack_from("<I", self._buffer, 4)[0]
                needed = HEADER_LENGTH + size
                if len(self._buffer) >= needed:
                    out = bytearray()
                    for _ in range(needed):
                        out.append(self._buffer.pop(0))
                    msg: BaseResponse = from_bytes(bytes(out))
                    _LOGGER.debug(f"PROTOCOL_BUFFER: Yielding message {msg.code}")
                    yield msg
                else:
                    _LOGGER.debug(
                        f"PROTOCOL_BUFFER: {len(self._buffer)} bytes remaining"
                    )
                    break

        for message in complete_messages(data):
            _LOGGER.debug(
                f"RECEIVE: #{message.id}, {message.code}, {message.payload.bytes}"
            )
            if not self._complete_transaction(message) or self._send_all:
                self._message_received_cb(message)

    def connection_lost(self, exc) -> None:
        """Called when connection is closed/lost."""
        self._connected = False
        _LOGGER.debug("Transport closed")
        self._cleanup_all_transactions()
        if exc:
            _LOGGER.debug(exc)
            self._closed.set_exception(exc)
        else:
            self._closed.set_result("ScreenLogicProtocol.connection_lost")
        if self._connection_lost_cb is not None:
            self._connection_lost_cb(self._closing)

    async def close(self) -> None:
        """Shutdown the protocol and close the transport."""
        self._closing = True
        if self._transport and not self._transport.is_closing():
            _LOGGER.debug("Closing transport")
            self._transport.close()
        await self._closed

    def _begin_transaction(self, id: int) -> asyncio.Future:
        if id not in self._active_requests:
            fut = self._loop.create_future()
            fut.add_done_callback(self._cleanup_transaction)
            self._active_requests[id] = fut
            return fut
        raise ValueError(f"Request with id:{id} already exists")

    def _complete_transaction(self, result: BaseResponse) -> bool:
        if fut := self._active_requests.pop(result.id, None):
            fut.remove_done_callback(self._cleanup_transaction)
            fut.set_result(result)
            return True
        return False

    def _cleanup_transaction(
        self, fut: asyncio.Future = None, *, id: int = None
    ) -> None:
        if fut is not None:
            for i, f in self._active_requests.items():
                if f == fut:
                    id = i
                    break
        if id is not None:
            fut = self._active_requests.pop(id)
            if not fut.done():
                fut.cancel()

    def _cleanup_all_transactions(self) -> None:
        all_req_ids = [id for id in self._active_requests.keys()]
        for id in all_req_ids:
            self._cleanup_transaction(id=id)


# *************************************************************************************
# *                                   Transaction                                     *
# *************************************************************************************


class TransactionIDSingleton:
    """Singleton class for Transaction IDs."""

    # Adapter-initiated message IDs seem to start at 32767,
    # so we'll use only the lower half of the message ID data size.
    _iter = itertools.cycle(range(32767))

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(TransactionIDSingleton, cls).__new__(cls)
        return cls.instance

    def next(self) -> int:
        return next(self._iter)


class Transaction:
    """Defines a request/response pair between a ScreenLogicClient and a ScreenLogic Gateway."""

    _id: int
    _request: BaseRequest = None
    _response: BaseResponse = None
    _timeout: int = COM_TIMEOUT
    _retry_delay: int = COM_RETRY_WAIT
    _max_attempts: int = COM_MAX_RETRIES
    _last_error: Exception = None

    def __init__(
        self,
        request: BaseRequest,
        *,
        timout: int = COM_TIMEOUT,
        retry_delay: int = COM_RETRY_WAIT,
        max_attempts: int = COM_MAX_RETRIES,
    ) -> None:
        self._id = TransactionIDSingleton().next()
        self._request = request
        self._request._id = self._id
        self._timeout = timout
        self._retry_delay - retry_delay
        self._max_attempts = max_attempts
        self._attempt = 0

    @property
    def completed(self) -> bool:
        return self._response is not None

    @property
    def id(self) -> int:
        return self._id

    @property
    def request(self) -> BaseRequest:
        return self._request

    @property
    def response(self) -> BaseResponse:
        return self._response

    @property
    def result(self) -> Payload | None:
        return self._response.payload

    async def execute_via(
        self, sender: Callable[[BaseRequest, asyncio.Timeout], asyncio.Future]
    ) -> BaseResponse:
        request = self._request
        while self._attempt <= COM_MAX_RETRIES:
            self._attempt += 1
            try:
                async with asyncio.timeout(self._timeout) as timeout:
                    future_response: asyncio.Future = await sender(request, timeout)
                    await future_response
            except asyncio.TimeoutError:
                self._last_error = ScreenLogicConnectionError(
                    f"Timeout waiting for response to message code '{request.code}'"
                )
            except asyncio.CancelledError:
                self._last_error = ScreenLogicConnectionError(
                    f"Request '{request.code}' canceled"
                )

            if not future_response.cancelled():
                response: BaseResponse = future_response.result()
                if self._is_valid_response(response):
                    self._response = response
                    return self._response

            await asyncio.sleep(self._retry_delay)

        raise self._last_error

    def _is_valid_response(self, response: BaseResponse) -> bool:
        if response.code == self._request.code + 1:
            return True
        elif response.code == MessageCode.LOGIN_REJECTED:
            self._last_error = ScreenLogicLoginError(
                f"Login Rejected for request code: {self._request.code}, request: {self._request.payload.bytes}"
            )
        elif response.code == MessageCode.INVALID_REQUEST:
            self._last_error = ScreenLogicRequestError(
                f"Invalid Request for request code: {self._request.code}, request: {self._request.payload.bytes}"
            )
        elif response.code == MessageCode.BAD_PARAMETER:
            self._last_error = ScreenLogicRequestError(
                f"Bad Parameter for request code: {self._request.code}, request: {self._request.payload.bytes}"
            )
        else:
            self._last_error = ScreenLogicResponseError(
                f"Unexpected response code '{response.code}' for request code: {self._request.code}, request: {self._request.payload.bytes}"
            )
        return False


# *************************************************************************************
# *                                Shared Functions                                   *
# *************************************************************************************


async def connect(
    gw_info: GatewayInfo,
    timeout: int = COM_TIMEOUT,
    async_message_cb: Callable[[BaseResponse], None] = None,
    connection_lost_cb: Callable[[bool], None] = None,
) -> tuple[asyncio.Transport, ScreenLogicProtocol]:
    try:
        loop = asyncio.get_running_loop()
        async with asyncio.timeout(timeout):
            transport, protocol = await loop.create_connection(
                lambda: ScreenLogicProtocol(
                    loop,
                    async_message_cb,
                    connection_lost_cb,
                ),
                gw_info.address,
                gw_info.port,
            )
    except asyncio.TimeoutError as to_ex:
        _LOGGER.debug("Timeout attempting to connect to host")
        raise ScreenLogicConnectionError(
            f"Failed to connect to host at {gw_info.address}:{gw_info.port}"
        ) from to_ex
    except OSError as os_ex:
        _LOGGER.debug(f"Error attempting to connect to host: {str(os_ex)}")
        raise ScreenLogicConnectionError(
            f"Failed to connect to host at {gw_info.address}:{gw_info.port}"
        ) from os_ex
    return (transport, protocol)


async def prime(protocol: ScreenLogicProtocol) -> None:
    try:
        # Connect ping
        _LOGGER.debug("Pinging protocol adapter")
        protocol.send_data(CONNECT_PING)
    except Exception as ex:
        raise ScreenLogicConnectionError("Error priming connection") from ex


async def challenge(
    protocol: ScreenLogicProtocol,
    timeout: int = COM_TIMEOUT,
    retry_delay: int = COM_RETRY_WAIT,
    max_attempts: int = COM_MAX_RETRIES,
) -> str:

    _LOGGER.debug("Sending challenge")

    async def _send(message: BaseRequest, _: asyncio.Timeout) -> asyncio.Future:
        """Send a message to the gateway."""
        return protocol.await_send_message(message)

    # mac address
    challenge_transaction = Transaction(
        ChallengeRequest(),
        timout=timeout,
        retry_delay=retry_delay,
        max_attempts=max_attempts,
    )
    challenge_response: ChallengeResponse = await challenge_transaction.execute_via(
        _send
    )
    return challenge_response.decode()


async def login(
    protocol: ScreenLogicProtocol,
    timeout: int = COM_TIMEOUT,
    retry_delay: int = COM_RETRY_WAIT,
    max_attempts: int = COM_MAX_RETRIES,
):

    async def _send(message: BaseRequest, _: asyncio.Timeout) -> asyncio.Future:
        """Send a message to the gateway."""
        return protocol.await_send_message(message)

    await Transaction(
        LocalLoginRequest(),
        timout=timeout,
        retry_delay=retry_delay,
        max_attempts=max_attempts,
    ).execute_via(_send)


async def get_version(
    protocol: ScreenLogicProtocol,
    timeout: int = COM_TIMEOUT,
    retry_delay: int = COM_RETRY_WAIT,
    max_attempts: int = COM_MAX_RETRIES,
) -> str:

    _LOGGER.debug("Sending challenge")

    async def _send(message: BaseRequest, _: asyncio.Timeout) -> asyncio.Future:
        """Send a message to the gateway."""
        return protocol.await_send_message(message)

    # mac address
    version_transaction = Transaction(
        GatewayVersionRequest(),
        timout=timeout,
        retry_delay=retry_delay,
        max_attempts=max_attempts,
    )
    version_response: GatewayVersionResponse = await version_transaction.execute_via(
        _send
    )
    return version_response.decode()


async def connect_for_mac(
    gw_info: GatewayInfo,
    timeout: int = COM_TIMEOUT,
    retry_delay: int = COM_RETRY_WAIT,
    max_attempts: int = COM_MAX_RETRIES,
) -> str:
    protocol: ScreenLogicProtocol
    _, protocol = connect(
        gw_info,
        timeout,
    )
    await prime(protocol)
    asyncio.sleep(0.25)
    mac = await challenge(
        protocol,
        timeout=timeout,
        retry_delay=retry_delay,
        max_attempts=max_attempts,
    )
    await protocol.close()
    return mac


# *************************************************************************************
# *                                   Connection                                      *
# *************************************************************************************


class Connection:
    """Defines an active connection between a ScreenLogicClient and a ScreenLogic Gateway."""

    _gw_info: GatewayInfo
    _async_message_cb: Callable[[BaseResponse], None] = None
    _connection_lost_cb: Callable[[bool], None] = None
    _timeout: int = COM_TIMEOUT
    _retry_delay: int = COM_RETRY_WAIT
    _max_attempts: int = COM_MAX_RETRIES

    _protocol: ScreenLogicProtocol = None
    _transport: asyncio.Transport = None

    _loop: asyncio.BaseEventLoop = None
    _opening: asyncio.Future = None
    _active: bool = False
    _keep_alive: bool = False
    _keep_alive_delay: int = COM_KEEPALIVE
    _keep_alive_handle: asyncio.TimerHandle = None

    def __init__(
        self,
        *,
        async_message_cb: Callable[[BaseResponse], None] = None,
        connection_lost_cb: Callable[[bool], None] = None,
        timeout: int = None,
        retry_delay: int = None,
        max_attempts: int = None,
        keep_alive: bool = True,
    ) -> None:
        """Create a ScreenLogic Connection instance.

        Keyword Arguments:
            `async_message_cb` - A callback that takes a Response object as the sole parameter.
            `connection_lost_cb` - Callback to be called when the connection was lost and could not be recovered.
            `timeout` - Number in seconds to wait for each Transaction to complete.
            `retry_delay` - Number in seconds to pause between attempts to complete a Transaction.
            `max_attempts` - Number of attempts to make to complete a Transaction.

        async_message_cb(message: Response) is called when a message that is not a \
        response to an active transaction is received from the gateway.
        """
        self._timeout = timeout or self._timeout
        self._retry_delay = retry_delay or self._retry_delay
        self._max_attempts = max_attempts or self._max_attempts
        self._async_message_cb = async_message_cb
        self._connection_lost_cb = connection_lost_cb
        self._loop = asyncio.get_running_loop()
        self._keep_alive = keep_alive

    @property
    def is_active(self) -> bool:
        """Returns if connection is considered active."""
        return self._active

    @property
    def gateway_info(self) -> GatewayInfo:
        """Returns the current GatewayInfo."""
        return self._gw_info

    async def open(
        self,
        gw_info: GatewayInfo,
        *,
        timeout: int = COM_TIMEOUT,
        retry_delay: int = COM_RETRY_WAIT,
        max_attempts: int = COM_MAX_RETRIES,
    ) -> Gateway:
        """Initiate the connection to the ScreenLogic gateway.

        Required:
        - `gw_info` - A GatewayInfo object with the details of the ScreenLogic gateway to connect to.

        Keyword Arguments:
        - `timeout` - Number in seconds to wait for each transaction to complete.
        - `retry_delay` - Number in seconds to pause between attempts to complete a transaction.
        - `max_attempts` - Number of attempts to make to complete a transaction.

        Returns a Gateway object which includes all `gw_info` paramaters and the connected gateway's MAC.
        """

        self._gw_info = gw_info
        self._timeout = timeout or self._timeout
        self._retry_delay = retry_delay or self._retry_delay
        self._max_attempts = max_attempts or self._max_attempts

        try:
            if self._opening:
                await self._opening
                return
            self._opening = self._loop.create_future()

            self._transport, self._protocol = await connect(
                gw_info,
                timeout,
                self._message_received,
                self._connection_lost,
            )

            await prime(self._protocol)
            await asyncio.sleep(0.25)
            if not self._protocol.is_connected:
                raise ScreenLogicConnectionError("Gateway unexpectedly disconnected.")

            gw_mac = await challenge(
                self._protocol,
                timeout,
                retry_delay,
                max_attempts,
            )

            await login(
                self._protocol,
                timeout,
                retry_delay,
                max_attempts,
            )

            gw_firmware = await get_version(
                self._protocol,
                timeout,
                retry_delay,
                max_attempts,
            )

            self._active = True
            if self._keep_alive:
                self._reset_keep_alive()
            self._opening.set_result("Connection.open")
            return Gateway(*astuple(gw_info), gw_mac, gw_firmware)
        except Exception as ex:
            self._opening.set_exception(ex)
            raise ex
        finally:
            self._opening = None

    async def close(self) -> None:
        """Cloase the connection to the ScreenLogic gateway."""
        self._keep_alive = False
        self._reset_keep_alive(None)
        if self._protocol:
            await self._protocol.close()
        self._protocol = None
        self._transport = None

    async def send(self, message: BaseRequest, _: asyncio.Timeout) -> asyncio.Future:
        """Send a message to the gateway."""
        if self._keep_alive:
            self._reset_keep_alive()
        return self._protocol.await_send_message(message)

    async def connected_send(
        self, message: BaseRequest, timeout: asyncio.Timeout
    ) -> asyncio.Future:
        """Send a message to the gateway, ensuring an active connection by attempting to reconnect if needed."""
        if not self._active:
            prev_when = timeout.when()
            timeout.reschedule(None)
            await self.open(self._gw_info)
            timeout.reschedule(prev_when)
        return await self.send(message, timeout)

    def set_msg_received_cb(
        self, callback: Callable[[BaseResponse], None] | None
    ) -> Callable:
        """Specify a callback to be called when an unsolicited message is received."""
        self._async_message_cb = callback

    def set_connection_lost_cb(self, callback: Callable | None) -> Callable:
        """Specify a callback to be called when the connection is closed or lost."""
        self._connection_lost_cb = callback

    def enable_keepalive(self, delay: int = 0) -> None:
        self._keep_alive = True
        if delay:
            self._keep_alive_delay = delay
        self._reset_keep_alive()

    def disable_keepalive(self) -> None:
        self._keep_alive = False
        self._reset_keep_alive(None)

    def _connection_lost(self, user_init) -> None:
        self.disable_keepalive()
        self._active = False
        _LOGGER.debug("Connection closed")
        if self._connection_lost_cb:
            self._connection_lost_cb(user_init)

    def _message_received(self, message: BaseResponse) -> None:
        if self._async_message_cb:
            self._async_message_cb(message)

    def _reset_keep_alive(self, delay: int | None = 0) -> None:
        """Schedules a 'keep-alive' ping request to be made after `delay` seconds.

        If `delay` is explicitly passed as None, any previously scheduled 'keep-alive'
        is canceled and cleared. Default `delay` is 300 seconds (5min).
        """

        def keep_alive_cb() -> None:
            _LOGGER.debug("CONNECTION: Keep alive ping")
            self._loop.create_task(Transaction(PingRequest()).execute_via(self.send))

        _LOGGER.debug("CONNECTION: Keep alive reset")
        if self._keep_alive_handle:
            self._keep_alive_handle.cancel()
        self._keep_alive_handle = (
            self._loop.call_later(
                self._keep_alive_delay if delay == 0 else delay, keep_alive_cb
            )
            if delay is not None
            else None
        )
