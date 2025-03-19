import asyncio
from collections.abc import Callable
from glob import glob
import pytest_asyncio
import socket
import struct
from unittest.mock import DEFAULT, AsyncMock, MagicMock, patch

from screenlogicpy import ScreenLogicGateway, __version__ as sl_version
from screenlogicpy.cli import file_format
from screenlogicpy.client import ClientManager
from screenlogicpy.const.common import ScreenLogicError
from screenlogicpy.const.data import DEVICE, GROUP, VALUE
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


DEFAULT_RESPONSE = "slpy-0110_pool-52-build-7380-rel_easytouch2-8_32824.json"


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
async def MockDiscoveryAdapter(discovery_response: bytes):
    _udp_sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    _udp_sock.bind(("", DISCOVERY_PORT))

    transport, protocol = await asyncio.get_running_loop().create_datagram_endpoint(
        lambda: FakeUDPProtocolAdapter(discovery_response),
        sock=_udp_sock,
    )
    return protocol


@pytest_asyncio.fixture(name="mock_transport")
async def mock_connected_transport():
    with patch(
        "screenlogicpy.gateway.asyncio.Transport", spec=asyncio.Transport
    ) as transport_mock:
        transport_inst = transport_mock.return_value
        return transport_inst


@pytest_asyncio.fixture(name="mock_protocol")
async def mock_connected_protocol():
    with patch(
        "screenlogicpy.requests.protocol.ScreenLogicProtocol", spec=ScreenLogicProtocol
    ) as protocol_mock:
        protocol_inst = protocol_mock.return_value

        def mock_close_protocol(_):
            protocol_inst._connected.return_value = False

        protocol_inst._connected.return_value = True
        protocol_inst.async_close.side_effect = mock_close_protocol
        return protocol_inst


@pytest_asyncio.fixture(name="mock_client")
async def mock_attached_client():
    with patch("screenlogicpy.client.ClientManager", spec=ClientManager) as client_mock:
        client_inst = client_mock.return_value
        client_inst.is_client.return_value = True
        client_inst.async_unsubscribe_gateway.return_value = True
        return client_inst


@pytest_asyncio.fixture(name="mock_gateway")
async def mock_connected_gateway(
    mock_transport: asyncio.Transport,
    mock_protocol: ScreenLogicProtocol,
    mock_client: ClientManager,
    response_collection: ScreenLogicResponseCollection,
):
    last, data = deconstruct_response_collection(response_collection)
    data[DEVICE.ADAPTER][VALUE.CONNECTION] = {"ip": "127.0.0.1", "port": 6448}
    data[DEVICE.ADAPTER][GROUP.CONFIGURATION] = {
        "type": 2,
        "subtype": 12,
        "name": "Fake: 00-00-00",
        "mac": "00:00:00:00:00:00",
    }

    with (
        patch.object(ScreenLogicGateway, "_transport", mock_transport),
        patch.object(
            ScreenLogicGateway,
            "_protocol",
            mock_protocol,
        ),
        patch.dict("screenlogicpy.gateway.ScreenLogicGateway._data", data),
        patch.dict("screenlogicpy.gateway.ScreenLogicGateway._last", last),
    ):
        # mock_protocol_inst = mock_protocol.return_value
        # mock_protocol_inst.async_close = AsyncMock(side_effect=mock_close_protocol)
        gateway = ScreenLogicGateway()
        with patch.object(gateway, "_client_manager", mock_client):
            yield gateway
