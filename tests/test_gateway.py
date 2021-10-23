import asyncio
import pytest
import struct
from unittest.mock import patch

# from deepdiff import DeepDiff


from .const_data import (
    EXPECTED_COMPLETE_DATA,
    FAKE_GATEWAY_ADDRESS,
    FAKE_GATEWAY_MAC,
    FAKE_GATEWAY_NAME,
    FAKE_GATEWAY_PORT,
    FAKE_GATEWAY_VERSION,
)


@pytest.mark.asyncio
async def test_gateway(event_loop: asyncio.AbstractEventLoop, MockConnectedGateway):
    gateway = MockConnectedGateway
    assert gateway.ip == FAKE_GATEWAY_ADDRESS
    assert gateway.port == FAKE_GATEWAY_PORT
    assert gateway.name == FAKE_GATEWAY_NAME
    assert gateway.version == FAKE_GATEWAY_VERSION
    assert gateway.mac == FAKE_GATEWAY_MAC
    data = gateway.get_data()
    await gateway.async_disconnect()
    assert data

    # diff = DeepDiff(data, EXPECTED_COMPLETE_DATA)
    # print(diff)
    assert data == EXPECTED_COMPLETE_DATA


@pytest.mark.asyncio
async def test_async_set_circuit(
    event_loop: asyncio.AbstractEventLoop, MockConnectedGateway
):
    circuit_id = 505
    circuit_state = 1
    result = event_loop.create_future()
    result.set_result(b"")
    with patch(
        "screenlogicpy.requests.button.ScreenLogicProtocol.await_send_data",
        return_value=result,
    ) as mockRequest:
        gateway = MockConnectedGateway
        assert await gateway.async_set_circuit(circuit_id, circuit_state)
        await gateway.async_disconnect()
        assert mockRequest.call_args.args[0] == 12530
        assert mockRequest.call_args.args[1] == struct.pack(
            "<III", 0, circuit_id, circuit_state
        )


@pytest.mark.asyncio
async def test_async_set_heat_temp(
    event_loop: asyncio.AbstractEventLoop, MockConnectedGateway
):
    body = 0
    temp = 88
    result = event_loop.create_future()
    result.set_result(b"")
    with patch(
        "screenlogicpy.requests.heat.ScreenLogicProtocol.await_send_data",
        return_value=result,
    ) as mockRequest:
        gateway = MockConnectedGateway
        assert await gateway.async_set_heat_temp(body, temp)
        await gateway.async_disconnect()
        assert mockRequest.call_args.args[0] == 12528
        assert mockRequest.call_args.args[1] == struct.pack("<III", 0, body, temp)


@pytest.mark.asyncio
async def test_async_set_heat_mode(
    event_loop: asyncio.AbstractEventLoop, MockConnectedGateway
):
    body = 0
    mode = 3
    result = event_loop.create_future()
    result.set_result(b"")
    with patch(
        "screenlogicpy.requests.heat.ScreenLogicProtocol.await_send_data",
        return_value=result,
    ) as mockRequest:
        gateway = MockConnectedGateway
        assert await gateway.async_set_heat_mode(body, mode)
        await gateway.async_disconnect()
        assert mockRequest.call_args.args[0] == 12538
        assert mockRequest.call_args.args[1] == struct.pack("<III", 0, body, mode)


@pytest.mark.asyncio
async def test_async_set_color_lights(
    event_loop: asyncio.AbstractEventLoop, MockConnectedGateway
):
    mode = 7
    result = event_loop.create_future()
    result.set_result(b"")
    with patch(
        "screenlogicpy.requests.lights.ScreenLogicProtocol.await_send_data",
        return_value=result,
    ) as mockRequest:
        gateway = MockConnectedGateway
        assert await gateway.async_set_color_lights(mode)
        await gateway.async_disconnect()
        assert mockRequest.call_args.args[0] == 12556
        assert mockRequest.call_args.args[1] == struct.pack("<II", 0, mode)


@pytest.mark.asyncio
async def test_async_set_scg_config(
    event_loop: asyncio.AbstractEventLoop, MockConnectedGateway
):
    pool_output = 50
    spa_output = 0
    result = event_loop.create_future()
    result.set_result(b"")
    with patch(
        "screenlogicpy.requests.heat.ScreenLogicProtocol.await_send_data",
        return_value=result,
    ) as mockRequest:
        gateway = MockConnectedGateway
        assert await gateway.async_set_scg_config(pool_output, spa_output)
        await gateway.async_disconnect()
        assert mockRequest.call_args.args[0] == 12576
        assert mockRequest.call_args.args[1] == struct.pack(
            "<IIIII", 0, pool_output, spa_output, 0, 0
        )
