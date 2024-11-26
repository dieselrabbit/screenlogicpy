import asyncio
import pytest
from unittest.mock import MagicMock, Mock, NonCallableMock

from screenlogicpy.connection import ScreenLogicProtocol


@pytest.fixture
def mock_msg_rcvd_cb() -> Mock:
    return Mock(name="mock_message_received_callback")


@pytest.fixture
def mock_conn_lost_cb() -> Mock:
    return Mock(name="mock_connection_lost_callback")


@pytest.fixture
def mock_transport() -> Mock:
    return Mock(spec=asyncio.Transport, is_closing=Mock(return_value=False))


@pytest.fixture
@pytest.mark.asyncio
async def mock_connected_protocol(
    mock_msg_rcvd_cb, mock_conn_lost_cb, mock_transport
) -> ScreenLogicProtocol:
    protocol = ScreenLogicProtocol(
        asyncio.get_running_loop(), mock_msg_rcvd_cb, mock_conn_lost_cb
    )
    protocol.connection_made(mock_transport)
    return protocol


@pytest.fixture
def mock_protocol(mock_msg_rcvd_cb, mock_conn_lost_cb, mock_transport):
    return NonCallableMock(
        spec=ScreenLogicProtocol,
        _loop=asyncio.get_running_loop(),
        _transport=mock_transport,
        _message_reveived_callback=mock_msg_rcvd_cb,
        _connection_lost_cb=mock_conn_lost_cb,
    )
