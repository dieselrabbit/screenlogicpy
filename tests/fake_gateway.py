""" Fake ScreenLogic gateway """
import asyncio
import struct
from typing import Tuple

from screenlogicpy.const import CODE
from screenlogicpy.requests.utility import takeMessage, makeMessage, encodeMessageString
from tests.const_data import (
    ASYNC_SL_RESPONSES,
    FAKE_GATEWAY_ADDRESS,
    FAKE_GATEWAY_CHK,
    FAKE_GATEWAY_MAC,
    FAKE_GATEWAY_NAME,
    FAKE_GATEWAY_PORT,
    FAKE_GATEWAY_SUB_TYPE,
    FAKE_GATEWAY_TYPE,
)


class CONNECTION_STAGE:
    NO_CONNECTION = 0
    CONNECTSERVERHOST = 1
    CHALLENGE = 2
    LOGIN = 3


class FakeScreenLogicTCPProtocol(asyncio.Protocol):
    def connection_made(self, transport: asyncio.Transport) -> None:
        self.transport = transport
        self.connected = True
        self._connection_stage = CONNECTION_STAGE.NO_CONNECTION

    def data_received(self, data: bytes) -> None:
        if (data_to_send := self.process_request(data)) is not None:
            self.transport.write(data_to_send)

    def connection_lost(self, exc: Exception) -> None:
        return super().connection_lost(exc)

    def process_request(self, data):
        if self._connection_stage == CONNECTION_STAGE.NO_CONNECTION:
            if data == b"CONNECTSERVERHOST\r\n\r\n":
                self._connection_stage = CONNECTION_STAGE.CONNECTSERVERHOST
                return None

        messageID, messageCode, message = takeMessage(data)
        if (
            messageCode == CODE.CHALLENGE_QUERY
            and self._connection_stage == CONNECTION_STAGE.CONNECTSERVERHOST
        ):
            self._connection_stage = CONNECTION_STAGE.CHALLENGE
            return makeMessage(
                messageID,
                CODE.CHALLENGE_QUERY + 1,
                encodeMessageString(FAKE_GATEWAY_MAC),
            )

        if (
            messageCode == CODE.LOCALLOGIN_QUERY
            and self._connection_stage == CONNECTION_STAGE.CHALLENGE
        ):
            self._connection_stage = CONNECTION_STAGE.LOGIN
            return makeMessage(messageID, CODE.LOCALLOGIN_QUERY + 1, b"")

        if (
            self._connection_stage == CONNECTION_STAGE.LOGIN
            and messageCode in ASYNC_SL_RESPONSES
        ):
            return makeMessage(
                messageID, messageCode + 1, ASYNC_SL_RESPONSES[messageCode]
            )

        return None


class FakeScreenLogicUDPProtocol(asyncio.DatagramProtocol):
    def connection_made(self, transport: asyncio.DatagramTransport):
        self.transport = transport

    def datagram_received(self, data: bytes, addr: Tuple[str, int]) -> None:
        if struct.unpack("<8b", data) == (1, 0, 0, 0, 0, 0, 0, 0):
            ip1, ip2, ip3, ip4 = FAKE_GATEWAY_ADDRESS.split(".")
            response = struct.pack(
                f"<I4BH2B{len(FAKE_GATEWAY_NAME)}s",
                FAKE_GATEWAY_CHK,
                int(ip1),
                int(ip2),
                int(ip3),
                int(ip4),
                FAKE_GATEWAY_PORT,
                FAKE_GATEWAY_TYPE,
                FAKE_GATEWAY_SUB_TYPE,
                bytes(FAKE_GATEWAY_NAME, "UTF-8"),
            )
            self.transport.sendto(response, addr)
