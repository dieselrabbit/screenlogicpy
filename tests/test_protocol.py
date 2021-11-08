import pytest

from screenlogicpy.requests.protocol import ScreenLogicProtocol
from screenlogicpy.requests.utility import makeMessage


@pytest.mark.asyncio
async def test_async_data_received(event_loop):
    CODE = 1196
    MESSAGE = b"success"

    data = {}

    def callback(messageCode, message, target_data):
        target_data["result"] = message

    protocol = ScreenLogicProtocol(event_loop)
    protocol.register_async_message_callback(CODE, callback, data)

    payload = makeMessage(0, CODE, MESSAGE)
    protocol.data_received(payload)

    assert data.get("result") == MESSAGE
