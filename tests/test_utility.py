import asyncio
from datetime import datetime
import pytest

from screenlogicpy.requests.utility import decodeMessageTime, encodeMessageTime


def test_encode_decode_time():
    time = datetime(2023, 11, 19, 18, 15, 36, 175759)
    data = encodeMessageTime(time)
    assert data == b"\xe7\x07\x0b\x00\x06\x00\x13\x00\x12\x00\x0f\x00\x00\x00\xaf\x00"
    assert decodeMessageTime(data) == datetime(2023, 11, 19, 18, 15, 0, 175000)
