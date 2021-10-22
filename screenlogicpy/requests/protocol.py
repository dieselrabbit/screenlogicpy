import asyncio
import logging
from typing import Callable

from .utility import makeMessage, takeMessage

_LOGGER = logging.getLogger(__name__)


class ScreenLogicProtocol(asyncio.Protocol):
    def __init__(self, loop, connection_lost_callback: Callable = None) -> None:
        self.connected = False
        self._connection_lost_callback = connection_lost_callback
        self._futures = self.FutureManager(loop)
        self._callbacks = {}

    def connection_made(self, transport: asyncio.Transport) -> None:
        _LOGGER.debug("Connected to server")
        self.connected = True
        self.transport = transport

    def send_data(self, messageCode, data=b"", senderID=0):
        _LOGGER.debug("Sending: %i, %i, %s", senderID, messageCode, data)
        self.transport.write(makeMessage(messageCode, data, senderID))

    def await_send_data(self, messageCode, data=b"", senderID=0) -> asyncio.Future:
        self.send_data(messageCode, data, senderID)
        return self._futures.create(messageCode + 1, senderID)

    def data_received(self, data: bytes) -> None:
        messageCode, message, senderID = takeMessage(data)
        _LOGGER.debug("Received: %i, %i, %s", senderID, messageCode, message)
        if not self._futures.mark_done(messageCode, message, senderID):
            _LOGGER.debug(
                "Received async message: %i, %i, %s", senderID, messageCode, message
            )
            if messageCode in self._callbacks:
                callback, target_data = self._callbacks[messageCode]
                callback(messageCode, senderID, message, target_data)

    def connection_lost(self, exc) -> None:
        _LOGGER.debug("Connection closed")
        self.connected = False
        if self._connection_lost_callback is not None:
            self._connection_lost_callback()

    def register_async_message_callback(
        self,
        messageCode,
        callback: Callable[[int, int, bytes, dict], None],
        target_data=None,
    ):
        self._callbacks[messageCode] = (callback, target_data)

    class FutureManager:
        def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
            self._collection = {}
            self.loop = loop

        def create(self, msgCode, senderID=0) -> asyncio.Future:
            if msgCode not in self._collection:
                self._collection[msgCode] = {}

            self._collection[msgCode][senderID] = self.loop.create_future()
            return self._collection[msgCode][senderID]

        def try_get(self, msgCode, senderID=0):
            if (msg := self._collection.get(msgCode)) is None:
                return None
            return msg.get(senderID)

        def mark_done(self, msgCode, result=True, senderID=0):
            if (fut := self.try_get(msgCode, senderID)) is not None:
                if not fut.cancelled():
                    fut.set_result(result)
                    return True
            return False
