import struct
from .utility import sendRecieveMessage
from ..const import code


def request_pool_button_press(gateway_socket, circuit_id, circuit_state):
    response = sendRecieveMessage(
        gateway_socket,
        code.BUTTONPRESS_QUERY,
        struct.pack("<III", 0, circuit_id, circuit_state),
    )
    if response == b"":
        return True
    else:
        return False
