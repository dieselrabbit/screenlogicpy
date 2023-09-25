import asyncio
import pytest
import struct
from unittest.mock import call, patch

from screenlogicpy import ScreenLogicGateway
from screenlogicpy.client import ClientManager
from screenlogicpy.const.common import ScreenLogicRequestError
from screenlogicpy.const.data import ATTR, DEVICE, GROUP, VALUE
from screenlogicpy.const.msg import CODE
from screenlogicpy.data import ScreenLogicResponseCollection
from screenlogicpy.requests.request import async_make_request

from .const_data import (
    FAKE_CONNECT_INFO,
    FAKE_GATEWAY_ADDRESS,
    FAKE_GATEWAY_MAC,
    FAKE_GATEWAY_NAME,
    FAKE_GATEWAY_PORT,
)

from .conftest import DEFAULT_RESPONSE, load_response_collection
from .data_sets import TESTING_DATA_COLLECTION as TDC
from .fake_gateway import error_resp, expected_resp

TEST_GATEWAY_VERSION = TDC.decoded_complete[DEVICE.ADAPTER][VALUE.FIRMWARE][ATTR.VALUE]
TEST_CONTROLLER_MODEL = TDC.decoded_complete[DEVICE.CONTROLLER][VALUE.MODEL][ATTR.VALUE]
TEST_EQUIPMENT_FLAGS = TDC.decoded_complete[DEVICE.CONTROLLER][GROUP.EQUIPMENT][
    VALUE.FLAGS
]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "response_collection", load_response_collection([DEFAULT_RESPONSE])
)
async def test_gateway(
    MockConnectedGateway, response_collection: ScreenLogicResponseCollection
):
    gateway = MockConnectedGateway
    assert gateway.ip == FAKE_GATEWAY_ADDRESS
    assert gateway.port == FAKE_GATEWAY_PORT
    assert gateway.name == FAKE_GATEWAY_NAME
    assert gateway.mac == FAKE_GATEWAY_MAC
    assert (
        gateway.version
        == response_collection.decoded_complete[DEVICE.ADAPTER][VALUE.FIRMWARE][
            ATTR.VALUE
        ]
    )
    assert (
        gateway.controller_model
        == response_collection.decoded_complete[DEVICE.CONTROLLER][VALUE.MODEL][
            ATTR.VALUE
        ]
    )
    assert (
        gateway.equipment_flags
        == response_collection.decoded_complete[DEVICE.CONTROLLER][GROUP.EQUIPMENT][
            VALUE.FLAGS
        ]
    )
    data = gateway.get_data()
    assert data

    # diff = DeepDiff(data, EXPECTED_COMPLETE_DATA)
    # print(diff)
    assert data == response_collection.decoded_complete


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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "response_collection", load_response_collection([DEFAULT_RESPONSE])
)
async def test_gateway_async_connect_and_disconnect(
    FakeProtocolAdapter: asyncio.Server,
    response_collection: ScreenLogicResponseCollection,
):
    async with FakeProtocolAdapter:
        with patch(
            "screenlogicpy.gateway.ClientManager",
            spec=ClientManager,
        ) as client_manager:

            gateway = ScreenLogicGateway()
            await gateway.async_connect(**FAKE_CONNECT_INFO)

            client_mgr_inst = client_manager.return_value
            assert gateway.is_connected
            assert gateway.ip == FAKE_GATEWAY_ADDRESS
            assert gateway.port == FAKE_GATEWAY_PORT
            assert gateway.name == FAKE_GATEWAY_NAME
            assert gateway.mac == FAKE_GATEWAY_MAC
            assert (
                gateway.version
                == response_collection.decoded_complete[DEVICE.ADAPTER][VALUE.FIRMWARE][
                    ATTR.VALUE
                ]
            )
            assert (
                gateway.controller_model
                == response_collection.decoded_complete[DEVICE.CONTROLLER][VALUE.MODEL][
                    ATTR.VALUE
                ]
            )
            assert (
                gateway.equipment_flags
                == response_collection.decoded_complete[DEVICE.CONTROLLER][
                    GROUP.EQUIPMENT
                ][VALUE.FLAGS]
            )

            await gateway.async_disconnect()

            assert not gateway.is_connected
            client_mgr_inst.attach.assert_awaited_once()
            client_mgr_inst.async_unsubscribe_gateway.assert_awaited_once()


@pytest.mark.asyncio
async def test_gateway_get_status(
    MockConnectedGateway: ScreenLogicGateway,
    response_collection: ScreenLogicResponseCollection,
):

    gateway = MockConnectedGateway

    with patch(
        "screenlogicpy.requests.status.async_make_request",
        return_value=response_collection.status.raw,
    ) as mock_request:

        await gateway.async_get_status()

        mock_request.assert_awaited_once_with(
            gateway._protocol, 12526, b"\x00\x00\x00\x00", 1
        )
        assert gateway.get_debug()["status"] == response_collection.status.raw


@pytest.mark.asyncio
async def test_gateway_get_pumps(
    MockConnectedGateway: ScreenLogicGateway,
    response_collection: ScreenLogicResponseCollection,
):

    gateway = MockConnectedGateway

    with patch(
        "screenlogicpy.requests.pump.async_make_request",
        side_effect=[
            response_collection.pumps[0].raw,
            response_collection.pumps[1].raw,
        ],
    ) as mock_request:

        await gateway.async_get_pumps()

        mock_request.assert_has_awaits(
            [
                call(gateway._protocol, 12584, b"\x00\x00\x00\x00\x00\x00\x00\x00", 1),
                call(gateway._protocol, 12584, b"\x00\x00\x00\x00\x01\x00\x00\x00", 1),
            ]
        )
        assert gateway.get_debug()["pumps"][0] == response_collection.pumps[0].raw
        assert gateway.get_debug()["pumps"][1] == response_collection.pumps[1].raw


@pytest.mark.asyncio
async def test_gateway_get_chemistry(
    MockConnectedGateway: ScreenLogicGateway,
    response_collection: ScreenLogicResponseCollection,
):

    gateway = MockConnectedGateway

    with patch(
        "screenlogicpy.requests.chemistry.async_make_request",
        return_value=response_collection.chemistry.raw,
    ) as mock_request:

        await gateway.async_get_chemistry()

        mock_request.assert_awaited_once_with(
            gateway._protocol, 12592, b"\x00\x00\x00\x00", 1
        )
        assert gateway.get_debug()["chemistry"] == response_collection.chemistry.raw


@pytest.mark.asyncio
async def test_gateway_get_scg(
    MockConnectedGateway: ScreenLogicGateway,
    response_collection: ScreenLogicResponseCollection,
):

    gateway = MockConnectedGateway

    with patch(
        "screenlogicpy.requests.scg.async_make_request",
        return_value=response_collection.scg.raw,
    ) as mock_request:

        await gateway.async_get_scg()

        mock_request.assert_awaited_once_with(
            gateway._protocol, 12572, b"\x00\x00\x00\x00", 1
        )
        assert gateway.get_debug()["scg"] == response_collection.scg.raw


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
async def test_async_set_circuit(MockConnectedGateway: ScreenLogicGateway):

    gateway = MockConnectedGateway

    with patch(
        "screenlogicpy.requests.button.async_make_request",
        return_value=b"",
    ) as mockRequest:

        assert await gateway.async_set_circuit(505, 1)

        mockRequest.assert_awaited_once_with(
            gateway._protocol,
            12530,
            b"\x00\x00\x00\x00\xf9\x01\x00\x00\x01\x00\x00\x00",
            1,
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
async def test_async_set_heat(MockConnectedGateway: ScreenLogicGateway):
    """Test setting heat temperature and head mode."""

    gateway = MockConnectedGateway

    with patch(
        "screenlogicpy.requests.heat.async_make_request",
        return_value=b"",
    ) as mockRequest:

        assert await gateway.async_set_heat_temp(0, 84)
        assert await gateway.async_set_heat_mode(1, 3)

        mockRequest.assert_has_awaits(
            [
                call(
                    gateway._protocol,
                    12528,
                    b"\x00\x00\x00\x00\x00\x00\x00\x00T\x00\x00\x00",
                    1,
                ),
                call(
                    gateway._protocol,
                    12538,
                    b"\x00\x00\x00\x00\x01\x00\x00\x00\x03\x00\x00\x00",
                    1,
                ),
            ]
        )


@pytest.mark.asyncio
async def test_async_set_color_lights(MockConnectedGateway: ScreenLogicGateway):

    gateway = MockConnectedGateway

    with patch(
        "screenlogicpy.requests.lights.async_make_request",
        return_value=b"",
    ) as mockRequest:

        assert await gateway.async_set_color_lights(7)

        mockRequest.assert_awaited_once_with(
            gateway._protocol,
            12556,
            b"\x00\x00\x00\x00\x07\x00\x00\x00",
            1,
        )


@pytest.mark.asyncio
async def test_async_set_scg_config(MockConnectedGateway: ScreenLogicGateway):

    gateway = MockConnectedGateway

    with patch(
        "screenlogicpy.requests.scg.async_make_request",
        return_value=b"",
    ) as mockRequest:

        assert await gateway.async_set_scg_config(50, 0)

        mockRequest.assert_awaited_once_with(
            gateway._protocol,
            12576,
            b"\x00\x00\x00\x002\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
            1,
        )


@pytest.mark.asyncio
async def test_async_set_chem_data(MockConnectedGateway: ScreenLogicGateway):

    gateway = MockConnectedGateway

    with patch(
        "screenlogicpy.requests.chemistry.async_make_request",
        return_value=b"",
    ) as mockRequest:

        assert await gateway.async_set_chem_data(7.5, 700, 300, 80, 45, 1000)

        mockRequest.assert_awaited_once_with(
            gateway._protocol,
            12594,
            b"\x00\x00\x00\x00\xEE\x02\x00\x00\xBC\x02\x00\x00\x2C\x01\x00\x00\x50\x00\x00\x00\x2D\x00\x00\x00\xE8\x03\x00\x00",
            1,
        )


@pytest.mark.asyncio
async def test_gateway_connection_closed(
    event_loop: asyncio.AbstractEventLoop, MockDisconnectingProtocolAdapter
):
    async with MockDisconnectingProtocolAdapter as server:
        with patch("screenlogicpy.const.msg.COM_RETRY_WAIT", 1):
            # mock_instance._async_connected_request.side_effect = lambda *args, **kwargs: S
            gateway = ScreenLogicGateway()
            await gateway.async_connect(**FAKE_CONNECT_INFO)
            assert gateway.is_connected
            await gateway.async_update()
            # gw_inst = mock_gateway.return_value

            with patch(
                "screenlogicpy.requests.status.async_make_request",
                wraps=async_make_request,
            ) as mock_async_make_request:

                enable_disconnect_on_next_call = await gateway.async_send_message(
                    1111, struct.pack("<I", 0)
                )
                assert enable_disconnect_on_next_call == b""

                await gateway.async_get_status()

                print(mock_async_make_request.mock_calls)

                assert mock_async_make_request.call_count == 2
                assert (
                    mock_async_make_request.call_args_list[0][0]
                    != mock_async_make_request.call_args_list[1][0]
                )
                last_call = call(
                    gateway._protocol,
                    CODE.POOLSTATUS_QUERY,
                    b"\x00\x00\x00\x00",
                    1,
                )
                assert mock_async_make_request.call_args_list[0] != last_call
                assert mock_async_make_request.call_args_list[1] == last_call
        server.close()
