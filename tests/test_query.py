import struct
import screenlogicpy
from screenlogicpy.const import code
from screenlogicpy.requests.utility import sendRecieveMessage, getSome
from tests.test_decode import decode

#host = screenlogicpy.discovery.discover()
host = {'ip': 'xxx.xxx.xxx.xxx', 'port':'80'}
try:
    gateway_socket, gateway_mac = screenlogicpy.requests.login.connect_to_gateway(host['ip'], host['port'])
    _version = screenlogicpy.requests.gateway.request_gateway_version(gateway_socket)
    response = sendRecieveMessage(gateway_socket, code.CHEMISTRY_QUERY, struct.pack("<I", 0))
    print(response)
except screenlogicpy.ScreenLogicError as error:
    print(error)
finally:
    gateway_socket.close()

#toINT(response)
#decodePump(response)
#print(testData)
decode(response)
