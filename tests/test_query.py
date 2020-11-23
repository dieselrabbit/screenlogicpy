import struct
import screenlogicpy
from screenlogicpy.const import code
from screenlogicpy.request.utility import sendRecieveMessage
from screenlogicpy.response.utility import getSome
from tests.test_decode import decode, toINT, decodePump

_ip, _port, _type, _subtype, _name = screenlogicpy.discovery.discover()

gateway_socket = screenlogicpy.request.login.gateway_login(_ip, _port)
_version = screenlogicpy.request.gateway.request_gateway_version(gateway_socket)
response = sendRecieveMessage(gateway_socket, code.EQUIPMENT_QUERY, struct.pack("<II", 0, 0))
gateway_socket.close()

print(response)
decode(response)
#toINT(response)
#decodePump(response)
