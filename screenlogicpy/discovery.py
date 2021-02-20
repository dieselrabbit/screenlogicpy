import sys
import socket
import struct
import ipaddress
from .const import (
    ScreenLogicError,
    SL_GATEWAY_IP,
    SL_GATEWAY_PORT,
    SL_GATEWAY_TYPE,
    SL_GATEWAY_SUBTYPE,
    SL_GATEWAY_NAME
)

def discover():
    broadcast = "255.255.255.255"
    port  = 1444
    addressfamily = socket.AF_INET
    wantchk = 2

    data  = struct.pack('<bbbbbbbb', 1,0,0,0, 0,0,0,0)
    udpSock = socket.socket(addressfamily, socket.SOCK_DGRAM)
    udpSock.settimeout(1)
    udpSock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    responses = []
    try:
        udpSock.sendto(data, (broadcast, port))

        while True:
            response = udpSock.recvfrom(4096)
            if response:
                responses.append(response)
            else:
                break
    except socket.timeout:
        pass
    finally:
        udpSock.close()

    #addr, port = server

    expectedfmt = "<I4BH2B"
    hosts = []
    for data, _ in responses:
        paddedfmt = expectedfmt + str(len(data)-struct.calcsize(expectedfmt)) + "s"
        chk, ip1, ip2, ip3, ip4, gatewayPort, gatewayType, gatewaySubtype, gatewayName = struct.unpack(paddedfmt, data)

        okchk = (chk == wantchk)

        if(not okchk):
            # not sure that I need to exit if "chk" isn't what we wanted.
            raise ScreenLogicError("ScreenLogic Discovery: Unexpected response checksum.")

        # make sure we got a good IP address
        receivedIP = "{}.{}.{}.{}".format(str(ip1), str(ip2), str(ip3), str(ip4))
        try:
            gatewayIP = str(ipaddress.ip_address(receivedIP))
        except ValueError as err:
            raise ScreenLogicError("ScreenLogic Discovery: Got an invalid IP address from the gateway.") from err
        except NameError as err:
            raise ScreenLogicError("ScreenLogic Discovery: Received garbage from the gateway.") from err
        except Exception as err:
            raise ScreenLogicError("ScreenLogic Discovery: Couldn't get an IP address for the gateway.") from err
        
        host = {
            SL_GATEWAY_IP: gatewayIP,
            SL_GATEWAY_PORT: gatewayPort,
            SL_GATEWAY_TYPE: gatewayType,
            SL_GATEWAY_SUBTYPE: gatewaySubtype,
            SL_GATEWAY_NAME: gatewayName.decode("utf-8").strip('\0')
        }
        hosts.append(host)
    
    return hosts #gatewayIP, gatewayPort, gatewayType, gatewaySubtype, gatewayName.decode("utf-8").strip('\0')
