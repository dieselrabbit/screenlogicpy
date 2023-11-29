import asyncio
import pytest
from unittest.mock import call, patch

from screenlogicpy import ScreenLogicGateway
from screenlogicpy.client import ClientManager
from screenlogicpy.const.data import ATTR, DEVICE, GROUP, VALUE
from screenlogicpy.data import ScreenLogicResponseCollection

from .const_data import (
    FAKE_CONNECT_INFO,
    FAKE_GATEWAY_ADDRESS,
    FAKE_GATEWAY_MAC,
    FAKE_GATEWAY_NAME,
    FAKE_GATEWAY_PORT,
)


@pytest.mark.asyncio
async def test_mock_gateway(
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

    assert data == response_collection.decoded_complete


@pytest.mark.asyncio
async def test_gateway_connect_on_create():
    with pytest.raises(TypeError):
        _ = ScreenLogicGateway(**FAKE_CONNECT_INFO)


@pytest.mark.asyncio
async def test_gateway_async_connect_and_disconnect(
    MockProtocolAdapter: asyncio.Server,
    response_collection: ScreenLogicResponseCollection,
):
    async with MockProtocolAdapter:
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
            assert gateway.version == "POOL: 5.2 Build 738.0 Rel"
            assert gateway.controller_model == "EasyTouch2 8"
            assert gateway.equipment_flags == 32824
            assert gateway.temperature_unit == "°F"
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
                "value": 64,
                "unit": "°F",
                "device_type": "temperature",
                "state_type": "measurement",
            },
        ),
        (
            ("controller", "equipment"),
            {
                "flags": 32824,
                "list": [
                    "INTELLIBRITE",
                    "INTELLIFLO_0",
                    "INTELLIFLO_1",
                    "INTELLICHEM",
                ],
            },
        ),
        (
            ("adapter",),
            {
                "firmware": {
                    "name": "Protocol Adapter Firmware",
                    "value": "POOL: 5.2 Build 738.0 Rel",
                    "major": 5.2,
                    "minor": 738.0,
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
def test_gateway_get_data(MockConnectedGateway: ScreenLogicGateway, path, expected):
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
            64,
        ),
        (
            ("circuit", 505),
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
def test_gateway_get_value(MockConnectedGateway: ScreenLogicGateway, path, expected):
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
def test_gateway_get_name(MockConnectedGateway: ScreenLogicGateway, path, expected):
    assert MockConnectedGateway.get_name(*path) == expected


def test_gateway_get_any_strict(MockConnectedGateway: ScreenLogicGateway):
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
async def test_gateway_async_set_circuit(MockConnectedGateway: ScreenLogicGateway):
    """Test setting circuit state."""

    gateway = MockConnectedGateway

    with patch(
        "screenlogicpy.requests.button.async_make_request",
        return_value=b"",
    ) as mockRequest:
        await gateway.async_set_circuit(502, 1)

        mockRequest.assert_awaited_once_with(
            gateway._protocol,
            12530,
            b"\x00\x00\x00\x00\xF6\x01\x00\x00\x01\x00\x00\x00",
            1,
        )


@pytest.mark.asyncio
async def test_gateway_async_set_heat(MockConnectedGateway: ScreenLogicGateway):
    """Test setting heat temperature and heat mode."""

    gateway = MockConnectedGateway

    with patch(
        "screenlogicpy.requests.heat.async_make_request",
        return_value=b"",
    ) as mockRequest:
        await gateway.async_set_heat_temp(0, 84)
        await gateway.async_set_heat_mode(1, 3)

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
async def test_gateway_async_set_color_lights(MockConnectedGateway: ScreenLogicGateway):
    gateway = MockConnectedGateway

    with patch(
        "screenlogicpy.requests.lights.async_make_request",
        return_value=b"",
    ) as mockRequest:
        await gateway.async_set_color_lights(7)

        mockRequest.assert_awaited_once_with(
            gateway._protocol,
            12556,
            b"\x00\x00\x00\x00\x07\x00\x00\x00",
            1,
        )


@pytest.mark.asyncio
async def test_gateway_async_set_scg_config(MockConnectedGateway: ScreenLogicGateway):
    gateway = MockConnectedGateway

    with patch(
        "screenlogicpy.requests.scg.async_make_request",
        return_value=b"",
    ) as mockRequest:
        await gateway.async_set_scg_config(pool_setpoint=50, spa_setpoint=0)

        mockRequest.assert_awaited_once_with(
            gateway._protocol,
            12576,
            b"\x00\x00\x00\x002\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x06\x00\x00\x00",
            1,
        )


@pytest.mark.asyncio
async def test_gateway_async_set_chem_data(MockConnectedGateway: ScreenLogicGateway):
    gateway = MockConnectedGateway

    with patch(
        "screenlogicpy.requests.chemistry.async_make_request",
        return_value=b"",
    ) as mockRequest:
        await gateway.async_set_chem_data(
            ph_setpoint=7.5,
            orp_setpoint=700,
            calcium_hardness=300,
            total_alkalinity=80,
            cya=45,
            salt_tds_ppm=1000,
        )

        mockRequest.assert_awaited_once_with(
            gateway._protocol,
            12594,
            b"\x00\x00\x00\x00\xEE\x02\x00\x00\xBC\x02\x00\x00\x2C\x01\x00\x00\x50\x00\x00\x00\x2D\x00\x00\x00\xE8\x03\x00\x00",
            1,
        )


@pytest.mark.asyncio
async def test_gateway_register_async_message_handler(
    MockConnectedGateway: ScreenLogicGateway,
):
    gateway = MockConnectedGateway

    async def callback():
        pass

    MSG_CODE = 16
    gateway.register_async_message_handler(MSG_CODE, callback, 1)

    assert MSG_CODE in gateway._protocol._callbacks
    assert gateway._protocol._callbacks[MSG_CODE] == (callback, (1,))
