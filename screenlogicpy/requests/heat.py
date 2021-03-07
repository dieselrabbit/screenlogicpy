import struct
from .utility import sendRecieveMessage
from ..const import code


def request_set_heat_setpoint(gateway_socket, body, setpoint):
    response = sendRecieveMessage(
        gateway_socket, code.SETHEATTEMP_QUERY, struct.pack("<III", 0, body, setpoint)
    )
    if response == b"":
        return True
    else:
        return False


def request_set_heat_mode(gateway_socket, body, heat_mode):
    response = sendRecieveMessage(
        gateway_socket, code.SETHEATMODE_QUERY, struct.pack("<III", 0, body, heat_mode)
    )
    if response == b"":
        return True
    else:
        return False

