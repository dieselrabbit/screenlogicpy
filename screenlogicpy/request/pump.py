import struct
from .utility import sendRecieveMessage, makeMessage
from ..response.pump import decode
from ..const import code

def request_pump_status(gateway_socket, data, pumpID):
    response = sendRecieveMessage(gateway_socket, code.PUMPSTATUS_QUERY, struct.pack("<II", 0, pumpID))
    decode(response, data, pumpID)