import asyncio

from screenlogicpy.requests.protocol import ScreenLogicProtocol
from screenlogicpy.requests.utility import makeMessage


def test_async_data_received():
    CODE = 1196
    SENDER = 0
    MESSAGE = b""

    data = {}

    def callback(messageCode, senderID, message, target_data):
        target_data["success"] = True

    protocol = ScreenLogicProtocol(asyncio.get_event_loop())
    protocol.register_async_message_callback(CODE, callback, data)

    payload = makeMessage(CODE, MESSAGE, SENDER)
    protocol.data_received(payload)

    assert data.get("success") is True
