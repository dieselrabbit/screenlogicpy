import struct
import screenlogicpy
from screenlogicpy.const import code
from screenlogicpy.request.utility import sendRecieveMessage
from screenlogicpy.response.utility import getSome
#from tests.test_decode import decode, toINT, decodePump
from screenlogicpy.response.equipment import decode

host = screenlogicpy.discovery.discover()
try:
    gateway_socket = screenlogicpy.request.login.gateway_login(host['ip'], host['port'])
    _version = screenlogicpy.request.gateway.request_gateway_version(gateway_socket)
    response = sendRecieveMessage(gateway_socket, code.EQUIPMENT_QUERY, struct.pack("<2I", 0, 0))
    print(response)
except screenlogicpy.ScreenLogicError as error:
    print(error)
finally:
    gateway_socket.close()

testData = {}
decode(response, testData)
#toINT(response)
#decodePump(response)
print(testData)
