from unittest.mock import patch
import socket  # noqa: F401
import struct
from tests.const_data import (
    FAKE_CONFIG_RESPONSE,
    FAKE_STATUS_RESPONSE,
    FAKE_PUMP_RESPONSE,
    FAKE_CHEMISTRY_RESPONSE,
    EXPECTED_CONFIG_DATA,
    EXPECTED_STATUS_DATA,
    EXPECTED_PUMP_DATA,
    EXPECTED_CHEMISTRY_DATA,
)
from screenlogicpy.requests import (
    request_pool_config,
    request_pool_status,
    request_pump_status,
    request_chemistry,
    request_pool_button_press,
    request_set_heat_mode,
    request_set_heat_setpoint,
    request_pool_lights_command,
)


def test_request_pool_config():
    data = {}
    with patch(
        "screenlogicpy.requests.config.sendReceiveMessage",
        return_value=FAKE_CONFIG_RESPONSE,
    ) as mockRequest, patch("socket.socket", autospec=True) as mockSocket:
        request_pool_config(mockSocket, data)

    assert mockRequest.call_args[0][1] == 12532
    assert data == EXPECTED_CONFIG_DATA


def test_request_pool_status():
    data = {}
    with patch(
        "screenlogicpy.requests.status.sendReceiveMessage",
        return_value=FAKE_STATUS_RESPONSE,
    ) as mockRequest, patch("socket.socket", autospec=True) as mockSocket:
        request_pool_status(mockSocket, data)

    assert mockRequest.call_args[0][1] == 12526
    assert data == EXPECTED_STATUS_DATA


def test_request_pump_status():
    data = {}
    with patch(
        "screenlogicpy.requests.pump.sendReceiveMessage",
        return_value=FAKE_PUMP_RESPONSE,
    ) as mockRequest, patch("socket.socket", autospec=True) as mockSocket:
        request_pump_status(mockSocket, data, 0)

    assert mockRequest.call_args[0][1] == 12584
    assert data == EXPECTED_PUMP_DATA


def test_request_chemistry():
    data = {}
    with patch(
        "screenlogicpy.requests.chemistry.sendReceiveMessage",
        return_value=FAKE_CHEMISTRY_RESPONSE,
    ) as mockRequest, patch("socket.socket", autospec=True) as mockSocket:
        request_chemistry(mockSocket, data)

    assert mockRequest.call_args[0][1] == 12592
    assert data == EXPECTED_CHEMISTRY_DATA


def test_request_pool_button_press():
    circuit_id = 505
    circuit_state = 1
    with patch(
        "screenlogicpy.requests.button.sendReceiveMessage", return_value=b""
    ) as mockRequest, patch("socket.socket", autospec=True) as mockSocket:
        result = request_pool_button_press(mockSocket, circuit_id, circuit_state)

    assert mockRequest.call_args[0][1] == 12530
    assert mockRequest.call_args[0][2] == struct.pack(
        "<III", 0, circuit_id, circuit_state
    )
    assert result


def test_request_set_heat_mode():
    body = 0
    mode = 3
    with patch(
        "screenlogicpy.requests.heat.sendReceiveMessage", return_value=b""
    ) as mockRequest, patch("socket.socket", autospec=True) as mockSocket:
        success = request_set_heat_mode(mockSocket, body, mode)

    assert mockRequest.call_args[0][1] == 12538
    assert mockRequest.call_args[0][2] == struct.pack("<III", 0, body, mode)
    assert success


def test_request_set_heat_setpoint():
    body = 0
    temp = 88
    with patch(
        "screenlogicpy.requests.heat.sendReceiveMessage", return_value=b""
    ) as mockRequest, patch("socket.socket", autospec=True) as mockSocket:
        success = request_set_heat_setpoint(mockSocket, body, temp)

    assert mockRequest.call_args[0][1] == 12528
    assert mockRequest.call_args[0][2] == struct.pack("<III", 0, body, temp)
    assert success


def test_request_pool_lights_command():
    mode = 7
    with patch(
        "screenlogicpy.requests.lights.sendReceiveMessage", return_value=b""
    ) as mockRequest, patch("socket.socket", autospec=True) as mockSocket:
        success = request_pool_lights_command(mockSocket, mode)

    assert mockRequest.call_args[0][1] == 12556
    assert mockRequest.call_args[0][2] == struct.pack("<II", 0, mode)
    assert success
