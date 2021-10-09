import asyncio
import json
from io import StringIO
from unittest.mock import patch

import pytest
from screenlogicpy.cli import cli
from .const_data import (
    FAKE_CONFIG_RESPONSE,
    FAKE_STATUS_RESPONSE,
    FAKE_PUMP_RESPONSE,
    FAKE_CHEMISTRY_RESPONSE,
    FAKE_SCG_RESPONSE,
    FAKE_CONNECT_INFO,
    EXPECTED_COMPLETE_DATA,
    EXPECTED_DASHBOARD,
    EXPECTED_VERBOSE_PREAMBLE,
)

# from .test_gateway import MockConnectedGateway

OUTPUT = False


@pytest.mark.asyncio
@pytest.fixture
async def MockCLI(event_loop: asyncio.AbstractEventLoop, MockConnectedGateway):
    async def _mock_cli(args, expected):
        with patch(
            "screenlogicpy.cli.async_discover", return_value=[FAKE_CONNECT_INFO]
        ), patch(
            "screenlogicpy.cli.ScreenLogicGateway",
            return_value=MockConnectedGateway,
        ), patch(
            "sys.stdout", new=StringIO()
        ) as mockOut:
            result = await cli(args)
            assert mockOut.getvalue().strip() == expected
            assert result == 99

    return _mock_cli


def OLDMockCLI(args, expected):
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


@pytest.mark.asyncio
async def test_cli_dashboard(MockProtocolAdapter):
    async with MockProtocolAdapter:
        with patch(
            "screenlogicpy.cli.async_discover", return_value=[FAKE_CONNECT_INFO]
        ), patch("sys.stdout", new=StringIO()) as mockOut:
            result = await cli(())
            assert mockOut.getvalue().strip() == EXPECTED_DASHBOARD
            assert result == 0


@pytest.mark.asyncio
async def test_get_circuit(MockProtocolAdapter, capsys):
    async with MockProtocolAdapter:
        with patch(
            "screenlogicpy.cli.async_discover", return_value=[FAKE_CONNECT_INFO]
        ):
            test_input = [
                (("get", "circuit", "500"), "0"),
                (("get", "c", "502"), "1"),
                (
                    ("-v", "get", "c", "502"),
                    EXPECTED_VERBOSE_PREAMBLE + "Pool Light: On",
                ),
            ]

            for args, expected in test_input:
                result = await cli(args)
                std = capsys.readouterr()
                assert std.out.strip() == expected
                assert result == 0

    # MockCLI(("get", "circuit", "500"), "0")

    # MockCLI(("get", "c", "502"), "1")

    # MockCLI(("-v", "get", "c", "502"), EXPECTED_VERBOSE_PREAMBLE + "Pool Light: On")


@pytest.mark.asyncio
async def test_get_current_temp(MockProtocolAdapter, capsys):
    async with MockProtocolAdapter:
        with patch(
            "screenlogicpy.cli.async_discover", return_value=[FAKE_CONNECT_INFO]
        ):
            test_input = [
                (("get", "current-temp", "0"), "56"),
                (("get", "t", "spa"), "97"),
            ]

            for args, expected in test_input:
                result = await cli(args)
                std = capsys.readouterr()
                assert std.out.strip() == expected
                assert result == 0

    # MockCLI(("get", "current-temp", "0"), "56")

    # MockCLI(("get", "t", "spa"), "97")


@pytest.mark.asyncio
async def test_get_heat_mode(MockProtocolAdapter, capsys):
    async with MockProtocolAdapter:
        with patch(
            "screenlogicpy.cli.async_discover", return_value=[FAKE_CONNECT_INFO]
        ):
            test_input = [
                (("get", "heat-mode", "pool"), "0"),
                (("get", "hm", "1"), "3"),
            ]

            for args, expected in test_input:
                result = await cli(args)
                std = capsys.readouterr()
                assert std.out.strip() == expected
                assert result == 0

    # MockCLI(("get", "heat-mode", "pool"), "0")

    # MockCLI(("get", "hm", "1"), "3")


@pytest.mark.asyncio
async def test_get_heat_temp(MockProtocolAdapter, capsys):
    async with MockProtocolAdapter:
        with patch(
            "screenlogicpy.cli.async_discover", return_value=[FAKE_CONNECT_INFO]
        ):
            test_input = [
                (("get", "heat-temp", "0"), "86"),
                (("get", "ht", "spa"), "97"),
            ]

            for args, expected in test_input:
                result = await cli(args)
                std = capsys.readouterr()
                assert std.out.strip() == expected
                assert result == 0

    # MockCLI(("get", "heat-temp", "0"), "86")

    # MockCLI(("get", "ht", "spa"), "97")


@pytest.mark.asyncio
async def test_get_heat_state(MockProtocolAdapter, capsys):
    async with MockProtocolAdapter:
        with patch(
            "screenlogicpy.cli.async_discover", return_value=[FAKE_CONNECT_INFO]
        ):
            test_input = [
                (("get", "heat-state", "0"), "0"),
                (("get", "hs", "spa"), "0"),
            ]

            for args, expected in test_input:
                result = await cli(args)
                std = capsys.readouterr()
                assert std.out.strip() == expected
                assert result == 0

    # MockCLI(("get", "heat-state", "0"), "0")

    # MockCLI(("get", "hs", "spa"), "0")


@pytest.mark.asyncio
async def test_get_json(MockProtocolAdapter, capsys):
    async with MockProtocolAdapter:
        with patch(
            "screenlogicpy.cli.async_discover", return_value=[FAKE_CONNECT_INFO]
        ):
            test_input = [
                (("get", "json"), json.dumps(EXPECTED_COMPLETE_DATA, indent=2)),
            ]

            for args, expected in test_input:
                result = await cli(args)
                std = capsys.readouterr()
                assert std.out.strip() == expected
                assert result == 0

    # MockCLI(("get", "json"), json.dumps(EXPECTED_COMPLETE_DATA, indent=2))


@pytest.mark.asyncio
async def test_set_circuit(MockProtocolAdapter, capsys):
    async with MockProtocolAdapter:
        with patch(
            "screenlogicpy.cli.async_discover", return_value=[FAKE_CONNECT_INFO]
        ):
            test_input = [
                (("set", "circuit", "500", "off"), "0"),
                (
                    ("-v", "set", "circuit", "502", "1"),
                    EXPECTED_VERBOSE_PREAMBLE + "Pool Light: On",
                ),
            ]

            for args, expected in test_input:
                result = await cli(args)
                std = capsys.readouterr()
                assert std.out.strip() == expected
                assert result == 0

    # MockCLI(("set", "circuit", "500", "off"), "0")
    # MockCLI(
    #    ("-v", "set", "circuit", "502", "1"),
    #    EXPECTED_VERBOSE_PREAMBLE + "Pool Light: On",
    # )


@pytest.mark.asyncio
async def test_set_heat_mode(MockProtocolAdapter, capsys):
    async with MockProtocolAdapter:
        with patch(
            "screenlogicpy.cli.async_discover", return_value=[FAKE_CONNECT_INFO]
        ):
            test_input = [
                (("set", "heat-mode", "pool", "0"), "0"),
                (
                    ("-v", "set", "hm", "1", "heater"),
                    EXPECTED_VERBOSE_PREAMBLE + "Spa Heat Mode: Heater",
                ),
            ]

            for args, expected in test_input:
                result = await cli(args)
                std = capsys.readouterr()
                assert std.out.strip() == expected
                assert result == 0

    # MockCLI(("set", "heat-mode", "pool", "0"), "0")

    # MockCLI(
    #    ("-v", "set", "hm", "1", "heater"),
    #    EXPECTED_VERBOSE_PREAMBLE + "Spa Heat Mode: Heater",
    # )


@pytest.mark.asyncio
async def test_set_heat_temp(MockProtocolAdapter, capsys):
    async with MockProtocolAdapter:
        with patch(
            "screenlogicpy.cli.async_discover", return_value=[FAKE_CONNECT_INFO]
        ):
            test_input = [
                (("set", "heat-temp", "pool", "86"), "86"),
                (
                    ("-v", "set", "ht", "1", "97"),
                    EXPECTED_VERBOSE_PREAMBLE + "Spa Heat Set Point: 97",
                ),
            ]

            for args, expected in test_input:
                result = await cli(args)
                std = capsys.readouterr()
                assert std.out.strip() == expected
                assert result == 0

    # MockCLI(("set", "heat-temp", "pool", "86"), "86")

    # MockCLI(
    #    ("-v", "set", "ht", "1", "97"),
    #    EXPECTED_VERBOSE_PREAMBLE + "Spa Heat Set Point: 97",
    # )


@pytest.mark.asyncio
async def test_set_color_lights(MockProtocolAdapter, capsys):
    async with MockProtocolAdapter:
        with patch(
            "screenlogicpy.cli.async_discover", return_value=[FAKE_CONNECT_INFO]
        ):
            test_input = [
                (("set", "color-lights", "romance"), "6"),
                (
                    ("-v", "set", "cl", "0"),
                    EXPECTED_VERBOSE_PREAMBLE + "Set color mode to All Off",
                ),
            ]

            for args, expected in test_input:
                result = await cli(args)
                std = capsys.readouterr()
                assert std.out.strip() == expected
                assert result == 0

    # MockCLI(("set", "color-lights", "romance"), "6")

    # MockCLI(
    #    ("-v", "set", "cl", "0"),
    #    EXPECTED_VERBOSE_PREAMBLE + "Set color mode to All Off",
    # )
