"""Defines an asyncio.Protocol for communicating with Pentair ScreenLogic systems."""
import asyncio
import itertools
import logging
import struct
import time
from typing import Awaitable, Callable, Tuple, List

from ..const import ScreenLogicError
from ..const.msg import HEADER_LENGTH
from .utility import makeMessage, takeMessage

_LOGGER = logging.getLogger(__name__)


class ScreenLogicProtocol(asyncio.Protocol):
    """asyncio.Protocol for handling connection to a ScreenLogic protocol adapter."""

    def __init__(self, loop, connection_lost_callback: Callable = None) -> None:
        self._loop: asyncio.BaseEventLoop = loop
        self._connection_lost_callback = connection_lost_callback
        self._futures = self.FutureManager(self._loop)
        self._callbacks = {}
        self._connected = False
        self._closing = False
        self._closed: asyncio.Future = None
        self._last_request: float = None
        self._last_response: float = None
        self._buff = bytearray()

        self._keepalive_awaitable: Callable[[any, any], Awaitable[any]] = None
        self._keepalive_interval: int = None
        self._stop_keepalive: Callable = None

        # Adapter-initiated message IDs seem to start at 32767,
        # so we'll use only the lower half of the message ID data size.
        self.__msgID = itertools.cycle(range(32767))

    @property
    def is_connected(self):
        """Return if protocol is currently connected."""
        return self._connected

    @property
    def is_closing(self):
        return self._closing

    @property
    def last_request(self):
        """Monotonic time for the last message sent."""
        return self._last_request

    @property
    def last_response(self):
        """Monotonic time for last message received."""
        return self._last_response

    def connection_made(self, transport: asyncio.Transport) -> None:
        """Called when connection is made."""
        self._connected = True
        _LOGGER.debug("Connected to server")
        self.transport = transport
        self._closed = self._loop.create_future()

    def send_message(self, messageID, messageCode, messageData=b"") -> None:
        """Send a message via the transport."""
        _LOGGER.debug("Sending: %i, %i, %s", messageID, messageCode, messageData)
        if not self.transport.is_closing():
            self.transport.write(makeMessage(messageID, messageCode, messageData))

        self._last_request = time.monotonic()

        if self._keepalive_awaitable:
            self._set_keepalive()

    def await_send_message(self, messageCode, messageData=b"") -> asyncio.Future:
        """
        Send a message and return an awaitable.

        Sends the message and returns an awaitable asyncio.Future object that will
        contain the result of the ScreenLogic protocol adapter's response.
        """

        messageID = next(self.__msgID)
        fut = self._futures.create(messageID)
        if self._closing:
            fut.cancel()
        else:
            self.send_message(messageID, messageCode, messageData)
        return fut

    def data_received(self, data: bytes) -> None:
        """Called with data is received."""

        if self._closing:
            return

        def complete_messages(data: bytes) -> List[Tuple[int, int, bytes]]:
            """Return only complete ScreenLogic messages."""

            # Some pool configurations can require SL messages larger than can
            # come through in a single call to data_received(), so lets wait until
            # we have at least enough data to make a complete message before we
            # process and pass it on. Conversely, multiple SL messages may come in
            # a single call to data_received() so we collect all complete messages
            # before sending on.

            self._buff.extend(data)
            complete = []
            while len(self._buff) >= HEADER_LENGTH:
                dataLen = struct.unpack_from("<I", self._buff, 4)[0]
                totalLen = HEADER_LENGTH + dataLen
                if len(self._buff) >= totalLen:
                    out = bytearray()
                    for _ in range(totalLen):
                        out.append(self._buff.pop(0))
                    complete.append(takeMessage(bytes(out)))
                else:
                    break
            if len(self._buff) > 0:
                _LOGGER.debug(
                    f"Returning {len(complete)} messages with {len(self._buff)} bytes in the buffer"
                )
                _LOGGER.debug(f"Buffer: {self._buff}")
            return complete

        for message in complete_messages(data):

            if self._futures.mark_done(message):
                _LOGGER.debug("Received: %i, %i, %s", *message)
            else:
                _LOGGER.debug("Received async message: %i, %i, %s", *message)
                # Unsolicited message received. See if there's a callback registered
                # for the message code and create a task for it.
                _, msgCode, msgData = message
                if msgCode in self._callbacks:
                    handler, args = self._callbacks[msgCode]
                    _LOGGER.debug(f"Calling {handler}")
                    self._loop.create_task(handler(msgData, *args))

    def connection_lost(self, exc) -> None:
        """Called when connection is closed/lost."""
        self._connected = False
        _LOGGER.debug("Connection closed")
        self._closed.set_result(True)
        if self._connection_lost_callback is not None:
            self._connection_lost_callback()

    async def async_close(self, force: bool = False) -> None:
        """
        Shutdown the protocol and close the transport.

        Waits for any outstanding requests to be resolved.
        If force == true, immediately cancel all outstanding requests.
        """
        self._closing = True
        try:
            await self._futures.all_done(force)
        except asyncio.CancelledError:
            pass
        if self.transport and not self.transport.is_closing():
            _LOGGER.debug("Closing transport")
            self.transport.close()
        await self._closed

    def register_async_message_callback(
        self,
        messageCode,
        handler: Callable[[bytes, any], Awaitable[any]],
        *args,
    ) -> None:
        """
        Register callback for async ScreenLogic message.

        Registers an async callback function to call for the specified message code.
        Callback will be scheduled to run with loop.create_task()
        """
        _LOGGER.debug(
            f"Registering async handler {handler} for message code {messageCode}"
        )
        self._callbacks[messageCode] = (handler, args)

    def remove_async_message_callback(self, messageCode) -> bool:
        """Remove callback for message code."""
        return True if self._callbacks.pop(messageCode, None) else False

    def remove_all_async_message_callbacks(self) -> None:
        """Remove all message callbacks."""
        self._callbacks.clear()

    def _call_keepalive(self) -> None:
        """Schedule keepalive callback."""
        _LOGGER.debug("Creating keepalive task")
        task = self._loop.create_task(self._keepalive_awaitable())
        _LOGGER.debug(f"keepalive task {task} created")

    def _set_keepalive(self) -> None:
        """Call keepalive scheduler after set delay."""
        if self._stop_keepalive:
            _LOGGER.debug("Killing current keepalive")
            self._stop_keepalive()
            self._stop_keepalive = None

        handle: asyncio.TimerHandle

        _LOGGER.debug("Setting keepalive call_later")
        handle = self._loop.call_later(self._keepalive_interval, self._call_keepalive)

        def _stop():
            """Stop current keepalive timer."""
            if handle:
                _LOGGER.debug(f"Canceling call_later {handle}")
                handle.cancel()

        _LOGGER.debug("Assigning stop_keepalilve callback")
        self._stop_keepalive = _stop

    def enable_keepalive(
        self,
        keepalive_awaitable: Callable[[any, any], Awaitable[any]],
        keepalive_interval: int,
    ) -> None:
        """Enable connection keepalive."""
        _LOGGER.debug("Enabling keepalive")
        self._keepalive_awaitable = keepalive_awaitable
        self._keepalive_interval = keepalive_interval
        self._set_keepalive()

    def disable_keepalive(self) -> None:
        """Disable connection keepalive"""
        _LOGGER.debug("Disabling keepalive")
        self._keepalive_awaitable = None
        if self._stop_keepalive:
            self._stop_keepalive()
            self._stop_keepalive = None

    class FutureManager:
        """Class to manage responses for pending ScreenLogic requests."""

        def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
            self._collection = {}
            self.loop = loop

        def create(self, msgID: int) -> asyncio.Future:
            """Create future for response."""
            self._collection[msgID] = self.loop.create_future()
            return self._collection[msgID]

        def try_get(self, msgID: int) -> asyncio.Future:
            """Get response future for message ID."""
            fut: asyncio.Future
            if (fut := self._collection.pop(msgID, None)) is not None:
                if not fut.cancelled():
                    return fut
            return None

        def mark_done(self, message: Tuple[int, int, bytes]) -> bool:
            """Mark future done and add response."""
            msgID, _, _ = message
            if (fut := self.try_get(msgID)) is not None:
                try:
                    fut.set_result(message)
                except asyncio.exceptions.InvalidStateError as ise:
                    raise ScreenLogicError(
                        f"Attempted to set result on future {msgID} when result exists: {fut.result()}"
                    ) from ise
                return True
            return False

        def all_done(self, force: bool = False) -> asyncio.Future:
            """Return if outstanding still futures exist."""
            outstanding_result: asyncio.Future = asyncio.gather(
                *[fut for fut in self._collection.values()]
            )
            if force:
                outstanding_result.cancel()
            return outstanding_result
