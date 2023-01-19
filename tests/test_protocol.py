import asyncio
import pytest

from screenlogicpy.requests.protocol import ScreenLogicProtocol
from screenlogicpy.requests.utility import makeMessage


@pytest.mark.asyncio
async def test_async_data_received(event_loop):
    CODE = 1196
    MESSAGE = b"success"

    data = {}

    callback_triggered: asyncio.Future
    callback_triggered = event_loop.create_future()

    async def callback(message, target_data):
        target_data["result"] = message
        callback_triggered.set_result(True)

    protocol = ScreenLogicProtocol(event_loop)
    protocol.register_async_message_callback(CODE, callback, data)

    payload = makeMessage(0, CODE, MESSAGE)
    protocol.data_received(payload)

    await callback_triggered

    assert data.get("result") == MESSAGE


@pytest.mark.asyncio
async def test_async_disconnect(event_loop):
    fut_manager = ScreenLogicProtocol.FutureManager(event_loop)

    futures = []
    for i in range(5):
        futures.append(fut_manager.create(i))

    for x in range(4):
        futures[x].set_result(True)
        assert not fut_manager.all_done()
    futures[4].set_result(True)
    assert fut_manager.all_done()
