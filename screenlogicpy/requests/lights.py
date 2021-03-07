import struct
from .utility import sendRecieveMessage
from ..const import code


def request_pool_lights_command(gateway_socket, light_command):
    response = sendRecieveMessage(
        gateway_socket, code.LIGHTCOMMAND_QUERY, struct.pack("<III", 0, light_command)
    )
    if response == b"":
        return True
    else:
        return False
