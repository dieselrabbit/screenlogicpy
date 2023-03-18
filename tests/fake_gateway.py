""" Fake ScreenLogic gateway """
import asyncio
import random
import struct
import time
from typing import List, Tuple

from screenlogicpy.const import CODE, MESSAGE
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


def expected_resp(req_code, resp_data=b""):
    return 0, req_code + 1, resp_data


def error_resp(req_code):
    if req_code == CODE.LOCALLOGIN_QUERY:
        return 0, CODE.ERROR_LOGIN_REJECTED, b""
    else:
        return 0, CODE.ERROR_BAD_PARAMETER, b""


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
        self._buff = bytearray()

    def data_received(self, data: bytes) -> None:
        for response in self.process_request(data):
            if response is not None:
                self.transport.write(response)

    def connection_lost(self, exc: Exception) -> None:
        return super().connection_lost(exc)

    def process_request(self, data):
        if self._connection_stage == CONNECTION_STAGE.NO_CONNECTION:
            if data == b"CONNECTSERVERHOST\r\n\r\n":
                self._connection_stage = CONNECTION_STAGE.CONNECTSERVERHOST
                return []

        def complete_messages(data: bytes) -> List[Tuple[int, int, bytes]]:
            """Return only complete ScreenLogic messages."""

            self._buff.extend(data)
            complete = []
            while len(self._buff) >= MESSAGE.HEADER_LENGTH:
                dataLen = struct.unpack_from("<I", self._buff, 4)[0]
                totalLen = MESSAGE.HEADER_LENGTH + dataLen
                if len(self._buff) >= totalLen:
                    out = bytearray()
                    for _ in range(totalLen):
                        out.append(self._buff.pop(0))
                    complete.append(takeMessage(bytes(out)))
                else:
                    break
            return complete

        return [self.process_message(message) for message in complete_messages(data)]

    def process_message(self, message: Tuple[int, int, bytes]) -> bytes:
        time.sleep(0.1)
        messageID, messageCode, _ = message
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


class FailingFakeScreenLogicTCPProtocol(FakeScreenLogicTCPProtocol):
    def process_message(self, message: Tuple[int, int, bytes]) -> bytes:
        call_max = 75
        messageID, messageCode, _ = message
        call_min = messageID if messageID < call_max else call_max
        fail = random.randint(call_min, call_max)
        if fail > 68:
            if fail > 72:
                if messageCode == CODE.LOCALLOGIN_QUERY:
                    return makeMessage(messageID, CODE.ERROR_LOGIN_REJECTED)
                else:
                    return makeMessage(messageID, CODE.ERROR_BAD_PARAMETER)
            else:
                return None
        else:
            return super().process_message(message)


class FailingFakeScreenLogicTCPProtocol(FakeScreenLogicTCPProtocol):
    def process_request(self, data):
        fail = random.randint(0, 5)
        if fail > 3:
            messageID, messageCode, _ = takeMessage(data)
            if fail == 4:
                if messageCode == CODE.LOCALLOGIN_QUERY:
                    return makeMessage(messageID, CODE.ERROR_LOGIN_REJECTED)
                else:
                    return makeMessage(messageID, CODE.ERROR_BAD_PARAMETER)
            else:
                return None
        else:
            return super().process_request(data)


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
