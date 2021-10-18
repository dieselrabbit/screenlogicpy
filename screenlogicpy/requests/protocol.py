import asyncio
from typing import Callable

from .utility import makeMessage, takeMessage


class ScreenLogicProtocol(asyncio.Protocol):
    def __init__(
        self, loop, data={}, connection_lost_callback: Callable = None
    ) -> None:
        self.connected = False
        self._connection_lost_callback = connection_lost_callback
        self._data = data
        self._futures = self.FutureManager(loop)
        self._callbacks = {}

    def connection_made(self, transport: asyncio.Transport) -> None:
        # print("Connected to server.")
        self.connected = True
        self.transport = transport

    def send_data(self, messageCode, data=b"", senderID=0):
        # print(f"Sending: {senderID}, {messageCode}, {data}")
        self.transport.write(makeMessage(messageCode, data, senderID))

    def await_send_data(self, messageCode, data=b"", senderID=0) -> asyncio.Future:
        # print(f"Sending: {senderID}, {messageCode}, {data}")
        self.send_data(messageCode, data, senderID)
        return self._futures.create(messageCode + 1, senderID)

    def data_received(self, data: bytes) -> None:
        messageCode, message, senderID = takeMessage(data)
        # print(f"Received: {senderID}, {messageCode}, {message}")
        if not self._futures.mark_done(messageCode, message, senderID):

            def process_async_message(senderID, messageCode, message):
                print(f"Received async message: {senderID}, {messageCode}, {message}")
                if (callback := self._callbacks.get(messageCode)) is not None:
                    callback(messageCode, senderID, message, self._data)

            process_async_message(senderID, messageCode, message)

    def connection_lost(self, exc) -> None:
        # print("The connection was closed.")
        self.connected = False
        if self._connection_lost_callback is not None:
            self._connection_lost_callback()
        # self.on_connection_lost.set_result(True)

    def register_async_message_callback(
        self, messageCode, callback: Callable[[int, int, bytes, dict], None]
    ):
        self._callbacks[messageCode] = callback

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
