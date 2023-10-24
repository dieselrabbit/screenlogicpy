import asyncio
import pytest

from screenlogicpy.const.msg import CODE as MSG_CODE
from screenlogicpy.requests.protocol import ScreenLogicProtocol
from screenlogicpy.requests.utility import makeMessage

from .data_sets import TEST_DATA_COLLECTIONS


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
async def test_async_large_data_received(event_loop):
    CODE = MSG_CODE.CTRLCONFIG_QUERY + 1
    MESSAGE = TEST_DATA_COLLECTIONS[2].config.raw

    data = {}

    callback_triggered: asyncio.Future
    callback_triggered = event_loop.create_future()

    async def callback(message, target_data):
        target_data["result"] = message
        callback_triggered.set_result(True)

    protocol = ScreenLogicProtocol(event_loop)
    protocol.register_async_message_callback(CODE, callback, data)

    payload = makeMessage(0, CODE, MESSAGE)
    protocol.data_received(payload[:1024])
    protocol.data_received(payload[1024:])

    await callback_triggered

    assert data.get("result") == MESSAGE


@pytest.mark.asyncio
async def test_async_close(event_loop: asyncio.AbstractEventLoop):
    test_count = 5
    fut_manager = ScreenLogicProtocol.FutureManager(event_loop)

    futures: list[asyncio.Future] = []
    for i in range(test_count):
        futures.append(fut_manager.create(i))

    def mark_done():
        for x in range(test_count):
            fut = fut_manager.try_get(x)
            fut.set_result(True)

    assert len(fut_manager._collection) == 5
    event_loop.call_later(1.0, mark_done)
    await asyncio.sleep(0)
    await fut_manager.all_done()
    assert len(fut_manager._collection) == 0
    for x in range(test_count):
        assert futures[x].done()
        assert not futures[x].cancelled()

    fut_manager = ScreenLogicProtocol.FutureManager(event_loop)

    futures = []
    for i in range(5):
        futures.append(fut_manager.create(i))

    assert len(fut_manager._collection) == 5

    await fut_manager.all_done(True)
    await asyncio.sleep(0)

    assert len(fut_manager._collection) == 0

    for x in range(test_count):
        assert futures[x].cancelled()
