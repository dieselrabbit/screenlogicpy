""" Fake ScreenLogic gateway """
import socket
import struct
import threading
from screenlogicpy.const import code
from screenlogicpy.requests.utility import takeMessage, makeMessage, encodeMessageString
from tests.const_data import (
    FAKE_CONFIG_RESPONSE,
    FAKE_STATUS_RESPONSE,
    FAKE_PUMP_RESPONSE,
    FAKE_CHEMISTRY_RESPONSE,
)


class fake_ScreenLogicGateway:
    def __init__(self, discovery=True, request=True):
        self._chk = 2
        self._broadcast_address = ""
        self._gateway_address = "127.0.0.1"
        self._discover_port = 1444
        self._gateway_port = 6448
        self._gateway_type = 2
        self._gateway_subtype = 12
        self._gateway_name = b"Fake: 00-00-00"
        self._gateway_mac = "00:00:00:00:00:00"
        self._connectServerHost = False
        self._challenge = False
        self._login = False
        self._discovery_thread = threading.Thread(
            target=self.discovery_server, daemon=True
        )
        self._request_thread = threading.Thread(target=self.request_server, daemon=True)

        if discovery:
            self._discovery_thread.start()

        if request:
            self._request_thread.start()

    def discovery_server(self,):
        with socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM) as udpSock:
            udpSock.bind((self._broadcast_address, self._discover_port))

            while True:
                request = udpSock.recvfrom(1024)
                message, sender = request
                if struct.unpack("<8b", message) == (1, 0, 0, 0, 0, 0, 0, 0):
                    ip1, ip2, ip3, ip4 = self._gateway_address.split(".")
                    response = struct.pack(
                        f"<I4BH2B{len(self._gateway_name)}s",
                        self._chk,
                        int(ip1),
                        int(ip2),
                        int(ip3),
                        int(ip4),
                        self._gateway_port,
                        self._gateway_type,
                        self._gateway_subtype,
                        self._gateway_name,
                    )
                    udpSock.sendto(response, sender)

    def request_server(self,):
        with socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM) as tcpSock:
            tcpSock.bind((self._gateway_address, self._gateway_port))
            tcpSock.listen()
            print("waiting for connection")
            # pylint: disable=unused-variable
            connection, sender = tcpSock.accept()  # noqa F401
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
                        code.CHALLENGE_ANSWER, encodeMessageString(self._gateway_mac)
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
