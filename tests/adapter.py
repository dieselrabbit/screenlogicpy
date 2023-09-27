import asyncio
from enum import IntEnum
import struct
from typing import Any

from screenlogicpy.const.msg import CODE
from screenlogicpy.data import ScreenLogicResponseCollection
from screenlogicpy.requests.utility import encodeMessageString, makeMessage, takeMessage

from tests.const_data import (
    FAKE_GATEWAY_MAC,
)


class CONNECTION_STATE(IntEnum):
    NO_CONNECTION = 0
    CONNECTSERVERHOST = 1
    CHALLENGE = 2
    LOGIN = 3


class FakeProtocolAdapterTCPProtocol(asyncio.Protocol):
    def __init__(self, responses: ScreenLogicResponseCollection) -> None:
        self.responses = responses
        self._cs = CONNECTION_STATE.NO_CONNECTION

        self.response_map = {
            CODE.VERSION_QUERY: self.responses.version.raw,
            CODE.CTRLCONFIG_QUERY: self.responses.config.raw,
            CODE.POOLSTATUS_QUERY: self.responses.status.raw,
            CODE.STATUS_CHANGED: self.responses.status.raw,
            CODE.PUMPSTATUS_QUERY: lambda pump_num: self.responses.pumps[pump_num].raw,
            CODE.CHEMISTRY_QUERY: self.responses.chemistry.raw,
            CODE.CHEMISTRY_CHANGED: self.responses.chemistry.raw,
            CODE.SCGCONFIG_QUERY: self.responses.scg.raw,
            CODE.BUTTONPRESS_QUERY: b"",
            CODE.LIGHTCOMMAND_QUERY: b"",
            CODE.SETHEATMODE_QUERY: b"",
            CODE.SETHEATTEMP_QUERY: b"",
            CODE.SETSCG_QUERY: b"",
            CODE.SETCHEMDATA_QUERY: b"",
            CODE.ADD_CLIENT_QUERY: b"",
            CODE.REMOVE_CLIENT_QUERY: b"",
            CODE.PING_QUERY: b"",
        }

    def connection_made(self, transport: asyncio.Transport) -> None:
        self.transport = transport

    def data_received(self, data: bytes) -> None:
        if (response := self.process_data(data)) is not None:
            self.transport.write(response)

    def process_data(self, data: bytes) -> bytes:
        if self._cs == CONNECTION_STATE.NO_CONNECTION:
            if data == b"CONNECTSERVERHOST\r\n\r\n":
                self._cs = CONNECTION_STATE.CONNECTSERVERHOST
                return None
        return self.process_message(takeMessage(data))

    def process_message(self, message: tuple[int, int, bytes]) -> bytes:
        msgID, msgCode, _ = message
        if self._cs == CONNECTION_STATE.LOGIN:
            return self.process_request(message)
        else:
            if self._cs == CONNECTION_STATE.CONNECTSERVERHOST:
                if msgCode == CODE.CHALLENGE_QUERY:
                    self._cs = CONNECTION_STATE.CHALLENGE
                    return makeMessage(
                        msgID, msgCode + 1, encodeMessageString(FAKE_GATEWAY_MAC)
                    )
            elif self._cs == CONNECTION_STATE.CHALLENGE:
                if msgCode == CODE.LOCALLOGIN_QUERY:
                    self._cs = CONNECTION_STATE.LOGIN
                    return makeMessage(msgID, msgCode + 1)
            return makeMessage(msgID, CODE.ERROR_LOGIN_REJECTED)

    def process_request(self, message: tuple[int, int, bytes]) -> bytes:
        msgID, msgCode, msgData = message
        if msgCode in self.response_map:
            if msgCode == CODE.PUMPSTATUS_QUERY:
                pump = struct.unpack_from("<I", msgData, 4)[0]
                return makeMessage(msgID, msgCode + 1, self.response_map[msgCode](pump))
            else:
                return makeMessage(msgID, msgCode + 1, self.response_map[msgCode])
        else:
            return makeMessage(msgID, CODE.ERROR_INVALID_REQUEST)


class FakeUDPProtocolAdapter(asyncio.DatagramProtocol):
    def __init__(self, discovery_response: bytes) -> None:
        self.discovery_response = discovery_response

    def connection_made(self, transport: asyncio.DatagramTransport) -> None:
        self.transport = transport

    def datagram_received(self, data: bytes, addr: tuple[str | Any, int]) -> None:
        if struct.unpack("<8b", data) == (1, 0, 0, 0, 0, 0, 0, 0):
            self.transport.sendto(self.discovery_response, addr)
