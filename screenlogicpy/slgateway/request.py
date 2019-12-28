import socket
from slgateway.msgutil import *
from slgateway.const import code
from slgateway.decode_response.config import decode_pool_config_response
from slgateway.decode_response.status import decode_pool_status_response

def request_gateway(gateway_socket):
    gateway_socket.sendall(makeMessage(code.VERSION_QUERY))
    data = gateway_socket.recv(480)
    if not data:
        sys.stderr.write("WARNING: {}: no {} data received.\n".format(me, "VERSION_ANSWER"))
    rcvcode, buff = takeMessage(data)
    if (rcvcode != code.VERSION_ANSWER):
        sys.stderr.write("WARNING: {}: rcvCode({}) != {}.\n".format(me, rcvCode2, code.VERSION_ANSWER))
        return False
        #sys.exit(10)
    return getMessageString(buff)

def request_pool_config(gateway_socket, data):
    gateway_socket.sendall(makeMessage(code.CTRLCONFIG_QUERY, struct.pack("<2I", 0, 0)))
    rcvcode, buff = takeMessage(gateway_socket.recv(1024))
    if (rcvcode != code.CTRLCONFIG_ANSWER):
        sys.stderr.write("WARNING: {}: rcvCode({}) != {}.\n".format(me, rcvcode, code.CTRLCONFIG_ANSWER))
        return False
        #sys.exit(11)
    decode_pool_config_response(buff, data)

def request_pool_status(gateway_socket, data):
    gateway_socket.sendall(makeMessage(code.POOLSTATUS_QUERY, struct.pack("<I", 0)))
    rcvcode, buff = takeMessage(gateway_socket.recv(1024))
    if (rcvcode != code.POOLSTATUS_ANSWER):
        sys.stderr.write("WARNING: {}: rcvCode({}) != {}.\n".format(me, rcvCode, code.POOLSTATUS_ANSWER))
        return False
        #sys.exit(11)
    decode_pool_status_response(buff, data)

def request_pool_button_press(gateway_socket, circuit_id, circuit_state):
    gateway_socket.sendall(makeMessage(code.BUTTONPRESS_QUERY, struct.pack("<III", 0, circuit_id, circuit_state)))
    rcvcode, buff = takeMessage(gateway_socket.recv(1024))
    if (rcvcode != code.BUTTONPRESS_ANSWER):
        sys.stderr.write("WARNING: {}: rcvCode({}) != {}.\n".format(me, rcvCode, code.BUTTONPRESS_ANSWER))
        return False
        #sys.exit(11)
    #print(rcvcode)
    return True

def request_set_heat_setpoint(gateway_socket, body, setpoint):
    gateway_socket.sendall(makeMessage(code.SETHEATTEMP_QUERY, struct.pack("<III", 0, body, setpoint)))
    rcvcode, buff = takeMessage(gateway_socket.recv(1024))
    if (rcvcode != code.SETHEATTEMP_ANSWER):
        sys.stderr.write("WARNING: {}: rcvCode({}) != {}.\n".format(me, rcvCode, code.BUTTONPRESS_ANSWER))
        return False
        #sys.exit(11)
    #print(rcvcode)
    return True

def request_set_heat_mode(gateway_socket, body, heat_mode):
    gateway_socket.sendall(makeMessage(code.SETHEATMODE_QUERY, struct.pack("<III", 0, body, heat_mode)))
    rcvcode, buff = takeMessage(gateway_socket.recv(1024))
    if (rcvcode != code.SETHEATMODE_ANSWER):
        sys.stderr.write("WARNING: {}: rcvCode({}) != {}.\n".format(me, rcvCode, code.BUTTONPRESS_ANSWER))
        return False
        #sys.exit(11)
    #print(rcvcode)
    return True
