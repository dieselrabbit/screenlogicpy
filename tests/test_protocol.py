import asyncio
import pytest

from .const_data import FAKE_CONFIG_RESPONSE_LARGE
from screenlogicpy.const import CODE as MSG_CODE, MESSAGE as CONST_MESSAGE
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
async def test_async_large_data_received(event_loop):
    CODE = MSG_CODE.CTRLCONFIG_QUERY + 1
    MESSAGE = FAKE_CONFIG_RESPONSE_LARGE[CONST_MESSAGE.HEADER_LENGTH :]

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
async def test_async_close(event_loop):
    test_count = 5
    fut_manager = ScreenLogicProtocol.FutureManager(event_loop)

    futures = []
    for i in range(test_count):
        futures.append(fut_manager.create(i))

    outstanding_result = fut_manager.all_done()
    for x in range(4):
        futures[x].set_result(True)
        assert not outstanding_result.done()
    futures[4].set_result(True)
    await asyncio.sleep(0)
    assert outstanding_result.done()
    assert outstanding_result.result() == [True for _ in range(test_count)]

    fut_manager = ScreenLogicProtocol.FutureManager(event_loop)

    futures = []
    for i in range(5):
        futures.append(fut_manager.create(i))

    outstanding_result = fut_manager.all_done(True)
    await asyncio.sleep(0)
    assert outstanding_result.done()
    assert isinstance(outstanding_result.exception(), asyncio.CancelledError)
