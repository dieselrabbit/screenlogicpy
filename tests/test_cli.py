import json
from unittest.mock import patch

import pytest
from screenlogicpy.cli import cli
from .const_data import (
    FAKE_GATEWAY_ADDRESS,
    FAKE_GATEWAY_NAME,
    FAKE_GATEWAY_PORT,
    FAKE_CONNECT_INFO,
    EXPECTED_COMPLETE_DATA,
    EXPECTED_DASHBOARD,
    EXPECTED_VERBOSE_PREAMBLE,
)


@pytest.mark.asyncio
async def test_cli_dashboard(MockProtocolAdapter, capsys):
    async with MockProtocolAdapter:
        with patch(
            "screenlogicpy.cli.async_discover", return_value=[FAKE_CONNECT_INFO]
        ):
            result = await cli(())
            std = capsys.readouterr()
            assert std.out.strip() == EXPECTED_DASHBOARD
            assert result == 0


@pytest.mark.asyncio
async def test_cli_discover(MockProtocolAdapter, capsys):
    async with MockProtocolAdapter:
        with patch(
            "screenlogicpy.cli.async_discover", return_value=[FAKE_CONNECT_INFO]
        ):
            test_input = [
                (
                    ("discover",),
                    f"{FAKE_GATEWAY_ADDRESS}:{FAKE_GATEWAY_PORT} '{FAKE_GATEWAY_NAME}'",
                ),
                (
                    ("-v", "discover"),
                    f"Discovered:\n'{FAKE_GATEWAY_NAME}' at {FAKE_GATEWAY_ADDRESS}:{FAKE_GATEWAY_PORT}",
                ),
            ]
            for args, expected in test_input:
                result = await cli(args)
                std = capsys.readouterr()
                assert std.out.strip() == expected
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


@pytest.mark.asyncio
async def test_set_scg(MockProtocolAdapter, capsys):
    async with MockProtocolAdapter:
        with patch(
            "screenlogicpy.cli.async_discover", return_value=[FAKE_CONNECT_INFO]
        ):
            test_input = [
                (("set", "salt-generator", "100", "20"), "50 0"),
                (
                    ("-v", "set", "scg", "20", "0"),
                    EXPECTED_VERBOSE_PREAMBLE + "Pool SCG Level: 50 Spa SCG Level: 0",
                ),
            ]

            for args, expected in test_input:
                result = await cli(args)
                std = capsys.readouterr()
                assert std.out.strip() == expected
                assert result == 0
