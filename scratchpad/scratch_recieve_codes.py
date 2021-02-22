import struct
import time
import socket
from datetime import datetime
from screenlogicpy.requests.login import create_socket, gateway_connect, gateway_login
from screenlogicpy.requests.utility import takeMessage, makeMessage
from screenlogicpy.const import code

soc = create_socket('192.168.1.43', '80')
mac = gateway_connect(soc)
gateway_login(soc)
code = code.POOLSTATUS_QUERY
message = struct.pack("<I", 0)
while True:
    try:
        print(datetime.now().strftime('%H:%M:%S'))
        soc.sendall(makeMessage(code, message))
        while True:
            data = soc.recv(1024)
            if not data:
                print("No data recieved from socket")
                break
            rcvCode, buff = takeMessage(data)
            if (rcvCode == (code + 1)):
                print('.')
                break
            else:
                print('Recieved unexpected reply: {}'.format(rcvCode))
                print(buff)
    except socket.timeout:
        break
    time.sleep(10.0)