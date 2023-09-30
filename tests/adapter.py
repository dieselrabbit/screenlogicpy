import asyncio
from enum import IntEnum
from dataclasses import dataclass
import struct
from typing import Any

from screenlogicpy.const.msg import CODE
from screenlogicpy.data import ScreenLogicResponseCollection
from screenlogicpy.requests.utility import encodeMessageString, makeMessage, takeMessage

from tests.const_data import (
    FAKE_GATEWAY_MAC,
)


@dataclass
class SLMessage:
    id: int
    code: int
    data: bytes = b""


class CONNECTION_STATE(IntEnum):
    NO_CONNECTION = 0
    CONNECTSERVERHOST = 1
    CHALLENGE = 2
    LOGIN = 3


class FakeProtocolAdapterTCPProtocol(asyncio.Protocol):
    def __init__(self, responses: ScreenLogicResponseCollection) -> None:
        self.responses = responses
        self._cs = CONNECTION_STATE.NO_CONNECTION

        self.unconnected_response_map = {
            CODE.CHALLENGE_QUERY: self.handle_challenge_request,
            CODE.LOCALLOGIN_QUERY: self.handle_logon_request,
        }
        self.connected_response_map = {
            CODE.VERSION_QUERY: self.handle_version_request,
            CODE.CTRLCONFIG_QUERY: self.handle_config_request,
            CODE.POOLSTATUS_QUERY: self.handle_status_request,
            CODE.PUMPSTATUS_QUERY: self.handle_pump_state_request,
            CODE.CHEMISTRY_QUERY: self.handle_chemistry_status_request,
            CODE.SCGCONFIG_QUERY: self.handle_scg_status_request,
            CODE.BUTTONPRESS_QUERY: self.handle_button_press_request,
            CODE.LIGHTCOMMAND_QUERY: self.handle_light_command_request,
            CODE.SETHEATMODE_QUERY: self.handle_set_heat_mode_request,
            CODE.SETHEATTEMP_QUERY: self.handle_set_heat_temp_request,
            CODE.SETSCG_QUERY: self.handle_set_scg_config_request,
            CODE.SETCHEMDATA_QUERY: self.handle_set_chemistry_config_request,
            CODE.ADD_CLIENT_QUERY: self.handle_add_client_request,
            CODE.REMOVE_CLIENT_QUERY: self.handle_remove_client_request,
            CODE.PING_QUERY: self.handle_ping_request,
        }

    def connection_made(self, transport: asyncio.Transport) -> None:
        self.transport = transport

    def data_received(self, data: bytes) -> None:
        resp: SLMessage
        if (resp := self.process_data(data)) is not None:
            self.transport.write(makeMessage(resp.id, resp.code, resp.data))

    def process_data(self, data: bytes) -> bytes:
        if self._cs == CONNECTION_STATE.NO_CONNECTION:
            if data == b"CONNECTSERVERHOST\r\n\r\n":
                self._cs = CONNECTION_STATE.CONNECTSERVERHOST
                return None
        return self.process_message(SLMessage(*takeMessage(data)))

    def process_message(self, msg: SLMessage) -> bytes:
        if self._cs == CONNECTION_STATE.LOGIN:
            if (code_handler := self.connected_response_map.get(msg.code)) is not None:
                return code_handler(msg)
        else:
            if (
                logon_handler := self.unconnected_response_map.get(msg.code)
            ) is not None:
                return logon_handler(msg)
        return SLMessage(msg.id, CODE.ERROR_INVALID_REQUEST)

    def handle_challenge_request(self, msg: SLMessage) -> SLMessage:
        if self._cs == CONNECTION_STATE.CONNECTSERVERHOST:
            self._cs = CONNECTION_STATE.CHALLENGE
            return SLMessage(
                msg.id, msg.code + 1, encodeMessageString(FAKE_GATEWAY_MAC)
            )
        return SLMessage(msg.id, CODE.ERROR_BAD_PARAMETER)

    def handle_logon_request(self, msg: SLMessage) -> SLMessage:
        if self._cs == CONNECTION_STATE.CHALLENGE:
            self._cs = CONNECTION_STATE.LOGIN
            return SLMessage(msg.id, msg.code + 1)
        return SLMessage(msg.id, CODE.ERROR_LOGIN_REJECTED)

    def handle_version_request(self, msg: SLMessage) -> SLMessage:
        return SLMessage(msg.id, msg.code + 1, self.responses.version.raw)

    def handle_config_request(self, msg: SLMessage) -> SLMessage:
        return SLMessage(msg.id, msg.code + 1, self.responses.config.raw)

    def handle_status_request(self, msg: SLMessage) -> SLMessage:
        return SLMessage(msg.id, msg.code + 1, self.responses.status.raw)

    def handle_pump_state_request(self, msg: SLMessage) -> SLMessage:
        pump = struct.unpack_from("<I", msg.data, 4)[0]
        return SLMessage(msg.id, msg.code + 1, self.responses.pumps[pump].raw)

    def handle_chemistry_status_request(self, msg: SLMessage) -> SLMessage:
        return SLMessage(msg.id, msg.code + 1, self.responses.chemistry.raw)

    def handle_scg_status_request(self, msg: SLMessage) -> SLMessage:
        return SLMessage(msg.id, msg.code + 1, self.responses.scg.raw)

    def handle_button_press_request(self, msg: SLMessage) -> SLMessage:
        return SLMessage(msg.id, msg.code + 1)

    def handle_light_command_request(self, msg: SLMessage) -> SLMessage:
        return SLMessage(msg.id, msg.code + 1)

    def handle_set_heat_mode_request(self, msg: SLMessage) -> SLMessage:
        return SLMessage(msg.id, msg.code + 1)

    def handle_set_heat_temp_request(self, msg: SLMessage) -> SLMessage:
        return SLMessage(msg.id, msg.code + 1)

    def handle_set_scg_config_request(self, msg: SLMessage) -> SLMessage:
        return SLMessage(msg.id, msg.code + 1)

    def handle_set_chemistry_config_request(self, msg: SLMessage) -> SLMessage:
        return SLMessage(msg.id, msg.code + 1)

    def handle_add_client_request(self, msg: SLMessage) -> SLMessage:
        return SLMessage(msg.id, msg.code + 1)

    def handle_remove_client_request(self, msg: SLMessage) -> SLMessage:
        return SLMessage(msg.id, msg.code + 1)

    def handle_ping_request(self, msg: SLMessage) -> SLMessage:
        return SLMessage(msg.id, msg.code + 1)


class FakeUDPProtocolAdapter(asyncio.DatagramProtocol):
    def __init__(self, discovery_response: bytes) -> None:
        self.discovery_response = discovery_response

    def connection_made(self, transport: asyncio.DatagramTransport) -> None:
        self.transport = transport

    def datagram_received(self, data: bytes, addr: tuple[str | Any, int]) -> None:
        if struct.unpack("<8b", data) == (1, 0, 0, 0, 0, 0, 0, 0):
            self.transport.sendto(self.discovery_response, addr)
