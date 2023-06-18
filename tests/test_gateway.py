import asyncio
import pytest
import struct
from unittest.mock import patch

from screenlogicpy import ScreenLogicGateway
from screenlogicpy.const.common import ScreenLogicRequestError
from screenlogicpy.const.data import ATTR, DEVICE, GROUP, VALUE
from screenlogicpy.const.msg import CODE

from .const_data import (
    FAKE_CONNECT_INFO,
    FAKE_GATEWAY_ADDRESS,
    FAKE_GATEWAY_MAC,
    FAKE_GATEWAY_NAME,
    FAKE_GATEWAY_PORT,
)
from .data_sets import TESTING_DATA_COLLECTION as TDC
from .fake_gateway import error_resp, expected_resp

TEST_GATEWAY_VERSION = TDC.decoded_complete[DEVICE.ADAPTER][VALUE.FIRMWARE][ATTR.VALUE]
TEST_CONTROLLER_MODEL = TDC.decoded_complete[DEVICE.CONTROLLER][VALUE.MODEL][ATTR.VALUE]
TEST_EQUIPMENT_FLAGS = TDC.decoded_complete[DEVICE.CONTROLLER][GROUP.EQUIPMENT][
    VALUE.FLAGS
]


@pytest.mark.asyncio
async def test_gateway(MockConnectedGateway):
    gateway = MockConnectedGateway
    assert gateway.ip == FAKE_GATEWAY_ADDRESS
    assert gateway.port == FAKE_GATEWAY_PORT
    assert gateway.name == FAKE_GATEWAY_NAME
    assert gateway.mac == FAKE_GATEWAY_MAC
    assert gateway.version == TEST_GATEWAY_VERSION
    assert gateway.controller_model == TEST_CONTROLLER_MODEL
    assert gateway.equipment_flags == TEST_EQUIPMENT_FLAGS
    data = gateway.get_data()
    await gateway.async_disconnect()
    assert data

    # diff = DeepDiff(data, EXPECTED_COMPLETE_DATA)
    # print(diff)
    assert data == TDC.decoded_complete


@pytest.mark.asyncio
async def test_gateway_connect(MockProtocolAdapter):
    async with MockProtocolAdapter:
        with pytest.raises(TypeError):
            _ = ScreenLogicGateway(**FAKE_CONNECT_INFO)


@pytest.mark.asyncio
async def test_gateway_late_connect(MockProtocolAdapter):
    async with MockProtocolAdapter:
        gateway = ScreenLogicGateway()
        await gateway.async_connect(**FAKE_CONNECT_INFO)
        assert gateway.ip == FAKE_GATEWAY_ADDRESS
        assert gateway.port == FAKE_GATEWAY_PORT
        assert gateway.name == FAKE_GATEWAY_NAME
        assert gateway.mac == FAKE_GATEWAY_MAC
        assert gateway.version == TEST_GATEWAY_VERSION
        assert gateway.controller_model == TEST_CONTROLLER_MODEL
        assert gateway.equipment_flags == TEST_EQUIPMENT_FLAGS
        assert gateway.is_connected
        await gateway.async_disconnect()


@pytest.mark.parametrize(
    "path, expected",
    [
        (
            ("controller", "sensor", "air_temperature"),
            {
                "name": "Air Temperature",
                "value": 57,
                "unit": "°F",
                "device_type": "temperature",
                "state_type": "measurement",
            },
        ),
        (
            ("controller", "equipment"),
            {
                "flags": 98360,
                "list": [
                    "INTELLIBRITE",
                    "INTELLIFLO_0",
                    "INTELLIFLO_1",
                    "INTELLICHEM",
                    "HYBRID_HEATER",
                ],
            },
        ),
        (
            ("adapter",),
            {
                "firmware": {
                    "name": "Protocol Adapter Firmware",
                    "value": "POOL: 5.2 Build 736.0 Rel",
                }
            },
        ),
        (
            ("intellichem", "alarm", "does_not_exist"),
            None,
        ),
        (
            ("controller", "configuration", "color", 20),
            None,
        ),
    ],
)
def test_get_data(MockConnectedGateway: ScreenLogicGateway, path, expected):
    assert MockConnectedGateway.get_data(*path) == expected


@pytest.mark.parametrize(
    "path, expected",
    [
        (
            ("controller", "configuration", "color", 2),
            (0, 255, 80),
        ),
        (
            ("controller", "sensor", "air_temperature"),
            57,
        ),
        (
            ("circuit", 502),
            1,
        ),
        (
            ("intellichem", "alarm", "does_not_exist"),
            None,
        ),
        (
            ("controller", "configuration", "color", 20),
            None,
        ),
    ],
)
def test_get_value(MockConnectedGateway: ScreenLogicGateway, path, expected):
    assert MockConnectedGateway.get_value(*path) == expected


@pytest.mark.parametrize(
    "path, expected",
    [
        (
            ("controller", "configuration", "color", 2),
            "Green",
        ),
        (
            ("controller", "sensor", "air_temperature"),
            "Air Temperature",
        ),
        (
            ("circuit", 502),
            "Pool Light",
        ),
        (
            ("intellichem", "alarm", "does_not_exist"),
            None,
        ),
        (
            ("controller", "configuration", "color", 20),
            None,
        ),
    ],
)
def test_get_name(MockConnectedGateway: ScreenLogicGateway, path, expected):
    assert MockConnectedGateway.get_name(*path) == expected


def test_get_strict(MockConnectedGateway: ScreenLogicGateway):
    with pytest.raises(KeyError):
        MockConnectedGateway.get_data(
            "intellichem", "alarm", "does_not_exist", strict=True
        )

    with pytest.raises(KeyError):
        MockConnectedGateway.get_value(
            "controller", "configuration", "body_type", 0, strict=True
        )

    with pytest.raises(KeyError):
        MockConnectedGateway.get_name(
            "controller", "configuration", "color", 20, strict=True
        )


@pytest.mark.asyncio
async def test_async_set_circuit(
    event_loop: asyncio.AbstractEventLoop, MockConnectedGateway
):
    circuit_id = 505
    circuit_state = 1
    button_code = 12530

    result = event_loop.create_future()
    result.set_result(expected_resp(button_code))
    with patch(
        "screenlogicpy.requests.button.ScreenLogicProtocol.await_send_message",
        return_value=result,
    ) as mockRequest:
        gateway = MockConnectedGateway
        assert await gateway.async_set_circuit(circuit_id, circuit_state)
        await gateway.async_disconnect()
        assert mockRequest.call_args.args[0] == button_code
        assert mockRequest.call_args.args[1] == struct.pack(
            "<III", 0, circuit_id, circuit_state
        )


@pytest.mark.asyncio
async def test_async_set_circuit_retry(
    event_loop: asyncio.AbstractEventLoop, MockConnectedGateway
):

    circuit_id = 505
    circuit_state = 1
    button_code = 12530

    def req_fut(result=None):
        nonlocal event_loop
        fut = event_loop.create_future()
        if result:
            fut.set_result(result)
        return fut

    with patch(
        "screenlogicpy.requests.button.ScreenLogicProtocol.await_send_message",
        side_effect=(
            req_fut(error_resp(button_code)),
            req_fut(expected_resp(button_code)),
        ),
    ) as mockRequest, patch("screenlogicpy.const.msg.COM_RETRY_WAIT", 1):
        gateway = MockConnectedGateway
        assert await gateway.async_set_circuit(circuit_id, circuit_state)
        await gateway.async_disconnect()
        assert mockRequest.call_count == 2
        assert mockRequest.call_args.args[0] == button_code
        assert mockRequest.call_args.args[1] == struct.pack(
            "<III", 0, circuit_id, circuit_state
        )


@pytest.mark.asyncio
async def test_async_set_circuit_timeout(
    event_loop: asyncio.AbstractEventLoop, MockConnectedGateway
):

    circuit_id = 505
    circuit_state = 1
    button_code = 12530

    async def patched_request(self, async_method, *args, **kwargs):
        if kwargs.get("max_retries") is None:
            kwargs["max_retries"] = 1

        async def attempt_request():
            if await self.async_connect():
                return await async_method(self._protocol, *args, **kwargs)

        return await attempt_request()

    with patch(
        "screenlogicpy.requests.button.ScreenLogicProtocol.await_send_message",
        side_effect=(
            event_loop.create_future(),
            event_loop.create_future(),
        ),
    ) as mockRequest, patch.object(
        ScreenLogicGateway, "_async_connected_request", patched_request
    ), patch(
        "screenlogicpy.const.msg.COM_RETRY_WAIT", 1
    ):
        gateway: ScreenLogicGateway = MockConnectedGateway
        with pytest.raises(ScreenLogicRequestError) as e_info:
            await gateway.async_set_circuit(circuit_id, circuit_state)
        await gateway.async_disconnect()
        assert "Timeout" in e_info.value.msg
        assert mockRequest.call_count == 2
        assert mockRequest.call_args.args[0] == button_code
        assert mockRequest.call_args.args[1] == struct.pack(
            "<III", 0, circuit_id, circuit_state
        )


@pytest.mark.asyncio
async def test_async_set_heat_temp(
    event_loop: asyncio.AbstractEventLoop, MockConnectedGateway
):
    body = 0
    temp = 88
    heat_temp_code = 12528

    result = event_loop.create_future()
    result.set_result(expected_resp(heat_temp_code))
    with patch(
        "screenlogicpy.requests.heat.ScreenLogicProtocol.await_send_message",
        return_value=result,
    ) as mockRequest:
        gateway = MockConnectedGateway
        assert await gateway.async_set_heat_temp(body, temp)
        await gateway.async_disconnect()
        assert mockRequest.call_args.args[0] == heat_temp_code
        assert mockRequest.call_args.args[1] == struct.pack("<III", 0, body, temp)


@pytest.mark.asyncio
async def test_async_set_heat_mode(
    event_loop: asyncio.AbstractEventLoop, MockConnectedGateway
):
    body = 0
    mode = 3
    heat_mode_code = 12538

    result = event_loop.create_future()
    result.set_result(expected_resp(heat_mode_code))
    with patch(
        "screenlogicpy.requests.heat.ScreenLogicProtocol.await_send_message",
        return_value=result,
    ) as mockRequest:
        gateway = MockConnectedGateway
        assert await gateway.async_set_heat_mode(body, mode)
        await gateway.async_disconnect()
        assert mockRequest.call_args.args[0] == heat_mode_code
        assert mockRequest.call_args.args[1] == struct.pack("<III", 0, body, mode)


@pytest.mark.asyncio
async def test_async_set_color_lights(
    event_loop: asyncio.AbstractEventLoop, MockConnectedGateway
):
    mode = 7
    color_lights_code = 12556

    result = event_loop.create_future()
    result.set_result(expected_resp(color_lights_code))
    with patch(
        "screenlogicpy.requests.lights.ScreenLogicProtocol.await_send_message",
        return_value=result,
    ) as mockRequest:
        gateway = MockConnectedGateway
        assert await gateway.async_set_color_lights(mode)
        await gateway.async_disconnect()
        assert mockRequest.call_args.args[0] == color_lights_code
        assert mockRequest.call_args.args[1] == struct.pack("<II", 0, mode)


@pytest.mark.asyncio
async def test_async_set_scg_config(
    event_loop: asyncio.AbstractEventLoop, MockConnectedGateway
):
    pool_output = 50
    spa_output = 0
    scg_code = 12576

    result = event_loop.create_future()
    result.set_result(expected_resp(scg_code))
    with patch(
        "screenlogicpy.requests.heat.ScreenLogicProtocol.await_send_message",
        return_value=result,
    ) as mockRequest:
        gateway = MockConnectedGateway
        assert await gateway.async_set_scg_config(pool_output, spa_output)
        await gateway.async_disconnect()
        assert mockRequest.call_args.args[0] == scg_code
        assert mockRequest.call_args.args[1] == struct.pack(
            "<IIIII", 0, pool_output, spa_output, 0, 0
        )


@pytest.mark.asyncio
async def test_async_send_message_retry(
    event_loop: asyncio.AbstractEventLoop, MockConnectedGateway: ScreenLogicGateway
):
    result = event_loop.create_future()
    result.set_result(expected_resp(CODE.POOLSTATUS_QUERY, TDC.status.raw))
    with patch(
        "screenlogicpy.requests.gateway.ScreenLogicProtocol.await_send_message",
        side_effect=(event_loop.create_future(), event_loop.create_future(), result),
    ) as mockRequest, patch("screenlogicpy.const.msg.COM_RETRY_WAIT", 1):
        gateway = MockConnectedGateway
        gateway.set_max_retries(3)
        response = await gateway.async_send_message(
            CODE.POOLSTATUS_QUERY, struct.pack("<I", 0)
        )
        assert response == TDC.status.raw
        assert mockRequest.call_count == 3
        assert mockRequest.call_args.args[0] == CODE.POOLSTATUS_QUERY
        assert mockRequest.call_args.args[1] == struct.pack("<I", 0)
