import asyncio
from collections.abc import Callable
from glob import glob
import pytest_asyncio
import socket
import struct
from unittest.mock import DEFAULT, MagicMock, patch

from screenlogicpy import ScreenLogicGateway, __version__ as sl_version
from screenlogicpy.cli import file_format
from screenlogicpy.const.common import ScreenLogicError
from screenlogicpy.data import (
    ScreenLogicResponseCollection,
    deconstruct_response_collection,
    import_response_collection,
)
from screenlogicpy.discovery import DISCOVERY_PORT
from screenlogicpy.requests.protocol import ScreenLogicProtocol

from .adapter import FakeTCPProtocolAdapter, FakeUDPProtocolAdapter
from .const_data import (
    FAKE_GATEWAY_ADDRESS,
    FAKE_GATEWAY_CHK,
    FAKE_GATEWAY_PORT,
    FAKE_CONNECT_INFO,
    FAKE_GATEWAY_MAC,
    FAKE_GATEWAY_NAME,
    FAKE_GATEWAY_SUB_TYPE,
    FAKE_GATEWAY_TYPE,
)


DEFAULT_RESPONSE = "slpy-0100_pool-52-build-7380-rel_easytouch2-8_32824.json"


def load_response_collections(filenames: list[str] | None = None):
    dir = "tests/data/"
    file_filter = f"slpy-{file_format(sl_version)}*.json"
    files = filenames or glob(file_filter, root_dir=dir)
    response_collections = []
    for file in files:
        response_collections.append((file, import_response_collection(f"{dir}{file}")))
    if not response_collections:
        raise ScreenLogicError(
            f"No response collections imported from {dir}{file_filter}"
        )
    return response_collections


@pytest_asyncio.fixture()
async def response_collection():
    return load_response_collections([DEFAULT_RESPONSE])[0][1]


@pytest_asyncio.fixture()
async def MockProtocolAdapter(
    response_collection: ScreenLogicResponseCollection,
):
    server = await asyncio.get_running_loop().create_server(
        lambda: FakeTCPProtocolAdapter(response_collection),
        FAKE_GATEWAY_ADDRESS,
        FAKE_GATEWAY_PORT,
        reuse_address=True,
    )

    async with server:
        yield server
        server.close()


@pytest_asyncio.fixture
async def discovery_response() -> bytes:
    return struct.pack(
        f"<I4BH2B{len(FAKE_GATEWAY_NAME)}s",
        FAKE_GATEWAY_CHK,
        *[int(part) for part in FAKE_GATEWAY_ADDRESS.split(".")],
        FAKE_GATEWAY_PORT,
        FAKE_GATEWAY_TYPE,
        FAKE_GATEWAY_SUB_TYPE,
        bytes(FAKE_GATEWAY_NAME, "UTF-8"),
    )


@pytest_asyncio.fixture()
async def MockDiscoveryAdapter(
    discovery_response: bytes
):
    _udp_sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    _udp_sock.bind(("", DISCOVERY_PORT))

    transport, protocol = await asyncio.get_running_loop().create_datagram_endpoint(
        lambda: FakeUDPProtocolAdapter(discovery_response),
        sock=_udp_sock,
    )
    return protocol


async def stub_async_connect(
    resp_col: ScreenLogicResponseCollection,
    self: ScreenLogicGateway,
    ip: str = None,
    port: int = None,
    gtype: int = None,
    gsubtype: int = None,
    name: str = FAKE_GATEWAY_NAME,
    connection_closed_callback: Callable = None,
) -> bool:
    """Initialize minimum attributes needed for tests."""
    if self.is_connected:
        return True

    self._ip = ip
    self._port = port
    self._type = gtype
    self._subtype = gsubtype
    self._name = name
    self._custom_connection_closed_callback = connection_closed_callback
    self._mac = FAKE_GATEWAY_MAC
    self._protocol = ScreenLogicProtocol(asyncio.get_running_loop())
    self._protocol.connection_made(MagicMock(spec=asyncio.Transport))
    self._last, self._data = deconstruct_response_collection(resp_col)

    return True


@pytest_asyncio.fixture()
async def MockConnectedGateway(
    response_collection: ScreenLogicResponseCollection
):
    with patch.multiple(
        ScreenLogicGateway,
        async_connect=lambda *args, **kwargs: stub_async_connect(
            response_collection, *args, **kwargs
        ),
        async_disconnect=DEFAULT,
        # get_debug=lambda self: {},
    ):
        gateway = ScreenLogicGateway()
        await gateway.async_connect(**FAKE_CONNECT_INFO)
        assert gateway.is_connected
        yield gateway
