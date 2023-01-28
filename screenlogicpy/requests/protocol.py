import asyncio
import itertools
import logging
import time
from typing import Awaitable, Callable

from ..const import CODE, ScreenLogicError
from .utility import makeMessage, takeMessages

_LOGGER = logging.getLogger(__name__)


class ScreenLogicProtocol(asyncio.Protocol):
    """asyncio.Protocol for handling the connection to a ScreenLogic protocol adapter."""

    def __init__(self, loop, connection_lost_callback: Callable = None) -> None:
        self.connected = False
        self._loop: asyncio.BaseEventLoop = loop
        self._connection_lost_callback = connection_lost_callback
        self._futures = self.FutureManager(self._loop)
        self._callbacks = {}
        self._last_request: float = None
        self._last_response: float = None
        # Adapter-initiated message IDs seem to start at 32767,
        # so we'll use only the lower half of the message ID data size.
        self.__msgID = itertools.cycle(range(32767))

    @property
    def last_request(self):
        return self._last_request

    @property
    def last_response(self):
        return self._last_response

    def connection_made(self, transport: asyncio.Transport) -> None:
        _LOGGER.debug("Connected to server")
        self.connected = True
        self.transport = transport

    def send_message(self, messageID, messageCode, messageData=b""):
        """Sends the message via the transport."""
        _LOGGER.debug("Sending: %i, %i, %s", messageID, messageCode, messageData)
        self.transport.write(makeMessage(messageID, messageCode, messageData))
        self._last_request = time.monotonic()

    def await_send_message(self, messageCode, messageData=b"") -> asyncio.Future:
        """
        Sends the message and returns an awaitable asyncio.Future object that will contain the
        result of the ScreenLogic protocol adapter's response.
        """
        messageID = next(self.__msgID)
        fut = self._futures.create(messageID)
        self.send_message(messageID, messageCode, messageData)
        return fut

    def data_received(self, data: bytes) -> None:
        for messageID, messageCode, message in takeMessages(data):
            self._last_response = time.monotonic()

            if messageCode == CODE.UNKNOWN_ANSWER:
                raise ScreenLogicError(f"Request explicitly rejected: {messageID}")

            if self._futures.mark_done(messageID, message):
                _LOGGER.debug("Received: %i, %i, %s", messageID, messageCode, message)
            else:
                _LOGGER.debug(
                    "Received async message: %i, %i, %s",
                    messageID,
                    messageCode,
                    message,
                )
                # Unsolicited message received. See if there's a callback registered
                # for the message code and create a task for it.
                if messageCode in self._callbacks:
                    handler, args = self._callbacks[messageCode]
                    _LOGGER.debug(f"Calling {handler}")
                    self._loop.create_task(handler(message, *args))

    def connection_lost(self, exc) -> None:
        _LOGGER.debug("Connection closed")
        self.connected = False
        if self._connection_lost_callback is not None:
            self._connection_lost_callback()

    def register_async_message_callback(
        self,
        messageCode,
        handler: Callable[[bytes, any], Awaitable[any]],
        *args,
    ):
        """Registers an async callback function to call for the specified message code."""
        _LOGGER.debug(
            f"Registering async handler {handler} for message code {messageCode}"
        )
        self._callbacks[messageCode] = (handler, args)

    def remove_async_message_callback(self, messageCode) -> bool:
        """Removes the callback for the specified message code."""
        return True if self._callbacks.pop(messageCode, None) else False

    def remove_all_async_message_callbacks(self):
        """Removes all saved message callbacks."""
        self._callbacks.clear()

    def requests_pending(self) -> bool:
        return not self._futures.all_done()

    class FutureManager:
        def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
            self._collection = {}
            self.loop = loop

        def create(self, msgID) -> asyncio.Future:
            self._collection[msgID] = self.loop.create_future()
            return self._collection[msgID]

        def try_get(self, msgID) -> asyncio.Future:
            fut: asyncio.Future
            if (fut := self._collection.pop(msgID, None)) is not None:
                if not fut.cancelled():
                    return fut
            return None

        def mark_done(self, msgID, result=True) -> bool:
            if (fut := self.try_get(msgID)) is not None:
                try:
                    fut.set_result(result)
                except asyncio.exceptions.InvalidStateError as ise:
                    raise ScreenLogicError(
                        f"Attempted to set result on future {msgID} when result exists: {fut.result()}"
                    ) from ise
                return True
            return False

        def all_done(self) -> bool:
            fut: asyncio.Future
            for fut in self._collection.values():
                if not fut.done():
                    return False
            return True
