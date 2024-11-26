import asyncio
import struct
import pytest
from unittest.mock import AsyncMock, MagicMock, NonCallableMagicMock, patch

from screenlogicpy.connection import (
    COM_KEEPALIVE,
    COM_TIMEOUT,
    COM_RETRY_WAIT,
    COM_MAX_RETRIES,
    Connection,
    GatewayInfo,
    ScreenLogicProtocol,
    Transaction,
    TransactionIDSingleton,
    connect,
    prime,
    challenge,
    login,
)
from screenlogicpy.devices import Controller
from screenlogicpy.exceptions import *
from screenlogicpy.messages import (
    BaseResponse,
    ChallengeResponse,
    LocalLoginResponse,
    LocalLoginRequest,
    MessageCode,
    Payload,
    GetPoolConfigResponse,
    PoolStatusResponse,
    PoolStatusChanged,
    encode_string,
    from_bytes,
)
from screenlogicpy.messages.login import CONNECT_PING

GW_ADDR = "111.222.33.4"
GW_PORT = 80
GW_MAC = "AA:BB:CC:DD:EE"


LOCALLOGINREQUEST_BYTES = (
    LocalLoginRequest().payload.bytes
)  # b"\\\x01\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00Android\x00\x10\x00\x00\x000000000000000000\x00\x02\x00\x00\x00"


def complete_fut(fut, response) -> asyncio.Future:
    fut.set_result(response)
    return fut


def timeout_fut(fut, response) -> asyncio.Future:
    return fut


def cancel_fut(fut, response) -> asyncio.Future:
    fut.cancel()
    return fut


def except_fut(fut, exception: ScreenLogicException) -> asyncio.Future:
    fut.set_exception(exception)
    return fut


# **************************************
# *          Protocol Tests            *
# **************************************


@pytest.mark.asyncio
async def test_protocol():
    mock_msg_rcv_cb = MagicMock()
    mock_ctn_lst_cb = MagicMock()

    # Connect
    protocol = ScreenLogicProtocol(
        asyncio.get_running_loop(), mock_msg_rcv_cb, mock_ctn_lst_cb
    )

    def mock_transport_close():
        protocol.connection_lost(None)

    mock_transport = NonCallableMagicMock(
        spec=asyncio.Transport,
        is_closing=MagicMock(return_value=False),
        close=MagicMock(side_effect=mock_transport_close),
    )

    protocol.connection_made(mock_transport)
    assert protocol.is_connected

    # Send request
    r_id = 2719
    request = LocalLoginRequest(r_id)
    transaction_fut = protocol.await_send_message(request)
    assert len(protocol._active_requests) == 1
    assert protocol._active_requests.get(r_id) == transaction_fut
    mock_transport.write.assert_called()

    # Receive reesponse
    data = LocalLoginResponse(id=r_id).to_bytes()
    protocol.data_received(data)
    assert transaction_fut.done()
    response: LocalLoginResponse = transaction_fut.result()
    assert response.id == r_id
    assert response.code == MessageCode.LOCAL_LOGIN + 1
    assert response.payload.bytes == b""
    assert len(protocol._active_requests) == 0
    mock_msg_rcv_cb.assert_not_called()

    # Receive update
    data = PoolStatusChanged().to_bytes()
    protocol.data_received(data)
    mock_msg_rcv_cb.assert_called_once()

    await protocol.close()
    mock_ctn_lst_cb.assert_called_once_with(True)


@pytest.mark.asyncio
async def test_protocol_multiple_messages():
    config_bytes = (
        b"\x02\x00\xf50H\x02\x00\x00d\x00\x00\x00(h(h\x00\r\x00\x008\x80\x00\x00"
        b"\x0e\x00\x00\x00Water Features\x00\x00\x0b\x00\x00\x00\xf4\x01\x00\x00"
        b"\x03\x00\x00\x00Spa\x00G\x01\x01\x01\x00\x00\x00\x01\xd0\x02\x00\x00"
        b"\xf5\x01\x00\x00\t\x00\x00\x00Waterfall\x00\x00\x00U\x00\x02\x00"
        b"\x00\x00\x00\x02\xd0\x02\x00\x00\xf6\x01\x00\x00\n\x00\x00\x00Pool Lig"
        b"ht\x00\x00>\x10\x03\x00\x02\x00\x02\x03\xd0\x02\x00\x00\xf7\x01\x00\x00"
        b"\t\x00\x00\x00Spa Light\x00\x00\x00I\x10\x03\x00\x06\x01\n\x04"
        b"\xd0\x02\x00\x00\xf8\x01\x00\x00\x07\x00\x00\x00Cleaner\x00\x15\x05\x02\x00"
        b"\x00\x00\x00\x05\xf0\x00\x00\x00\xf9\x01\x00\x00\x08\x00\x00\x00Pool Low"
        b"?\x02\x00\x01\x00\x00\x00\x06\xd0\x02\x00\x00\xfa\x01\x00\x00\n\x00\x00\x00"
        b"Yard Light\x00\x00[\x07\x04\x00\x00\x00\x00\x07\xd0\x02\x00\x00"
        b"\xfb\x01\x00\x00\x07\x00\x00\x00Cameras\x00e\x00\x02\x00\x00\x00\x00\x08"
        b"T\x06\x00\x00\xfc\x01\x00\x00\t\x00\x00\x00Pool High\x00\x00\x00"
        b"=\x00\x02\x00\x00\x00\x00\t\xd0\x02\x00\x00\xfe\x01\x00\x00\x08\x00\x00\x00"
        b"SpillwayN\x0e\x02\x00\x00\x00\x00\x0b\xd0\x02\x00\x00\xff\x01\x00\x00"
        b"\t\x00\x00\x00Pool High\x00\x00\x00=\x00\x05\x00\x00\x00\x00\x0c"
        b"\xd0\x02\x00\x00\x08\x00\x00\x00\x05\x00\x00\x00White\x00\x00\x00"
        b"\xff\x00\x00\x00\xff\x00\x00\x00\xff\x00\x00\x00\x0b\x00\x00\x00Light Gr"
        b"een\x00\xa0\x00\x00\x00\xff\x00\x00\x00\xa0\x00\x00\x00\x05\x00\x00\x00Gree"
        b"n\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00P\x00\x00\x00\x04\x00\x00\x00"
        b"Cyan\x00\x00\x00\x00\xff\x00\x00\x00\xc8\x00\x00\x00\x04\x00\x00\x00Blue"
        b"d\x00\x00\x00\x8c\x00\x00\x00\xff\x00\x00\x00\x08\x00\x00\x00Lavender"
        b"\xe6\x00\x00\x00\x82\x00\x00\x00\xff\x00\x00\x00\x07\x00\x00\x00Magenta\x00"
        b"\xff\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\r\x00\x00\x00Light Magent"
        b"a\x00\x00\x00\xff\x00\x00\x00\xb4\x00\x00\x00\xd2\x00\x00\x00FB\x00\x00"
        b"\x00\x00\x00\x00\x7f\x00\x00\x00\x01\x00\x00\x00"
    )

    status_bytes = (
        b"\x03\x00\xef0\xe8\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00?\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x007\x00\x00\x00\x00\x00\x00"
        b"\x00K\x00\x00\x00d\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00Z\x00\x00"
        b"\x00\x00\x00\x00\x00Z\x00\x00\x00?\x00\x00\x00\x03\x00\x00\x00\x0b\x00\x00"
        b"\x00\xf4\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xf5\x01\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\xf6\x01\x00\x00\x00\x00\x00\x00\x02\x00\x02"
        b"\x00\xf7\x01\x00\x00\x00\x00\x00\x00\x06\x01\n\x00\xf8\x01\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\xf9\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\xfa\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xfb\x01\x00\x00\x01\x00"
        b"\x00\x00\x00\x00\x00\x00\xfc\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\xfe\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\x01\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x9a\x02\x00\x00\xfe\x02\x00\x00\x9d\xff\xff\xff"
        b"\x00\x00\x00\x00\x07\x00\x00\x00\x07\x00\x00\x00\x01\x00\x00\x00"
    )
    mock_msg_rcv_cb = MagicMock()
    protocol = ScreenLogicProtocol(asyncio.get_running_loop(), mock_msg_rcv_cb)
    mock_transport = NonCallableMagicMock(spec=asyncio.Transport)

    protocol.connection_made(mock_transport)
    protocol.data_received(config_bytes + status_bytes)

    mock_msg_rcv_cb.assert_called()
    assert isinstance(mock_msg_rcv_cb.call_args_list[0].args[0], GetPoolConfigResponse)
    assert isinstance(mock_msg_rcv_cb.call_args_list[1].args[0], PoolStatusResponse)


@pytest.mark.asyncio
async def test_protocol_split_message():
    config_bytes = (
        b"\x00\x00\xf50\x18\x03\x00\x00d\x00\x00\x00(h(h\x00\r\x00\x00\x1c\x00\x00"
        b"\x00\x0e\x00\x00\x00Water Features\x00\x00\x12\x00\x00\x00\xf4\x01\x00\x00"
        b"\x03\x00\x00\x00Spa\x00G\x01\x01\x01\x00\x00\x00\x01\xd0\x02\x00\x00\xf5"
        b"\x01\x00\x00\n\x00\x00\x00Air Blower\x00\x00\x01\x00\x02\x00\x00\x00\x00\x02"
        b"\xd0\x02\x00\x00\xf6\x01\x00\x00\x06\x00\x00\x00Lights\x00\x00.\x10\x03\x00"
        b"\x00\x00\n\x03\xd0\x02\x00\x00\xf7\x01\x00\x00\x0b\x00\x00\x00BUBBLERS   "
        b"\x00e\r\x02\x00\x00\x00\x00\x04\xd0\x02\x00\x00\xf8\x01\x00\x00\x05\x00\x00"
        b"\x00Aux 4\x00\x00\x00\x05\x00\x02\x00\x00\x00\x00\x05\xd0\x02\x00\x00\xf9\x01"
        b"\x00\x00\x04\x00\x00\x00Pool<\x02\x00\x01\x00\x00\x00\x06\xd0\x02\x00\x00"
        b"\xfa\x01\x00\x00\x05\x00\x00\x00Aux 5\x00\x00\x00\x06\x00\x02\x00\x00\x00"
        b"\x00\x07\xd0\x02\x00\x00\xfb\x01\x00\x00\x05\x00\x00\x00Aux 6\x00\x00\x00"
        b"\x07\x00\x02\x00\x00\x00\x00\x08\xd0\x02\x00\x00\xfc\x01\x00\x00\x05\x00"
        b"\x00\x00Aux 7\x00\x00\x00\x08\x00\x02\x00\x00\x00\x00\t\xd0\x02\x00\x00\xfe"
        b"\x01\x00\x00\t\x00\x00\x00Feature 1\x00\x00\x00]\x00\x02\x00\x00\x00\x00\x0b"
        b"\xd0\x02\x00\x00\xff\x01\x00\x00\t\x00\x00\x00Feature 2\x00\x00\x00^\x00\x02"
        b"\x00\x00\x00\x00\x0c\xd0\x02\x00\x00\x00\x02\x00\x00\t\x00\x00\x00Feature 3"
        b"\x00\x00\x00_\x00\x02\x00\x00\x00\x00\r\xd0\x02\x00\x00\x01\x02\x00\x00\t"
        b"\x00\x00\x00Feature 4\x00\x00\x00`\x00\x02\x00\x00\x00\x00\x0e\xd0\x02\x00"
        b"\x00\x02\x02\x00\x00\t\x00\x00\x00Feature 5\x00\x00\x00a\x00\x02\x00\x00\x00"
        b"\x00\x0f\xd0\x02\x00\x00\x03\x02\x00\x00\t\x00\x00\x00Feature 6\x00\x00\x00b"
        b"\x00\x02\x00\x00\x00\x00\x10\xd0\x02\x00\x00\x04\x02\x00\x00\t\x00\x00\x00"
        b"Feature 7\x00\x00\x00c\x00\x02\x00\x00\x00\x00\x11\xd0\x02\x00\x00\x05\x02"
        b"\x00\x00\t\x00\x00\x00Feature 8\x00\x00\x00d\x00\x02\x00\x00\x00\x00\x12\xd0"
        b"\x02\x00\x00\x07\x02\x00\x00\x05\x00\x00\x00AuxEx\x00\x00\x00\\\x00\x02\x00"
        b"\x00\x00\x00\x14\xd0\x02\x00\x00\x08\x00\x00\x00\x05\x00\x00\x00White\x00"
        b"\x00\x00\xff\x00\x00\x00\xff\x00\x00\x00\xff\x00\x00\x00\x0b\x00\x00\x00"
        b"Light Green\x00\xa0\x00\x00\x00\xff\x00\x00\x00\xa0\x00\x00\x00\x05\x00\x00"
        b"\x00Green\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00P\x00\x00\x00\x04\x00"
        b"\x00\x00Cyan\x00\x00\x00\x00\xff\x00\x00\x00\xc8\x00\x00\x00\x04\x00\x00"
        b"\x00Blued\x00\x00\x00\x8c\x00\x00\x00\xff\x00\x00\x00\x08\x00\x00\x00Laven"
        b"der\xe6\x00\x00\x00\x82\x00\x00\x00\xff\x00\x00\x00\x07\x00\x00\x00Magenta"
        b"\x00\xff\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\r\x00\x00\x00Light Ma"
        b"genta\x00\x00\x00\xff\x00\x00\x00\xb4\x00\x00\x00\xd2\x00\x00\x00F\x00\x00"
        b"\x00\x00\x00\x00\x00\x7f\x00\x00\x00\x01\x00\x00\x00"
    )
    data1 = config_bytes[:512]
    data2 = config_bytes[512:]
    controller = Controller()

    def msg_rcv_cb(msg: BaseResponse):
        msg.decode(controller)

    protocol = ScreenLogicProtocol(asyncio.get_running_loop(), msg_rcv_cb)
    mock_transport = NonCallableMagicMock(spec=asyncio.Transport)

    protocol.connection_made(mock_transport)
    protocol.data_received(data1)
    protocol.data_received(data2)
    assert len(controller.circuits) == 18


@pytest.mark.asyncio
async def test_connection_lost():
    mock_ctn_lst_cb = MagicMock()
    protocol = ScreenLogicProtocol(
        asyncio.get_running_loop(), connection_lost_cb=mock_ctn_lst_cb
    )
    mock_transport = NonCallableMagicMock(
        spec=asyncio.Transport, is_closing=MagicMock(return_value=False)
    )
    protocol.connection_made(mock_transport)
    req_fut = protocol.await_send_message(LocalLoginRequest())
    assert len(protocol._active_requests) == 1

    protocol.connection_lost(ScreenLogicError("Connection Lost"))
    assert req_fut.cancelled()
    assert len(protocol._active_requests) == 0


# **************************************
# *        Transaction Tests           *
# **************************************


def test_transaction_singleton():
    MAX_IDS = 32767
    # Test that the counter increments through MAX_IDS
    for i in range(MAX_IDS):
        id = TransactionIDSingleton().next()
        assert id == i
    # Test that the counter cycled back to 0 after hitting MAX_IDS
    assert TransactionIDSingleton().next() == 0


@pytest.mark.parametrize(
    "responsecode, expected, error, message",
    [
        (
            MessageCode.LOGIN_REJECTED,
            False,
            ScreenLogicLoginError,
            (
                f"Login Rejected for request code: {MessageCode.LOCAL_LOGIN},"
                f" request: {LOCALLOGINREQUEST_BYTES}"
            ),
        ),
        (
            MessageCode.INVALID_REQUEST,
            False,
            ScreenLogicRequestError,
            (
                f"Invalid Request for request code: {MessageCode.LOCAL_LOGIN},"
                f" request: {LOCALLOGINREQUEST_BYTES}"
            ),
        ),
        (
            MessageCode.BAD_PARAMETER,
            False,
            ScreenLogicRequestError,
            (
                f"Bad Parameter for request code: {MessageCode.LOCAL_LOGIN},"
                f" request: {LOCALLOGINREQUEST_BYTES}"
            ),
        ),
        (
            0,
            False,
            ScreenLogicResponseError,
            (
                "Unexpected response code '0'"
                f" for request code: {MessageCode.LOCAL_LOGIN},"
                f" request: {LOCALLOGINREQUEST_BYTES}"
            ),
        ),
        (
            MessageCode.LOCAL_LOGIN + 1,
            True,
            None,
            None,
        ),
    ],
)
def test_transaction_is_valid_response(responsecode, expected, error, message):
    login_request = LocalLoginRequest()
    response = NonCallableMagicMock(
        spec=BaseResponse, code=responsecode, payload=Payload(b"")
    )
    transaction = Transaction(login_request)
    result = transaction._is_valid_response(response)
    assert result == expected
    if error:
        assert isinstance(transaction._last_error, error)
        assert transaction._last_error.msg == message


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "sendresults",
    [
        ((complete_fut, LocalLoginResponse()),),
        (
            (timeout_fut, None),
            (complete_fut, LocalLoginResponse()),
        ),
        pytest.param(
            (
                (timeout_fut, None),
                (timeout_fut, None),
            ),
            marks=pytest.mark.xfail(raises=ScreenLogicConnectionError),
        ),
        pytest.param(
            (
                (cancel_fut, LocalLoginResponse()),
                (cancel_fut, LocalLoginResponse()),
            ),
            marks=pytest.mark.xfail(raises=ScreenLogicConnectionError),
        ),
    ],
)
async def test_transaction_execute_via(sendresults):
    transaction = Transaction(LocalLoginRequest(), timout=0.01, retry_delay=0.0)
    itr = iter(sendresults)
    loop = asyncio.get_running_loop()

    async def mock_send(req, tout):
        result_func, result = next(itr)
        fut = loop.create_future()
        return result_func(fut, result)

    response = await transaction.execute_via(mock_send)
    assert response


# **************************************
# *      Connect Sequence Tests        *
# **************************************


@pytest.mark.asyncio
async def test_connect():
    with patch(
        "asyncio.get_running_loop",
        return_value=(
            NonCallableMagicMock(
                spec=asyncio.AbstractEventLoop,
                create_connection=AsyncMock(
                    return_value=(
                        NonCallableMagicMock(spec=asyncio.Transport),
                        NonCallableMagicMock(spec=ScreenLogicProtocol),
                    )
                ),
            )
        ),
    ) as mock_loop:
        mock_transport, mock_protocol = await connect(GatewayInfo(GW_ADDR, GW_PORT))
        mock_loop.return_value.create_connection.assert_awaited()
        assert isinstance(
            mock_loop.return_value.create_connection.await_args[0][0](),
            ScreenLogicProtocol,
        )
        assert mock_loop.return_value.create_connection.await_args[0][1] == GW_ADDR
        assert mock_loop.return_value.create_connection.await_args[0][2] == GW_PORT


@pytest.mark.asyncio
async def test_connect_timeout():

    async def long_connect(proto, addr, port):
        await asyncio.sleep(5)
        return (
            NonCallableMagicMock(spec=asyncio.Transport),
            NonCallableMagicMock(spec=ScreenLogicProtocol),
        )

    with patch(
        "asyncio.get_running_loop",
        return_value=(
            NonCallableMagicMock(
                spec=asyncio.AbstractEventLoop,
                create_connection=long_connect,
            )
        ),
    ) as mock_loop:
        with pytest.raises(
            ScreenLogicConnectionError,
            match=f"Failed to connect to host at {GW_ADDR}:{GW_PORT}",
        ):
            mock_transport, mock_protocol = await connect(GatewayInfo(GW_ADDR, GW_PORT))


@pytest.mark.asyncio
async def test_connect_error():
    with patch(
        "asyncio.get_running_loop",
        return_value=(
            NonCallableMagicMock(
                spec=asyncio.AbstractEventLoop,
                create_connection=AsyncMock(side_effect=OSError),
            )
        ),
    ) as mock_loop:
        with pytest.raises(
            ScreenLogicConnectionError,
            match=f"Failed to connect to host at {GW_ADDR}:{GW_PORT}",
        ):
            mock_transport, mock_protocol = await connect(GatewayInfo(GW_ADDR, GW_PORT))


@pytest.mark.asyncio
async def test_prime():
    mock_protocol = NonCallableMagicMock(spec=ScreenLogicProtocol)
    await prime(mock_protocol)
    mock_protocol.send_data.assert_called_with(CONNECT_PING)


@pytest.mark.asyncio
async def test_prime_error():
    mock_protocol = NonCallableMagicMock(
        spec=ScreenLogicProtocol, send_data=MagicMock(side_effect=OSError)
    )
    with pytest.raises(ScreenLogicConnectionError, match="Error priming connection"):
        await prime(mock_protocol)


@pytest.mark.asyncio
async def test_challange():
    mac_sl_string = encode_string(GW_MAC)
    test_response = ChallengeResponse(Payload(mac_sl_string))
    response_fut = asyncio.get_running_loop().create_future()
    response_fut.set_result(test_response)

    def mock_await_send_message(msg):
        return response_fut

    mock_protocol = NonCallableMagicMock(
        spec=ScreenLogicProtocol, await_send_message=mock_await_send_message
    )
    assert await challenge(mock_protocol) == GW_MAC


@pytest.mark.asyncio
async def test_login():
    test_response = LocalLoginResponse()
    response_fut = asyncio.get_running_loop().create_future()
    response_fut.set_result(test_response)

    def mock_await_send_message(msg):
        return response_fut

    mock_protocol = NonCallableMagicMock(
        spec=ScreenLogicProtocol,
        await_send_message=MagicMock(side_effect=mock_await_send_message),
    )
    await login(mock_protocol)
    mock_protocol.await_send_message.assert_called_once()
    assert isinstance(
        mock_protocol.await_send_message.call_args[0][0], LocalLoginRequest
    )


# **************************************
# *         Connection Tests           *
# **************************************


@pytest.mark.asyncio
async def test_connection_open():
    mock_transport = NonCallableMagicMock(spec=asyncio.Transport)
    mock_protocol = NonCallableMagicMock(
        spec=ScreenLogicProtocol, is_connected=MagicMock(return_value=True)
    )
    with patch(
        "screenlogicpy.connection.connect",
        return_value=(
            mock_transport,
            mock_protocol,
        ),
    ) as mock_connect, patch("screenlogicpy.connection.prime"), patch(
        "screenlogicpy.connection.challenge", return_value=GW_MAC
    ) as mock_challenge, patch(
        "screenlogicpy.connection.login"
    ) as mock_login:
        connection = Connection(keep_alive=False)
        gwinfo = GatewayInfo(GW_ADDR, GW_PORT)
        await connection.open(gwinfo)
    mock_connect.assert_called_with(
        gwinfo,
        COM_TIMEOUT,
        connection._message_received,
        connection._connection_lost,
    )
    mock_challenge.assert_called_with(
        mock_protocol, COM_TIMEOUT, COM_RETRY_WAIT, COM_MAX_RETRIES
    )
    assert connection.gateway.mac == GW_MAC
    assert connection.is_active


@pytest.mark.asyncio
async def test_connection_close():
    mock_transport = NonCallableMagicMock(spec=asyncio.Transport)
    mock_protocol = NonCallableMagicMock(spec=ScreenLogicProtocol)
    mock_ka_handle = NonCallableMagicMock(spec=asyncio.TimerHandle)
    connection = Connection()
    connection._transport = mock_transport
    connection._protocol = mock_protocol
    connection._keep_alive_handle = mock_ka_handle
    assert connection._transport
    assert connection._protocol
    assert connection._keep_alive_handle
    await connection.close()
    mock_protocol.close.assert_called_once()
    mock_ka_handle.cancel.assert_called_once()
    assert not connection._keep_alive_handle
    assert not connection._transport
    assert not connection._protocol


@pytest.mark.asyncio
async def test_connection_sends():
    connection = Connection()
    connection._active = False
    connection._gw_info = GatewayInfo(GW_ADDR, GW_PORT)
    connection._keep_alive = False
    connection._protocol = NonCallableMagicMock(
        spec=ScreenLogicProtocol, await_send_message=MagicMock(return_value=True)
    )

    async def mock_open(gwinfo):
        assert to.when() == None
        await asyncio.sleep(COM_TIMEOUT + 1)

    with patch.object(connection, "open", mock_open):
        async with asyncio.Timeout(COM_TIMEOUT) as to:
            await connection.connected_send(LocalLoginRequest(), to)
            assert to.when() == COM_TIMEOUT


@pytest.mark.asyncio
async def test_connection_keep_alive():
    connection = Connection()
    with patch(
        "screenlogicpy.connection.Transaction", execute_via=AsyncMock()
    ) as mock_transaction:
        connection.enable_keepalive(1)
        assert connection._keep_alive_handle
        assert isinstance(connection._keep_alive_handle, asyncio.TimerHandle)
        await asyncio.sleep(2)
        mock_transaction.return_value.execute_via.assert_called_once()
        connection.disable_keepalive()
        assert not connection._keep_alive_handle


@pytest.mark.asyncio
async def test_connection_keep_alive_delay():
    with patch(
        "asyncio.get_running_loop",
        return_value=(
            NonCallableMagicMock(
                spec=asyncio.BaseEventLoop,
                call_later=MagicMock(),
            )
        ),
    ) as mock_loop:
        loop_inst = mock_loop.return_value
        test_connection = Connection()

        # Test Defaults
        test_connection.enable_keepalive()
        assert loop_inst.call_later.call_args[0][0] == COM_KEEPALIVE
        assert test_connection._keep_alive_delay == COM_KEEPALIVE

        test_connection._reset_keep_alive()
        assert loop_inst.call_later.call_args[0][0] == COM_KEEPALIVE
        assert test_connection._keep_alive == True

        test_connection.disable_keepalive()
        assert test_connection._keep_alive_delay == COM_KEEPALIVE
        assert test_connection._keep_alive_handle == None
        assert test_connection._keep_alive == False

        # Test Specified
        val = 300
        test_connection.enable_keepalive(val)
        assert loop_inst.call_later.call_args[0][0] == val
        assert test_connection._keep_alive_delay == val

        test_connection._reset_keep_alive()
        assert loop_inst.call_later.call_args[0][0] == val
        assert test_connection._keep_alive == True

        test_connection.disable_keepalive()
        assert test_connection._keep_alive_delay == val
        assert test_connection._keep_alive_handle == None
        assert test_connection._keep_alive == False

        # Test None
        test_connection.enable_keepalive(None)
        assert mock_loop.return_value.call_later.call_args[0][0] == val
        assert test_connection._keep_alive_delay == val

        test_connection._reset_keep_alive()
        assert mock_loop.return_value.call_later.call_args[0][0] == val
        assert test_connection._keep_alive == True

        loop_inst.call_later.reset_mock()

        test_connection._reset_keep_alive(None)
        assert test_connection._keep_alive_delay == val
        loop_inst.call_later.assert_not_called()
        assert test_connection._keep_alive_handle == None


@pytest.mark.asyncio
async def test_connection_callbacks():
    mock_callback = MagicMock()
    connection = Connection(
        async_message_cb=mock_callback, connection_lost_cb=mock_callback
    )
    test_response = BaseResponse()

    connection._active = True
    connection._reset_keep_alive()
    connection._message_received(test_response)
    mock_callback.assert_called_once_with(test_response)
    assert connection._active == True
    assert connection._keep_alive_handle

    connection._connection_lost(False)
    assert connection._active == False
    assert not connection._keep_alive_handle
    mock_callback.assert_called_with(False)
