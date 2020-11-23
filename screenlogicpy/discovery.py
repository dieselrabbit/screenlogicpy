import sys
import socket
import struct
import ipaddress
from .const import ScreenLogicError

def discover():
    broadcast = "255.255.255.255"
    port  = 1444
    addressfamily = socket.AF_INET
    wantchk = 2

    data  = struct.pack('<bbbbbbbb', 1,0,0,0, 0,0,0,0)
    udpSock = socket.socket(addressfamily, socket.SOCK_DGRAM)
    udpSock.settimeout(5)
    udpSock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    try:
        udpSock.sendto(data, (broadcast, port))
        #pylint: disable=unused-variable
        data, server = udpSock.recvfrom(4096)
    except socket.timeout as err:
        raise ScreenLogicError("ScreenLogic Discovery: No Screenlogic Gateways found.") from err
    finally:
        udpSock.close()

    #addr, port = server

    expectedfmt = "<I4BH2B"
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
        'ip': gatewayIP,
        'port': gatewayPort,
        'type': gatewayType,
        'subtype': gatewaySubtype,
        'name': gatewayName.decode("utf-8").strip('\0')
    }
    
    return host #gatewayIP, gatewayPort, gatewayType, gatewaySubtype, gatewayName.decode("utf-8").strip('\0')
