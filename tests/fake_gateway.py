""" Fake ScreenLogic gateway """
import socket
import struct

from screenlogicpy.const import code
from screenlogicpy.requests.utility import takeMessage, makeMessage, encodeMessageString
from tests.const_data import (
    FAKE_CONFIG_RESPONSE,
    FAKE_STATUS_RESPONSE,
    FAKE_PUMP_RESPONSE,
    FAKE_CHEMISTRY_RESPONSE,
    FAKE_SCG_RESPONSE,
)

FAKE_GATEWAY_ADDRESS = "127.0.0.1"
FAKE_GATEWAY_CHK = 2
FAKE_GATEWAY_DISCOVERY_PORT = 1444
FAKE_GATEWAY_MAC = "00:00:00:00:00:00"
FAKE_GATEWAY_NAME = b"Fake: 00-00-00"
FAKE_GATEWAY_PORT = 6448
FAKE_GATEWAY_SUB_TYPE = 12
FAKE_GATEWAY_TYPE = 2


class fake_ScreenLogicGateway:
    def __init__(self, discovery=False, requests=False):
        self._connectServerHost = False
        self._challenge = False
        self._login = False
        self._discovery = discovery
        self._requests = requests
        self._udp_sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self._tcp_sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)

    def __enter__(self):
        if self._discovery:
            self._udp_sock.bind(("", FAKE_GATEWAY_DISCOVERY_PORT))
        if self._requests:
            self._tcp_sock.bind((FAKE_GATEWAY_ADDRESS, FAKE_GATEWAY_PORT))

    def __exit__(self, exception_type, exception_value, traceback):
        self._udp_sock.close()
        self._tcp_sock.close()

    def start_discovery_server(self):
        while True:
            try:
                message, sender = self._udp_sock.recvfrom(1024)
            except Exception:
                break
            if struct.unpack("<8b", message) == (1, 0, 0, 0, 0, 0, 0, 0):
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
                    FAKE_GATEWAY_NAME,
                )
                self._udp_sock.sendto(response, sender)

    def start_request_server(self):
        self._tcp_sock.listen()
        print("waiting for connection")
        connection, _ = self._tcp_sock.accept()
        print("connected")
        with connection:
            while True:
                print("waiting for request")
                request = connection.recv(1024)
                if not request:
                    print("Connection closed")
                    break
                # print("handling request", request)
                self.handle_request(connection, request)

    def handle_request(self, connection, request):
        # print(request)
        if self._connectServerHost:
            rcvCode, _ = takeMessage(request)
            if rcvCode == code.CHALLENGE_QUERY:
                print("Challenge")
                connection.sendall(
                    makeMessage(
                        code.CHALLENGE_ANSWER, encodeMessageString(FAKE_GATEWAY_MAC)
                    )
                )
                self._connectServerHost = False
                self._challenge = True
        elif self._challenge:
            # pylint: disable=unused-variable
            rcvCode, buff = takeMessage(request)
            if rcvCode == code.LOCALLOGIN_QUERY:
                # Need to test validity of login message?
                print("Login")
                connection.sendall(makeMessage(code.LOCALLOGIN_ANSWER))
                self._challenge = False
                self._login = True
        elif self._login:
            rcvCode, buff = takeMessage(request)
            if rcvCode == code.VERSION_QUERY:
                print("Version")
                version = "fake 0.0.2"
                connection.sendall(
                    makeMessage(code.VERSION_ANSWER, encodeMessageString(version))
                )
            if rcvCode == code.CTRLCONFIG_QUERY:
                print("Config")
                connection.sendall(
                    makeMessage(code.CTRLCONFIG_ANSWER, FAKE_CONFIG_RESPONSE)
                )
            elif rcvCode == code.POOLSTATUS_QUERY:
                print("Status")
                connection.sendall(
                    makeMessage(code.POOLSTATUS_ANSWER, FAKE_STATUS_RESPONSE)
                )
            elif rcvCode == code.PUMPSTATUS_QUERY:
                print("Pump")
                connection.sendall(
                    makeMessage(code.PUMPSTATUS_ANSWER, FAKE_PUMP_RESPONSE)
                )
            elif rcvCode == code.CHEMISTRY_QUERY:
                print("Chemistry")
                connection.sendall(
                    makeMessage(code.CHEMISTRY_ANSWER, FAKE_CHEMISTRY_RESPONSE)
                )
            elif rcvCode == code.SCGCONFIG_QUERY:
                print("SCG")
                connection.sendall(
                    makeMessage(code.SCGCONFIG_ANSWER, FAKE_SCG_RESPONSE)
                )
            elif rcvCode == code.BUTTONPRESS_QUERY:
                connection.sendall(makeMessage(code.BUTTONPRESS_ANSWER))
            else:
                print("Unknown code")
        else:
            if request == b"CONNECTSERVERHOST\r\n\r\n":
                print("CONNECTSERVERHOST")
                self._connectServerHost = True
            else:
                print("Unknown request")
