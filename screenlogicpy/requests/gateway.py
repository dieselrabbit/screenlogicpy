from .utility import sendReceiveMessage, decodeMessageString
from ..const import code


def request_gateway_version(gateway_socket):
    response = sendReceiveMessage(gateway_socket, code.VERSION_QUERY)
    return decodeMessageString(response)
