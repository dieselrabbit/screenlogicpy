import struct
from .utility import sendRecieveMessage, makeMessage
from ..response.status import decode
from ..const import code

def request_pool_status(gateway_socket, data):
    response = sendRecieveMessage(gateway_socket, code.POOLSTATUS_QUERY, struct.pack("<I", 0))
    decode(response, data)