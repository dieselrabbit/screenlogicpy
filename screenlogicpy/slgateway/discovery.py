import sys
import socket
import struct
import ipaddress
from slgateway.const import me

def discovery(self, verbose=False):
    broadcast = "255.255.255.255"
    port  = 1444
    addressfamily = socket.AF_INET
    wantchk = 2

    data  = struct.pack('<bbbbbbbb', 1,0,0,0, 0,0,0,0)
    try:
        udpSock = socket.socket(addressfamily, socket.SOCK_DGRAM)
        udpSock.settimeout(5)
        udpSock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    except:
        sys.stderr.write("ERROR: {}: Socket setup failed.\n".format(me))
        return False
        #sys.exit(1)


    if(verbose):
        print("Broadcasting for Pentair systems...")
    try:
        udpSock.sendto(data, (broadcast, port))
    except:
        sys.stderr.write("ERROR: {}: Socket broadcast failed.\n".format(me))
        return False
        #sys.exit(2) 

    if(verbose):
        print("Waiting for a response...")
    try:
        data, server = udpSock.recvfrom(4096)
    except:
        sys.stderr.write("ERROR: {}: Socket recieve failed.\n".format(me))
        return False
        #sys.exit(3)
    try:
        udpSock.close()
    except:
        sys.stderr.write("ERROR: {}: Socket close failed.\n".format(me))
        return False
        #sys.exit(4)

    if(verbose):
        addr, port = server
        print("INFO: {}: Received a response from {}:{}".format(me(), addr, port))

    expectedfmt = "<I4BH2B"
    paddedfmt = expectedfmt + str(len(data)-struct.calcsize(expectedfmt)) + "s"
    try:
        chk, ip1, ip2, ip3, ip4, gatewayPort, gatewayType, gatewaySubtype, gatewayName = struct.unpack(paddedfmt, data)
    except struct.error as err:
        print("ERROR: {}: received unpackable data from the gateway: \"{}\"".format(me, err))
        return False
        #sys.exit(6)

    okchk = (chk == wantchk)

    if(not okchk):
        # not sure that I need to exit if "chk" isn't what we wanted.
        sys.stderr.write("ERROR: {}: Incorrect checksum. Wanted '{}', got '{}'\n".format(me, wantchk, chk))
        return False
        #sys.exit(7)

    # make sure we got a good IP address
    receivedIP = "{}.{}.{}.{}".format(str(ip1), str(ip2), str(ip3), str(ip4))
    try:
        gatewayIP = str(ipaddress.ip_address(receivedIP))
    except ValueError as err:
        print("ERROR: {}: got an invalid IP address from the gateway:\n  \"{}\"".format(me, err))
        return False
        #sys.exit(8)
    except NameError as err:
        print("ERROR: {}: received garbage from the gateway:\n  \"{}\"".format(me, err))
        return False
        #sys.exit(9)
    except:
        print("ERROR: {}: Couldn't get an IP address for the gateway.".format(me, err))
        return False
        #sys.exit(10)
  
    if(verbose):
        print("gatewayIP: '{}'".format(gatewayIP))
        print("gatewayPort: '{}'".format(gatewayPort))
        print("gatewayType: '{}'".format(gatewayType))
        print("gatewaySubtype: '{}'".format(gatewaySubtype))
        print("gatewayName: '{}'".format(gatewayName.decode("utf-8").strip('\0')))

    return gatewayIP, gatewayPort, gatewayType, gatewaySubtype, gatewayName.decode("utf-8").strip('\0'), okchk
