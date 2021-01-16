import struct
import screenlogicpy
from screenlogicpy.const import code
from screenlogicpy.requests.utility import sendRecieveMessage, getSome
#from tests.test_decode import decode, toINT, decodePump
from screenlogicpy.requests.equipment import decode_equipment_config

host = screenlogicpy.discovery.discover()
try:
    gateway_socket = screenlogicpy.requests.login.gateway_login(host['ip'], host['port'])
    _version = screenlogicpy.requests.gateway.request_gateway_version(gateway_socket)
    response = sendRecieveMessage(gateway_socket, code.EQUIPMENT_QUERY, struct.pack("<2I", 0, 0))
    print(response)
except screenlogicpy.ScreenLogicError as error:
    print(error)
finally:
    gateway_socket.close()

testData = {}
decode_equipment_config(response, testData)
#toINT(response)
#decodePump(response)
print(testData)
