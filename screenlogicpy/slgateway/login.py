import os
import socket
from slgateway.msgutil import *
from slgateway.const import code

def create_login_message():
  # these constants are only for this message. keep them here.
  schema = 348
  connectionType = 0
  clientVersion = makeMessageString('Android')
  pid  = 2 #os.getpid() #random.randint(2,100)
  password = "0000000000000000" # passwd must be <= 16 chars. empty is not OK.
  passwd = makeMessageString(password)
  fmt = "<II" + str(len(clientVersion)) + "s" + str(len(passwd)) + "sxI"
  return struct.pack(fmt, schema, connectionType, clientVersion, passwd, pid)

def gateway_login(gateway_ip, gateway_port):
    tcpSock = None
    for result in socket.getaddrinfo(gateway_ip, gateway_port, socket.AF_UNSPEC, socket.SOCK_STREAM):
        af, socktype, proto, canonname, sa = result
        try:
            tcpSock = socket.socket(af, socktype, proto)
        except OSError as msg:
            tcpSock = None
            continue
        try:
            tcpSock.settimeout(10)
            tcpSock.connect(sa)
        except OSError as msg:
            tcpSock.close()
            tcpSock = None
            continue
        break

    if tcpSock is None:
        sys.stderr.write("ERROR: {}: Could not open socket to gateway host.\n".format(me))
        return false
        #sys.exit(10)

    connectString = b'CONNECTSERVERHOST\r\n\r\n'  # as bytes, not string
    tcpSock.sendall(connectString)

    # tx/rx challenge  (?)  (gateway returns its mac address in the form 01-23-45-AB-CD-EF)
    tcpSock.sendall(makeMessage(code.CHALLENGE_QUERY))
    data = tcpSock.recv(48)
    if not data:
        sys.stderr.write("WARNING: {}: no {} data received.\n".format(me, "CHALLENGE_ANSWER"))
    rcvcode, data = takeMessage(data)
    if(rcvcode != code.CHALLENGE_ANSWER):
        sys.stderr.write("WARNING: {}: rcvCode2({}) != {}.\n".format(me, CHALLENGE_ANSWER))
        return false
        #sys.exit(10)


    # now that we've "connected" and "challenged," we can "login." None of these things
    # actually do anything, but they are required.
    msg = create_login_message()
    tcpSock.sendall(makeMessage(code.LOCALLOGIN_QUERY, msg))
    data = tcpSock.recv(48)
    if not data:
        sys.stderr.write("WARNING: {}: no {} data received.\n".format(me, "LOCALLOGIN_ANSWER"))
    rcvCode, data = takeMessage(data)
    if(rcvCode != code.LOCALLOGIN_ANSWER):
        sys.stderr.write("WARNING: {}: rcvCode({}) != {}.\n".format(me, rcvCode, code.LOCALLOGIN_ANSWER))
        return false
        #sys.exit(10)
    # response should be empty
    return tcpSock
