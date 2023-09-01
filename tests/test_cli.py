import json
import pytest
from unittest.mock import patch

from screenlogicpy.cli import cli
from .const_data import (
    EXPECTED_DASHBOARD,
    EXPECTED_VERBOSE_PREAMBLE,
    FAKE_GATEWAY_ADDRESS,
    FAKE_GATEWAY_NAME,
    FAKE_GATEWAY_PORT,
    FAKE_CONNECT_INFO,
)
from .data_sets import TESTING_DATA_COLLECTION as TDC


async def run_cli_test(
    protocol_adapter, system_out, arguments, return_code, expected_output
):
    async with protocol_adapter:
        with patch(
            "screenlogicpy.cli.async_discover", return_value=[FAKE_CONNECT_INFO]
        ):
            assert await cli(arguments.split()) == return_code
            assert system_out.readouterr().out.strip() == expected_output


@pytest.mark.asyncio
async def test_dashboard(MockProtocolAdapter, capsys):
    await run_cli_test(MockProtocolAdapter, capsys, "", 0, EXPECTED_DASHBOARD)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "args, ret, expected",
    [
        (
            "discover",
            0,
            f"{FAKE_GATEWAY_ADDRESS}:{FAKE_GATEWAY_PORT} '{FAKE_GATEWAY_NAME}'",
        ),
        (
            "-v discover",
            0,
            f"Discovered:\n'{FAKE_GATEWAY_NAME}' at {FAKE_GATEWAY_ADDRESS}:{FAKE_GATEWAY_PORT}",
        ),
    ],
)
async def test_discover(MockProtocolAdapter, capsys, args, ret, expected):
    await run_cli_test(MockProtocolAdapter, capsys, args, ret, expected)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "args, ret, expected",
    [
        ("get circuit 500", 0, "0"),
        ("get c 502", 0, "1"),
        ("get c 300", 4, "Invalid circuit number: 300"),
        (
            "-v get c 502",
            0,
            EXPECTED_VERBOSE_PREAMBLE + "Pool Light: On",
        ),
        ("set circuit 500 off", 0, "0"),
        (
            "-v set circuit 502 1",
            0,
            EXPECTED_VERBOSE_PREAMBLE + "Pool Light: On",
        ),
        ("set circuit 900 1", 4, "Invalid circuit number: 900"),
    ],
)
async def test_circuit(MockProtocolAdapter, capsys, args, ret, expected):
    await run_cli_test(MockProtocolAdapter, capsys, args, ret, expected)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "args, ret, expected",
    [
        ("get current-temp 0", 0, "56"),
        ("get t spa", 0, "97"),
    ],
)
async def test_get_current_temp(MockProtocolAdapter, capsys, args, ret, expected):
    await run_cli_test(MockProtocolAdapter, capsys, args, ret, expected)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "args, ret, expected",
    [
        ("get heat-mode pool", 0, "0"),
        ("get hm 1", 0, "3"),
        ("set heat-mode pool 0", 0, "0"),
        (
            "-v set hm 1 heater",
            0,
            EXPECTED_VERBOSE_PREAMBLE + "Spa Heat Mode: Heater",
        ),
    ],
)
async def test_heat_mode(MockProtocolAdapter, capsys, args, ret, expected):
    await run_cli_test(MockProtocolAdapter, capsys, args, ret, expected)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "args, ret, expected",
    [
        ("get heat-temp 0", 0, "86"),
        ("get ht spa", 0, "97"),
        ("set heat-temp pool 86", 0, "86"),
        (
            "-v set ht 1 97",
            0,
            EXPECTED_VERBOSE_PREAMBLE + "Spa Heat Set Point: 97",
        ),
    ],
)
async def test_heat_temp(MockProtocolAdapter, capsys, args, ret, expected):
    await run_cli_test(MockProtocolAdapter, capsys, args, ret, expected)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "args, ret, expected",
    [
        ("get heat-state 0", 0, "0"),
        ("get hs spa", 0, "0"),
    ],
)
async def test_get_heat_state(MockProtocolAdapter, capsys, args, ret, expected):
    await run_cli_test(MockProtocolAdapter, capsys, args, ret, expected)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "args, ret, expected",
    [
        (
            "get json",
            0,
            json.dumps(TDC.decoded_complete, indent=2),
        ),
    ],
)
async def test_get_json(MockProtocolAdapter, capsys, args, ret, expected):
    await run_cli_test(MockProtocolAdapter, capsys, args, ret, expected)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "args, ret, expected",
    [
        ("set color-lights romance", 0, "6"),
        (
            "-v set cl 0",
            0,
            EXPECTED_VERBOSE_PREAMBLE + "Set color mode to All Off",
        ),
    ],
)
async def test_set_color_lights(MockProtocolAdapter, capsys, args, ret, expected):
    await run_cli_test(MockProtocolAdapter, capsys, args, ret, expected)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "args, ret, expected",
    [
        ("set salt-generator 100 20", 0, "50 0"),
        (
            "-v set scg 20 0",
            0,
            EXPECTED_VERBOSE_PREAMBLE
            + "Pool Chlorinator Setpoint: 50 Spa Chlorinator Setpoint: 0",
        ),
        ("set scg * *", 65, "No new Chlorinator values. Nothing to do."),
        ("set scg f *", 66, "Invalid Chlorinator value"),
    ],
)
async def test_set_scg(MockProtocolAdapter, capsys, args, ret, expected):
    await run_cli_test(MockProtocolAdapter, capsys, args, ret, expected)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "args, ret, expected",
    [
        ("set chem-data 7.5 700", 0, "7.5 700"),
        (
            "-v set ch 7.6 650",
            0,
            EXPECTED_VERBOSE_PREAMBLE + "pH Setpoint: 7.5 ORP Setpoint: 700",
        ),
        ("set ch * *", 129, "No new setpoint values. Nothing to do."),
        ("set ch f *", 130, "Invalid Chemistry Setpoint value"),
    ],
)
async def test_set_chemistry(MockProtocolAdapter, capsys, args, ret, expected):
    await run_cli_test(MockProtocolAdapter, capsys, args, ret, expected)
