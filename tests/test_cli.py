import json
import pytest
import pytest_asyncio
from unittest.mock import DEFAULT, MagicMock, mock_open, patch

from screenlogicpy import ScreenLogicGateway
from screenlogicpy.cli import cli
from screenlogicpy.data import ScreenLogicResponseCollection

from .const_data import (
    EXPECTED_DASHBOARD,
    EXPECTED_VERBOSE_PREAMBLE,
    FAKE_GATEWAY_ADDRESS,
    FAKE_GATEWAY_NAME,
    FAKE_GATEWAY_PORT,
    FAKE_CONNECT_INFO,
)


@pytest_asyncio.fixture()
async def PatchedGateway(
    mock_gateway: ScreenLogicGateway,
    response_collection: ScreenLogicResponseCollection
):
    with patch.multiple(
        ScreenLogicGateway, async_disconnect=DEFAULT, _async_connected_request=DEFAULT,
    ) as gateway, patch(
        "screenlogicpy.cli.async_discover", return_value=[FAKE_CONNECT_INFO]
    ):
        yield gateway


#@patch.multiple(ScreenLogicGateway, async_disconnect=DEFAULT, _async_connected_request=DEFAULT)
@pytest.mark.usefixtures("PatchedGateway")
class TestCLI:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "arguments, return_code, expected_output",
        [
            ("", 0, EXPECTED_DASHBOARD),
        ],
    )
    async def test_dashboard(
        self,
        capsys: pytest.CaptureFixture,
        arguments: str,
        return_code: int,
        expected_output: str,
    ):
        assert await cli(arguments.split()) == return_code
        assert capsys.readouterr().out.strip() == expected_output

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "arguments, return_code, expected_output",
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
    async def test_discover(
        self,
        capsys: pytest.CaptureFixture,
        arguments: str,
        return_code: int,
        expected_output: str,
    ):
        assert await cli(arguments.split()) == return_code
        assert capsys.readouterr().out.strip() == expected_output

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "arguments, return_code, expected_output",
        [
            ("get circuit 500", 0, "0"),
            ("get c 502", 0, "0"),
            ("get c 300", 4, "Invalid circuit number: 300"),
            (
                "-v get c 502",
                0,
                EXPECTED_VERBOSE_PREAMBLE + "Pool Light: Off",
            ),
            ("set circuit 500 off", 0, "0"),
            (
                "-v set circuit 502 1",
                0,
                EXPECTED_VERBOSE_PREAMBLE + "Pool Light: Off",
            ),
            ("set circuit 900 1", 4, "Invalid circuit number: 900"),
        ],
    )
    async def test_circuit(
        self,
        capsys: pytest.CaptureFixture,
        arguments: str,
        return_code: int,
        expected_output: str,
    ):
        assert await cli(arguments.split()) == return_code
        assert capsys.readouterr().out.strip() == expected_output

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "arguments, return_code, expected_output",
        [
            ("get current-temp 0", 0, "59"),
            ("get t spa", 0, "59"),
        ],
    )
    async def test_get_current_temp(
        self,
        capsys: pytest.CaptureFixture,
        arguments: str,
        return_code: int,
        expected_output: str,
    ):
        assert await cli(arguments.split()) == return_code
        assert capsys.readouterr().out.strip() == expected_output

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "arguments, return_code, expected_output",
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
    async def test_heat_mode(
        self,
        capsys: pytest.CaptureFixture,
        arguments: str,
        return_code: int,
        expected_output: str,
    ):
        assert await cli(arguments.split()) == return_code
        assert capsys.readouterr().out.strip() == expected_output

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "arguments, return_code, expected_output",
        [
            ("get heat-temp 0", 0, "83"),
            ("get ht spa", 0, "95"),
            ("set heat-temp pool 86", 0, "83"),
            (
                "-v set ht 1 97",
                0,
                EXPECTED_VERBOSE_PREAMBLE + "Spa Heat Set Point: 95",
            ),
        ],
    )
    async def test_heat_temp(
        self,
        capsys: pytest.CaptureFixture,
        arguments: str,
        return_code: int,
        expected_output: str,
    ):
        assert await cli(arguments.split()) == return_code
        assert capsys.readouterr().out.strip() == expected_output

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "arguments, return_code, expected_output",
        [
            ("get heat-state 0", 0, "0"),
            ("get hs spa", 0, "0"),
        ],
    )
    async def test_get_heat_state(
        self,
        capsys: pytest.CaptureFixture,
        arguments: str,
        return_code: int,
        expected_output: str,
    ):
        assert await cli(arguments.split()) == return_code
        assert capsys.readouterr().out.strip() == expected_output

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "arguments, return_code",
        [
            (
                "get json",
                0,
            ),
        ],
    )
    async def test_get_json(
        self,
        capsys: pytest.CaptureFixture,
        arguments: str,
        return_code: int,
        response_collection,
    ):
        assert await cli(arguments.split()) == return_code
        assert capsys.readouterr().out.strip() == json.dumps(
            response_collection.decoded_complete, indent=2
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "arguments, return_code, expected_output",
        [
            ("set color-lights romance", 0, "6"),
            (
                "-v set cl 0",
                0,
                EXPECTED_VERBOSE_PREAMBLE + "Set color mode to All Off",
            ),
        ],
    )
    async def test_set_color_lights(
        self,
        capsys: pytest.CaptureFixture,
        arguments: str,
        return_code: int,
        expected_output: str,
    ):
        assert await cli(arguments.split()) == return_code
        assert capsys.readouterr().out.strip() == expected_output

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "arguments, return_code, expected_output",
        [
            ("set salt-generator --pool 100 --spa 20", 0, "0 0"),
            (
                "-v set scg -p 20 -s 0",
                0,
                EXPECTED_VERBOSE_PREAMBLE
                + "Pool Chlorinator Setpoint: 0 Spa Chlorinator Setpoint: 0",
            ),
            ("set scg -p 50", 0, "0"),
            ("set scg -s 20", 0, "0"),
            ("set scg", 65, "No new chlorinator values. Nothing to do."),
            ("set super-chlorinate --state 1 --time 24", 0, "6"),
            ("set sc -s 0", 0, ""),
            ("set sc -t 12", 0, "6"),
        ],
    )
    async def test_set_scg(
        self,
        capsys: pytest.CaptureFixture,
        arguments: str,
        return_code: int,
        expected_output: str,
    ):
        assert await cli(arguments.split()) == return_code
        assert capsys.readouterr().out.strip() == expected_output

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "arguments, return_code, expected_output",
        [
            ("set chemistry-setpoint --ph 7.5 --orp 700", 0, "7.6 720"),
            (
                "-v set cs -p 7.6 -o 650",
                0,
                EXPECTED_VERBOSE_PREAMBLE + "pH Setpoint: 7.6 ORP Setpoint: 720",
            ),
            ("set cs -p 7.2", 0, "7.6"),
            ("set cs -o 650", 0, "720"),
            ("set cs", 129, "No new chemistry values. Nothing to do."),
            (
                "set chemistry-value --calcium-hardness 351 --total-alkalinity 80 --cyanuric-acid 45 --total-dissolved-solids 1000",
                0,
                "800 45 45 1000",
            ),
        ],
    )
    async def test_set_chemistry(
        self,
        capsys: pytest.CaptureFixture,
        arguments: str,
        return_code: int,
        expected_output: str,
    ):
        assert await cli(arguments.split()) == return_code
        assert capsys.readouterr().out.strip() == expected_output

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "arguments, return_code, expected_output",
        [
            ("get date-time", 0, "Mon Nov 20 14:06:09 2023"),
            (
                "-v get dt -f %I:%M%p",
                0,
                EXPECTED_VERBOSE_PREAMBLE + "02:06PM",
            ),
            ("get auto-dst", 0, "1"),
            ("get dst", 0, "1"),
            (
                "set date-time --date-time 2023-11-12T16:24:00",
                0,
                "Controller time now: Mon Nov 20 14:06:09 2023",
            ),
            (
                "set date-time",
                0,
                "Controller time now: Mon Nov 20 14:06:09 2023",
            ),
        ],
    )
    async def test_date_time(
        self,
        capsys: pytest.CaptureFixture,
        arguments: str,
        return_code: int,
        expected_output: str,
    ):
        assert await cli(arguments.split()) == return_code
        assert capsys.readouterr().out.strip() == expected_output

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "arguments, return_code, expected_output",
        [
            ("export", 0, ""),
        ],
    )
    async def test_export_data_collection(
        self,
        capsys: pytest.CaptureFixture,
        arguments: str,
        return_code: int,
        expected_output: str,
    ):
        written: str = ""

        def write(data):
            nonlocal written
            written += data

        mo: MagicMock = mock_open()
        handle = mo()
        handle.write.side_effect = write
        with patch("screenlogicpy.data.open", mo), patch(
            "screenlogicpy.cli.ScreenLogicGateway.async_update"
        ):
            assert await cli(arguments.split()) == return_code
        mo.assert_called_with(
            "slpy-0110_pool-52-build-7380-rel_easytouch2-8_32824.json",
            "w",
            encoding="utf-8",
        )

        assert written
