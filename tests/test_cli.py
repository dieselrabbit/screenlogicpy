import json
from io import StringIO
from unittest.mock import patch
from screenlogicpy.cli import cli
from tests.const_data import (
    FAKE_CONFIG_RESPONSE,
    FAKE_STATUS_RESPONSE,
    FAKE_PUMP_RESPONSE,
    FAKE_CHEMISTRY_RESPONSE,
    FAKE_SCG_RESPONSE,
    EXPECTED_COMPLETE_DATA,
    EXPECTED_DASHBOARD,
    EXPECTED_VERBOSE_PREAMBLE,
)

OUTPUT = False


def mockCLI(args, expected):
    with patch("socket.socket", autospec=True) as mockSocket, patch(
        "screenlogicpy.cli.discover", return_value=[{"ip": "1.1.1.1", "port": 80}]
    ) as mockDiscovery, patch(
        "screenlogicpy.gateway.connect_to_gateway",
        return_value=(mockSocket, "00:00:00:00:00:00"),
    ) as mockConnectRequest, patch(
        "screenlogicpy.gateway.request_gateway_version", return_value="0.0.1"
    ) as mockVersionRequest, patch(
        "screenlogicpy.requests.config.sendReceiveMessage",
        return_value=FAKE_CONFIG_RESPONSE,
    ) as mockConfigRequest, patch(
        "screenlogicpy.requests.status.sendReceiveMessage",
        return_value=FAKE_STATUS_RESPONSE,
    ) as mockStatusRequest, patch(
        "screenlogicpy.requests.pump.sendReceiveMessage",
        return_value=FAKE_PUMP_RESPONSE,
    ) as mockPumpRequest, patch(
        "screenlogicpy.requests.chemistry.sendReceiveMessage",
        return_value=FAKE_CHEMISTRY_RESPONSE,
    ) as mockChemistryRequest, patch(
        "screenlogicpy.requests.scg.sendReceiveMessage", return_value=FAKE_SCG_RESPONSE
    ) as mockSCGRequest, patch(
        "sys.stdout", new=StringIO()
    ) as mockOut:
        result = cli(args)

    if OUTPUT:
        exp = open(r"scratchpad\local_expected.json", "w+")
        exp.write(expected)
        exp.close()

        res = open(r"scratchpad\local_result.json", "w+")
        res.write(mockOut.getvalue().strip())
        res.close()

    assert result == 0
    assert mockOut.getvalue().strip() == expected
    assert mockDiscovery.call_count == 1

    if "set" in args:
        if "color-lights" in args or "cl" in args:
            connectCount = 2
        else:
            connectCount = 3
    else:
        connectCount = 1
    assert mockConnectRequest.call_count == connectCount
    assert mockVersionRequest.call_count == connectCount

    assert mockConfigRequest.call_count == 1

    if "set" not in args or "color-lights" in args or "cl" in args:
        updateCount = 1
    else:
        updateCount = 2
    assert mockStatusRequest.call_count == updateCount
    assert mockPumpRequest.call_count == updateCount
    assert mockChemistryRequest.call_count == updateCount
    assert mockSCGRequest.call_count == updateCount


def test_cli_dashboard():
    mockCLI((), EXPECTED_DASHBOARD)


def test_get_circuit():
    mockCLI(("get", "circuit", "500"), "0")

    mockCLI(("get", "c", "502"), "1")

    mockCLI(("-v", "get", "c", "502"), EXPECTED_VERBOSE_PREAMBLE + "Pool Light: On")


def test_get_current_temp():
    mockCLI(("get", "current-temp", "0"), "56")

    mockCLI(("get", "t", "spa"), "97")


def test_get_heat_mode():
    mockCLI(("get", "heat-mode", "pool"), "0")

    mockCLI(("get", "hm", "1"), "3")


def test_get_heat_temp():
    mockCLI(("get", "heat-temp", "0"), "86")

    mockCLI(("get", "ht", "spa"), "97")


def test_get_heat_state():
    mockCLI(("get", "heat-state", "0"), "0")

    mockCLI(("get", "hs", "spa"), "0")


def test_get_json():
    mockCLI(("get", "json"), json.dumps(EXPECTED_COMPLETE_DATA, indent=2))


def test_set_circuit():
    with patch("screenlogicpy.gateway.request_pool_button_press", return_value=True):
        mockCLI(("set", "circuit", "500", "off"), "0")
        mockCLI(
            ("-v", "set", "circuit", "502", "1"),
            EXPECTED_VERBOSE_PREAMBLE + "Pool Light: On",
        )


def test_set_heat_mode():
    with patch("screenlogicpy.gateway.request_set_heat_mode", return_value=True):
        mockCLI(("set", "heat-mode", "pool", "0"), "0")

        mockCLI(
            ("-v", "set", "hm", "1", "heater"),
            EXPECTED_VERBOSE_PREAMBLE + "Spa Heat Mode: Heater",
        )


def test_set_heat_temp():
    with patch("screenlogicpy.gateway.request_set_heat_setpoint", return_value=True):
        mockCLI(("set", "heat-temp", "pool", "86"), "86")

        mockCLI(
            ("-v", "set", "ht", "1", "97"),
            EXPECTED_VERBOSE_PREAMBLE + "Spa Heat Set Point: 97",
        )


def test_set_color_lights():
    with patch("screenlogicpy.gateway.request_pool_lights_command", return_value=True):
        mockCLI(("set", "color-lights", "romance"), "6")

        mockCLI(
            ("-v", "set", "cl", "0"),
            EXPECTED_VERBOSE_PREAMBLE + "Set color mode to All Off",
        )
