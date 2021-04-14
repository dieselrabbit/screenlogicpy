import struct
from .utility import sendReceiveMessage
from ..const import code


def request_pool_lights_command(gateway_socket, light_command):
    response = sendReceiveMessage(
        gateway_socket, code.LIGHTCOMMAND_QUERY, struct.pack("<II", 0, light_command)
    )
    if response == b"":
        return True
    else:
        return False
