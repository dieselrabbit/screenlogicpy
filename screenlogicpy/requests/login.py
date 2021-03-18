import time
import struct
import socket
from .utility import sendRecieveMessage, encodeMessageString, decodeMessageString
from ..const import code, ScreenLogicError


def create_login_message():
    # these constants are only for this message.
    schema = 348
    connectionType = 0
    clientVersion = encodeMessageString("Android")
    pid = 2
    password = "0000000000000000"  # passwd must be <= 16 chars. empty is not OK.
    passwd = encodeMessageString(password)
    fmt = "<II" + str(len(clientVersion)) + "s" + str(len(passwd)) + "sxI"
    return struct.pack(fmt, schema, connectionType, clientVersion, passwd, pid)


def create_socket(ip, port):
    tcpSock = None
    # pylint: disable=unused-variable
    for result in socket.getaddrinfo(ip, port, socket.AF_UNSPEC, socket.SOCK_STREAM):
        af, socktype, proto, canonname, sa = result
        try:
            tcpSock = socket.socket(af, socktype, proto)
        except OSError:
            tcpSock = None
            continue
        try:
            tcpSock.settimeout(5)
            tcpSock.connect(sa)
        except OSError:
            tcpSock.close()
            tcpSock = None
            continue
        break

    if not tcpSock:
        raise ScreenLogicError(f"Unable to connect to {ip}:{port}")

    return tcpSock


def gateway_connect(connected_socket):
    connectString = b"CONNECTSERVERHOST\r\n\r\n"  # as bytes, not string
    connected_socket.sendall(connectString)
    time.sleep(0.25)
    response = sendRecieveMessage(connected_socket, code.CHALLENGE_QUERY)
    mac_address = decodeMessageString(response)
    return mac_address


def gateway_login(connected_socket):
    msg = create_login_message()
    try:
        # Gateway will respond with the response code and that's all.
        _ = sendRecieveMessage(connected_socket, code.LOCALLOGIN_QUERY, msg)
        return True
    except ScreenLogicError:
        return False


def connect_to_gateway(gateway_ip, gateway_port):
    connected_socket = create_socket(gateway_ip, gateway_port)

    mac_address = gateway_connect(connected_socket)

    if gateway_login(connected_socket):
        return connected_socket, mac_address
    else:
        return None
