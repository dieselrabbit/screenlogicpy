import asyncio
import struct
import pytest
from unittest.mock import patch

from screenlogicpy import ScreenLogicGateway
from screenlogicpy.client import ClientManager
from screenlogicpy.const import CLIENT_ID, CODE
from .const_data import (
    EXPECTED_STATUS_DATA,
    EXPECTED_CHEMISTRY_DATA,
    FAKE_CONNECT_INFO,
    FAKE_CHEMISTRY_RESPONSE,
    FAKE_STATUS_RESPONSE,
)


@pytest.mark.asyncio()
async def test_sub_unsub(event_loop, MockProtocolAdapter):
    async with MockProtocolAdapter:
        gateway = ScreenLogicGateway()
        code = CODE.STATUS_CHANGED
        clientID = CLIENT_ID

        def callback():
            pass

        bad_unsub = await gateway.clients.async_subscribe(callback, code)

        assert not bad_unsub

        await gateway.async_connect(**FAKE_CONNECT_INFO)

        result = event_loop.create_future()
        result.set_result(b"")
        with patch(
            "screenlogicpy.requests.client.ScreenLogicProtocol.await_send_message",
            return_value=result,
        ) as mockSubRequest:
            unsub = await gateway.clients.async_subscribe(callback, code)

            assert callable(unsub)
            assert gateway.clients._listeners == {
                code: {
                    callback,
                },
            }
            assert gateway._protocol._callbacks == {
                code: (gateway.clients._async_common_callback, (code, gateway._data)),
            }
            assert mockSubRequest.call_args.args[0] == 12522
            assert mockSubRequest.call_args.args[1] == struct.pack("<II", 0, clientID)

        with patch(
            "screenlogicpy.requests.client.ScreenLogicProtocol.await_send_message",
            return_value=result,
        ) as mockUnsubRequest:
            unsub()

            assert gateway.clients._listeners == {}
            assert gateway._protocol._callbacks == {}

            await asyncio.sleep(0)

            assert mockUnsubRequest.call_args.args[0] == 12524
            assert mockUnsubRequest.call_args.args[1] == struct.pack("<II", 0, clientID)


@pytest.mark.asyncio()
async def test_notify():
    code1 = CODE.STATUS_CHANGED
    code2 = CODE.CHEMISTRY_CHANGED

    cb1_hit = False
    cb2_hit = False
    cb3_hit = False

    def callback1():
        nonlocal cb1_hit
        cb1_hit = True

    def callback2():
        nonlocal cb2_hit
        cb2_hit = True

    def callback3():
        nonlocal cb3_hit
        cb3_hit = True

    cm = ClientManager()
    cm._listeners = {
        code1: {
            callback1,
            callback2,
        },
        code2: {
            callback3,
        },
    }

    status_data = {}
    await cm._async_common_callback(
        FAKE_STATUS_RESPONSE, CODE.STATUS_CHANGED, status_data
    )

    assert cb1_hit
    assert cb2_hit
    assert not cb3_hit

    chem_data = {}
    await cm._async_common_callback(
        FAKE_CHEMISTRY_RESPONSE, CODE.CHEMISTRY_CHANGED, chem_data
    )

    assert cb3_hit

    assert status_data == EXPECTED_STATUS_DATA
    assert chem_data == EXPECTED_CHEMISTRY_DATA


@pytest.mark.asyncio()
async def test_attach_existing(MockProtocolAdapter):
    gateway = ScreenLogicGateway()
    code1 = CODE.STATUS_CHANGED
    code2 = CODE.CHEMISTRY_CHANGED

    cb1_hit = False
    cb2_hit = False
    cb3_hit = False

    def callback1():
        nonlocal cb1_hit
        cb1_hit = True

    def callback2():
        nonlocal cb2_hit
        cb2_hit = True

    def callback3():
        nonlocal cb3_hit
        cb3_hit = True

    gateway.clients._listeners = {
        code1: {
            callback1,
            callback2,
        },
        code2: {
            callback3,
        },
    }
    async with MockProtocolAdapter:

        await gateway.async_connect(**FAKE_CONNECT_INFO)

        assert gateway._protocol._callbacks == {
            code1: (gateway.clients._async_common_callback, (code1, gateway._data)),
            code2: (gateway.clients._async_common_callback, (code2, gateway._data)),
        }
