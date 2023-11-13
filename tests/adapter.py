import asyncio
from enum import IntEnum
from dataclasses import dataclass
from datetime import datetime
import struct
from typing import Any

from screenlogicpy.const.msg import CODE, HEADER_LENGTH
from screenlogicpy.data import ScreenLogicResponseCollection
from screenlogicpy.requests.utility import (
    encodeMessageString,
    encodeMessageTime,
    makeMessage,
    takeMessage,
    getSome,
    getString,
)

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
    PRIMED = 1
    CONNECTED = 2


class FakeTCPProtocolAdapter(asyncio.Protocol):
    def __init__(self, responses: ScreenLogicResponseCollection) -> None:
        self.responses = responses
        self._cs = CONNECTION_STATE.NO_CONNECTION
        self._buff = bytearray()
        print("TCP up")

        self.unconnected_response_map = {
            CODE.CHALLENGE_QUERY: self.handle_challenge_request,
            CODE.LOCALLOGIN_QUERY: self.handle_logon_request,
        }
        self.connected_response_map = {
            CODE.VERSION_QUERY: self.handle_version_request,
            CODE.FIRMWARE_QUERY: self.handle_firmware_request,
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
            CODE.GET_DATETIME_QUERY: self.handle_date_time_request,
            CODE.SET_DATETIME_QUERY: self.handle_set_date_time_request,
            CODE.EQUIPMENT_QUERY: self.handle_equipment_request,
        }

    def connection_made(self, transport: asyncio.Transport) -> None:
        self.transport = transport
        print("TCP Connected.")

    def data_received(self, data: bytes) -> None:
        print("Pentair data received!")
        self.process_data(data)

    def process_data(self, data: bytes) -> bytes:
        if self._cs == CONNECTION_STATE.NO_CONNECTION:
            if data == b"CONNECTSERVERHOST\r\n\r\n":
                print("Adapter primmed!")
                self._cs = CONNECTION_STATE.PRIMED
                return None
            # Adapter not primed. Go away.
            self.transport.close()

        self._buff.extend(data)

        # Take complete messages
        while len(self._buff) >= HEADER_LENGTH:
            dataLen = struct.unpack_from("<I", self._buff, 4)[0]
            nextMsgLen = HEADER_LENGTH + dataLen
            if len(self._buff) >= nextMsgLen:
                out = bytearray()
                for _ in range(nextMsgLen):
                    out.append(self._buff.pop(0))
                self.process_message(SLMessage(*takeMessage(bytes(out))))
                print(f"{len(self._buff)} left in buffer")
            else:
                break

    def process_message(self, msg: SLMessage) -> None:
        print(f"Received msg {msg.code}, {msg.data}")

        def get_response(msg: SLMessage) -> SLMessage | None:
            if self._cs == CONNECTION_STATE.CONNECTED:
                if (
                    connected_handler := self.connected_response_map.get(msg.code)
                ) is not None:
                    return connected_handler(msg)

            if self._cs >= CONNECTION_STATE.PRIMED:
                if (
                    primed_handler := self.unconnected_response_map.get(msg.code)
                ) is not None:
                    return primed_handler(msg)
                else:
                    return SLMessage(msg.id, CODE.ERROR_INVALID_REQUEST)

            self.transport.close()

        if (resp := get_response(msg)) is not None:
            print(f"Sent msg {resp.code}, {resp.data}")
            self.transport.write(makeMessage(resp.id, resp.code, resp.data))

    def handle_challenge_request(self, msg: SLMessage) -> SLMessage:
        return SLMessage(
            msg.id,
            msg.code + 1,
            encodeMessageString(FAKE_GATEWAY_MAC).ljust(28, b"\x00"),
        )

    def handle_logon_request(self, msg: SLMessage) -> SLMessage:
        schema, connType, clientType, passWord, pid = decode_login(msg.data)
        if pid == 2:
            self._cs = CONNECTION_STATE.CONNECTED
            return SLMessage(msg.id, msg.code + 1)
        return SLMessage(msg.id, CODE.ERROR_LOGIN_REJECTED)

    def handle_version_request(self, msg: SLMessage) -> SLMessage:
        return SLMessage(msg.id, msg.code + 1, self.responses.version.raw)

    def handle_firmware_request(self, msg: SLMessage) -> SLMessage:
        return SLMessage(
            msg.id,
            msg.code + 1,
            b"\x50\x00\x00\x00\x50\x00\x00\x00\x11\x00\x00\x00\x50\x65\x6e\x74"
            b"\x61\x69\x72\x3a\x20\x41\x41\x2d\x42\x42\x2d\x43\x43\x00\x00\x00"
            b"\x05\x00\x00\x00\x39\x30\x30\x30\x31\x00\x00\x00\x84\x2b\x05\x00"
            b"\xa4\xeb\x24\x00\xf9\xff\xff\xff\x19\x00\x00\x00\x50\x4f\x4f\x4c"
            b"\x3a\x20\x35\x2e\x32\x20\x42\x75\x69\x6c\x64\x20\x37\x33\x36\x2e"
            b"\x30\x20\x52\x65\x6c\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00"
            b"\x00\x00\x00\x00\x01\x00\x00\x00\x30\x00\x00\x00\x00\x00\x00\x00"
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x0b\x00\x00\x00\x52\x61\x62\x62"
            b"\x69\x74\x20\x43\x6f\x72\x65\x00\x05\x00\x00\x00\x42\x52\x49\x43"
            b"\x4b\x00\x00\x00",
        )

    def handle_config_request(self, msg: SLMessage) -> SLMessage:
        return SLMessage(msg.id, msg.code + 1, self.responses.config.raw)

    def handle_status_request(self, msg: SLMessage) -> SLMessage:
        return SLMessage(msg.id, msg.code + 1, self.responses.status.raw)

    def handle_pump_state_request(self, msg: SLMessage) -> SLMessage:
        try:
            pump_num, _ = getSome("I", msg.data, 4)
            if not 0 <= pump_num <= 7:
                raise ValueError("Invalid pump number")
        except Exception as ex:
            print(ex)
            return SLMessage(msg.id, CODE.ERROR_BAD_PARAMETER)
        return SLMessage(msg.id, msg.code + 1, self.responses.pumps[pump_num].raw)

    def handle_chemistry_status_request(self, msg: SLMessage) -> SLMessage:
        return SLMessage(msg.id, msg.code + 1, self.responses.chemistry.raw)

    def handle_scg_status_request(self, msg: SLMessage) -> SLMessage:
        return SLMessage(msg.id, msg.code + 1, self.responses.scg.raw)

    def handle_button_press_request(self, msg: SLMessage) -> SLMessage:
        return default_response(msg)

    def handle_light_command_request(self, msg: SLMessage) -> SLMessage:
        return default_response(msg)

    def handle_set_heat_mode_request(self, msg: SLMessage) -> SLMessage:
        return default_response(msg)

    def handle_set_heat_temp_request(self, msg: SLMessage) -> SLMessage:
        return default_response(msg)

    def handle_set_scg_config_request(self, msg: SLMessage) -> SLMessage:
        return default_response(msg)

    def handle_set_chemistry_config_request(self, msg: SLMessage) -> SLMessage:
        return default_response(msg)

    def handle_add_client_request(self, msg: SLMessage) -> SLMessage:
        return default_response(msg)

    def handle_remove_client_request(self, msg: SLMessage) -> SLMessage:
        return default_response(msg)

    def handle_ping_request(self, msg: SLMessage) -> SLMessage:
        return default_response(msg)

    def handle_date_time_request(self, msg: SLMessage) -> SLMessage:
        return SLMessage(
            msg.id,
            msg.code + 1,
            encodeMessageTime(datetime.now()) + struct.pack("<I", 1),
        )

    def handle_set_date_time_request(self, msg: SLMessage) -> SLMessage:
        return default_response(msg)

    def handle_equipment_request(self, msg: SLMessage) -> SLMessage:
        return SLMessage(msg.id, msg.code + 1, EQUIP_CONFIG)


class FakeUDPProtocolAdapter(asyncio.DatagramProtocol):
    def __init__(self, discovery_response: bytes) -> None:
        self.discovery_response = discovery_response
        print("UDP up)")

    def connection_made(self, transport: asyncio.DatagramTransport) -> None:
        print("Connection")
        self.transport = transport

    def datagram_received(self, data: bytes, addr: tuple[str | Any, int]) -> None:
        print("Received datagram.")
        if struct.unpack("<8b", data) == (1, 0, 0, 0, 0, 0, 0, 0):
            print("Pentair discovery!", addr, self.discovery_response)
            self.transport.sendto(self.discovery_response, addr)


def default_response(msg: SLMessage) -> SLMessage:
    return SLMessage(msg.id, msg.code + 1)


def decode_login(buff: bytes) -> tuple[bytes]:
    schema, offset = getSome("I", buff, 0)
    connType, offset = getSome("I", buff, offset)
    clientType, offset = getString(buff, offset)
    passWord, offset = getString(buff, offset)
    if schema == 348:
        offset += 1
    pid, offset = getSome("I", buff, offset)

    return schema, connType, clientType, passWord, pid


EQUIP_CONFIG = (
    b"\x0d\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x02\xa0\x00\x00"
    b"\x01\x0a\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00"
    b"\x00\x00\x00\x00\x41\x48\x00\x00\x18\x00\x00\x00\x03\x00\x00\x00"
    b"\x05\x00\xff\xff\xff\x00\x00\x00\x00\x00\x05\x06\x07\x08\x09\x0a"
    b"\x01\x02\x03\x04\x2c\x00\x00\x00\x00\x00\x00\x00\x05\x06\x07\x08"
    b"\x09\x0a\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x01\x02\x03\x04\x03\x00\x00\x00\x05\x00\x46\x00\x02\x00\x00\x00"
    b"\x10\x00\x00\x00\x8c\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x0a\x00\x00\x00\x00\x00\x00\x01\x01\x00\x00\x00"
    b"\x00\x00\x00\x00\x0c\x00\x00\x00\x03\x04\x07\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x68\x01\x00\x00\x40\x00\x00\x04\x06\x3f\x09\x48"
    b"\x01\x0d\x82\x4b\x0c\x48\x00\x1e\x00\x1e\x00\x1e\x00\xc4\x7a\x7a"
    b"\x00\x00\x00\x00\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff\x00\x00"
    b"\x00\x00\x00\x00\x00\x40\x0f\x02\x01\x02\x0a\x00\x1e\x00\x1e\x00"
    b"\x1e\x00\x1e\x00\x1e\x00\x1e\x00\x1e\x00\x8c\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x16\x00\x00\x00\x00\x3f\x00\x00\x00\x00\x20\x20\x20\x20\x20\x20"
    b"\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x00\x00\x10\x00\x00\x00"
    b"\x00\x00\x00\x00\x3e\x00\x32\x01\x01\x90\x0d\x7a\x0f\x82\x00\x00"
)
