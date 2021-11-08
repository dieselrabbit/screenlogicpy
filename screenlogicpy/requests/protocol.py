import asyncio
import itertools
import logging
from typing import Callable

from .utility import makeMessage, takeMessage

_LOGGER = logging.getLogger(__name__)


class ScreenLogicProtocol(asyncio.Protocol):
    """asyncio.Protocol for handling the connection to a ScreenLogic protocol adapter."""

    mID = itertools.cycle(range(65535))  # Maximum value for the messageID data size

    def __init__(self, loop, connection_lost_callback: Callable = None) -> None:
        self.connected = False
        self._connection_lost_callback = connection_lost_callback
        self._futures = self.FutureManager(loop)
        self._callbacks = {}

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
        messageID = next(self.mID)
        fut = self._futures.create(messageID)
        self.send_message(messageID, messageCode, messageData)
        return fut

    def data_received(self, data: bytes) -> None:
        messageID, messageCode, message = takeMessage(data)
        _LOGGER.debug("Received: %i, %i, %s", messageID, messageCode, message)
        if not self._futures.mark_done(messageID, message):
            _LOGGER.debug(
                "Received async message: %i, %i, %s", messageID, messageCode, message
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

    class FutureManager:
        def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
            self._collection = {}
            self.loop = loop

        def create(self, msgID) -> asyncio.Future:
            self._collection[msgID] = self.loop.create_future()
            return self._collection[msgID]

        def try_get(self, msgID):
            if (fut := self._collection.get(msgID)) is not None:
                if not fut.cancelled():
                    return fut
            return None

        def mark_done(self, msgID, result=True):
            if (fut := self.try_get(msgID)) is not None:
                fut.set_result(result)
                return True
            return False
