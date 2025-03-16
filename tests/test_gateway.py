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
    mock_gateway: ScreenLogicGateway, response_collection: ScreenLogicResponseCollection
):

    assert mock_gateway.ip == FAKE_GATEWAY_ADDRESS
    assert mock_gateway.port == FAKE_GATEWAY_PORT
    assert mock_gateway.name == FAKE_GATEWAY_NAME
    assert mock_gateway.mac == FAKE_GATEWAY_MAC
    assert (
        mock_gateway.version
        == response_collection.decoded_complete[DEVICE.ADAPTER][VALUE.FIRMWARE][
            ATTR.VALUE
        ]
    )
    assert (
        mock_gateway.controller_model
        == response_collection.decoded_complete[DEVICE.CONTROLLER][VALUE.MODEL][
            ATTR.VALUE
        ]
    )
    assert (
        mock_gateway.equipment_flags
        == response_collection.decoded_complete[DEVICE.CONTROLLER][GROUP.EQUIPMENT][
            VALUE.FLAGS
        ]
    )

    data = mock_gateway.get_data()

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
    mock_gateway: ScreenLogicGateway,
    response_collection: ScreenLogicResponseCollection,
):
    with patch(
        "screenlogicpy.requests.status.async_make_request",
        return_value=response_collection.status.raw,
    ) as mock_request:
        await mock_gateway.async_get_status()

        mock_request.assert_awaited_once_with(
            mock_gateway._protocol, 12526, b"\x00\x00\x00\x00", 1
        )
        assert mock_gateway.get_debug()["status"] == response_collection.status.raw


@pytest.mark.asyncio
async def test_gateway_get_pumps(
    mock_gateway: ScreenLogicGateway,
    response_collection: ScreenLogicResponseCollection,
):
    with patch(
        "screenlogicpy.requests.pump.async_make_request",
        side_effect=[
            response_collection.pumps[0].raw,
            response_collection.pumps[1].raw,
        ],
    ) as mock_request:
        await mock_gateway.async_get_pumps()

        mock_request.assert_has_awaits(
            [
                call(mock_gateway._protocol, 12584, b"\x00\x00\x00\x00\x00\x00\x00\x00", 1),
                call(mock_gateway._protocol, 12584, b"\x00\x00\x00\x00\x01\x00\x00\x00", 1),
            ]
        )
        assert mock_gateway.get_debug()["pumps"][0] == response_collection.pumps[0].raw
        assert mock_gateway.get_debug()["pumps"][1] == response_collection.pumps[1].raw


@pytest.mark.asyncio
async def test_gateway_get_chemistry(
    mock_gateway: ScreenLogicGateway,
    response_collection: ScreenLogicResponseCollection,
):
    with patch(
        "screenlogicpy.requests.chemistry.async_make_request",
        return_value=response_collection.chemistry.raw,
    ) as mock_request:
        await mock_gateway.async_get_chemistry()

        mock_request.assert_awaited_once_with(
            mock_gateway._protocol, 12592, b"\x00\x00\x00\x00", 1
        )
        assert mock_gateway.get_debug()["chemistry"] == response_collection.chemistry.raw


@pytest.mark.asyncio
async def test_gateway_get_scg(
    mock_gateway: ScreenLogicGateway,
    response_collection: ScreenLogicResponseCollection,
):
    with patch(
        "screenlogicpy.requests.scg.async_make_request",
        return_value=response_collection.scg.raw,
    ) as mock_request:
        await mock_gateway.async_get_scg()

        mock_request.assert_awaited_once_with(
            mock_gateway._protocol, 12572, b"\x00\x00\x00\x00", 1
        )
        assert mock_gateway.get_debug()["scg"] == response_collection.scg.raw


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
            ("adapter", "firmware"),
            {
                "name": "Protocol Adapter Firmware",
                "value": "POOL: 5.2 Build 738.0 Rel",
                "major": 5.2,
                "minor": 738.0,
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
def test_gateway_get_data(mock_gateway: ScreenLogicGateway, path, expected):
    assert mock_gateway.get_data(*path) == expected


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
def test_gateway_get_value(mock_gateway: ScreenLogicGateway, path, expected):
    assert mock_gateway.get_value(*path) == expected


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
def test_gateway_get_name(mock_gateway: ScreenLogicGateway, path, expected):
    assert mock_gateway.get_name(*path) == expected


def test_gateway_get_any_strict(mock_gateway: ScreenLogicGateway):
    with pytest.raises(KeyError):
        mock_gateway.get_data(
            "intellichem", "alarm", "does_not_exist", strict=True
        )

    with pytest.raises(KeyError):
        mock_gateway.get_value(
            "controller", "configuration", "body_type", 0, strict=True
        )

    with pytest.raises(KeyError):
        mock_gateway.get_name(
            "controller", "configuration", "color", 20, strict=True
        )


@pytest.mark.asyncio
async def test_gateway_async_set_circuit(mock_gateway: ScreenLogicGateway):
    """Test setting circuit state."""
    with patch(
        "screenlogicpy.requests.button.async_make_request",
        return_value=b"",
    ) as mockRequest:
        await mock_gateway.async_set_circuit(502, 1)

        mockRequest.assert_awaited_once_with(
            mock_gateway._protocol,
            12530,
            b"\x00\x00\x00\x00\xf6\x01\x00\x00\x01\x00\x00\x00",
            1,
        )


@pytest.mark.asyncio
async def test_gateway_async_set_heat(mock_gateway: ScreenLogicGateway):
    """Test setting heat temperature and heat mode."""
    with patch(
        "screenlogicpy.requests.heat.async_make_request",
        return_value=b"",
    ) as mockRequest:
        await mock_gateway.async_set_heat_temp(0, 84)
        await mock_gateway.async_set_heat_mode(1, 3)

        mockRequest.assert_has_awaits(
            [
                call(
                    mock_gateway._protocol,
                    12528,
                    b"\x00\x00\x00\x00\x00\x00\x00\x00T\x00\x00\x00",
                    1,
                ),
                call(
                    mock_gateway._protocol,
                    12538,
                    b"\x00\x00\x00\x00\x01\x00\x00\x00\x03\x00\x00\x00",
                    1,
                ),
            ]
        )


@pytest.mark.asyncio
async def test_gateway_async_set_color_lights(mock_gateway: ScreenLogicGateway):
    with patch(
        "screenlogicpy.requests.lights.async_make_request",
        return_value=b"",
    ) as mockRequest:
        await mock_gateway.async_set_color_lights(7)

        mockRequest.assert_awaited_once_with(
            mock_gateway._protocol,
            12556,
            b"\x00\x00\x00\x00\x07\x00\x00\x00",
            1,
        )


@pytest.mark.asyncio
async def test_gateway_async_set_scg_config(mock_gateway: ScreenLogicGateway):
    with patch(
        "screenlogicpy.requests.scg.async_make_request",
        return_value=b"",
    ) as mockRequest:
        await mock_gateway.async_set_scg_config(pool_setpoint=50, spa_setpoint=0)

        mockRequest.assert_awaited_once_with(
            mock_gateway._protocol,
            12576,
            b"\x00\x00\x00\x002\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x06\x00\x00\x00",
            1,
        )


@pytest.mark.asyncio
async def test_gateway_async_set_chem_data(mock_gateway: ScreenLogicGateway):
    with patch(
        "screenlogicpy.requests.chemistry.async_make_request",
        return_value=b"",
    ) as mockRequest:
        await mock_gateway.async_set_chem_data(
            ph_setpoint=7.5,
            orp_setpoint=700,
            calcium_hardness=300,
            total_alkalinity=80,
            cya=45,
            salt_tds_ppm=1000,
        )

        mockRequest.assert_awaited_once_with(
            mock_gateway._protocol,
            12594,
            b"\x00\x00\x00\x00\xee\x02\x00\x00\xbc\x02\x00\x00\x2c\x01\x00\x00\x50\x00\x00\x00\x2d\x00\x00\x00\xe8\x03\x00\x00",
            1,
        )


@pytest.mark.asyncio
async def test_gateway_register_async_message_handler(
    mock_gateway: ScreenLogicGateway,
):
    async def callback():
        pass

    MSG_CODE = 16
    mock_gateway.register_async_message_handler(MSG_CODE, callback, 1)

    mock_gateway._protocol.register_async_message_callback.assert_called_with(MSG_CODE, callback, 1)
