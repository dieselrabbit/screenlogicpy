import struct
from .utility import sendRecieveMessage, makeMessage
from ..response.config import decode
from ..const import code

def request_pool_config(gateway_socket, data):
    response = sendRecieveMessage(gateway_socket, code.CTRLCONFIG_QUERY, struct.pack("<2I", 0, 0))
    decode(response, data)
