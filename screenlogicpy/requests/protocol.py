import asyncio
import itertools
import logging
from typing import Callable

from ..const import CODE, ScreenLogicError
from .utility import makeMessage, takeMessages

_LOGGER = logging.getLogger(__name__)


class ScreenLogicProtocol(asyncio.Protocol):
    """asyncio.Protocol for handling the connection to a ScreenLogic protocol adapter."""

    def __init__(self, loop, connection_lost_callback: Callable = None) -> None:
        self.connected = False
        self._connection_lost_callback = connection_lost_callback
        self._futures = self.FutureManager(loop)
        self._callbacks = {}
        # Adapter-initiated message IDs seem to start at 32767,
        # so we'll use only the lower half of the message ID data size.
        self.__msgID = itertools.cycle(range(32767))

    def connection_made(self, transport: asyncio.Transport) -> None:
        _LOGGER.debug("Connected to server")
        self.connected = True
        self.transport = transport

    def send_message(self, messageID, messageCode, messageData=b""):
        """Sends the message via the transport."""
        _LOGGER.debug("Sending: %i, %i, %s", messageID, messageCode, messageData)
        self.transport.write(makeMessage(messageID, messageCode, messageData))

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
                # for the message code and call it.
                if messageCode in self._callbacks:
                    callback, target_data = self._callbacks[messageCode]
                    callback(messageCode, message, target_data)

    def connection_lost(self, exc) -> None:
        _LOGGER.debug("Connection closed")
        self.connected = False
        if self._connection_lost_callback is not None:
            self._connection_lost_callback()

    def register_async_message_callback(
        self,
        messageCode,
        callback: Callable[[int, bytes, dict], None],
        target_data=None,
    ):
        """Registers a callback function to call for the specified unhandled message code."""
        self._callbacks[messageCode] = (callback, target_data)

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
