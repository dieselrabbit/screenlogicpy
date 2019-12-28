import sys
import time
import json
import socket
import argparse
from slgateway.discovery import discovery
from slgateway.login import gateway_login
from slgateway.request import request_gateway, request_pool_config, \
                                request_pool_status, request_pool_button_press
from slgateway.const import mapping


# TODO: Rename project

class slgateway:
    def __init__(self, verbose=False, ip=None, port=None):
        self.__ip = ip
        self.__port = port
        self.__connected = False
        self.__data = {}
        

        # Try to discover gateway
        if (not self.__ip):
            self.__ip, self.__port, self.__type,\
            self.__subtype, self.__name, okchk = discovery(verbose)

        if (self.__ip):
            pass
            if (self._connect()):
                self._get_config()
                self._get_status()
                self._disconnect()


    def update(self):
        if ((self.is_connected or self._connect()) and self.__data):
            self._get_status()
            self._disconnect()

    def get_data(self):
        return self.__data

    def set_circuit(self, circuitID, circuitState):
        if (self._is_valid_circuit(circuitID) and
            self._is_valid_circuit_state(circuitState)):
            if (self.__connected or self._connect()):
                return request_pool_button_press(self.__socket, circuitID, circuitState)
        else:
            return False

    def set_heat_temp(self, body, temp):
        if (self._is_valid_body(body) and
            self._is_valid_heattemp(temp)):
            if (self.__connected or self._connect()):
                return request_set_heat_setpoint(self.__socket, body, temp)
        else:
            return False

    def set_heat_mode(self, body, mode):
        if (self._is_valid_body(body) and
            self._is_valid_heatmode(mode)):
            if (self.__connected or self._connect()):
                return request_set_heat_mode(self.__socket, body, mode)
        else:
            return False

    def is_connected(self):
        return self.__connected


    def _connect(self):
        self.__socket = gateway_login(self.__ip, self.__port)
        if (self.__socket):
            self.__version = ""
            self.__version = request_gateway(self.__socket)
            if (self.__version):
                self.__connected = True
                return True
        return False

    def _disconnect(self):
        if (self.__socket):
            self.__socket.close()
        self.__connected = False

    def _get_config(self):
        if (self.__connected or self._connect()):
            request_pool_config(self.__socket, self.__data)

    def _get_status(self):
        if (self.__connected or self._connect()):
            request_pool_status(self.__socket, self.__data)

    def _is_valid_circuit(self, circuit):
        return (circuit in self.__data['circuits'])

    def _is_valid_circuit_state(self, state):
        return (state == 0 or state == 1)

    def _is_valid_body(self, body):
        return (body in self.__data['bodies'])

    def _is_valid_heatmode(self, heatmode):
        return (0 <= heatmode < len(mapping.HEAT_MODE))

    def _is_valid_heattemp(self, body, temp):
        return (self.__data['config']['min_set_point']['value'][int(body)] <=
                temp <=
                self.__data['config']['max_set_point']['value'][int(body)])



if __name__ == "__main__":
    verbose = False
    host = None
    port = None
    parser = argparse.ArgumentParser(
        description="Interface for Pentair Screenlogic gateway")
    parser.add_argument('-v','--verbose', action='store_true')
    parser.add_argument('-i','--ip')
    parser.add_argument('-p','--port')
    parser.add_argument('-g','--getcircuit', metavar="CIRCUIT", type=int)
    parser.add_argument('-s','--setcircuit', nargs=2, metavar=("CIRCUIT", "STATE"))
    parser.add_argument('-m','--heatmode', nargs=2, metavar=("BODY", "HEATMODE"))
    parser.add_argument('-t','--heattemp', nargs=2, metavar=("BODY", "HEATTEMP"))
    parser.add_argument('-j','--json', action='store_true')
    args = parser.parse_args()

    gateway = slgateway(args.verbose, args.ip, args.port)
    if ('config' not in gateway.get_data()):
        sys.exit(1)

    if (args.getcircuit):
        print(
            mapping.ON_OFF[
                int(gateway.get_data()['circuits'][int(args.getcircuit)]['value'])
                ]
            )
        sys.exit()
    elif (args.setcircuit):
        state = 0
        if (len(args.setcircuit) > 1 and 
            (args.setcircuit[1] == '1' or args.setcircuit[1].lower() == 'on')):
            state = 1
        if (gateway.set_circuit(int(args.setcircuit[0]), state)):
            gateway.update()
            print(
                mapping.ON_OFF[
                    int(gateway.get_data()['circuits']
                        [int(args.setcircuit[0])]['value'])
                    ]
                )
            sys.exit()
        else:
            sys.exit(1)
    elif (args.heatmode):
        if (len(args.heatmode) = 2 and
            args.heatmode[0] in gateway.get_data()['bodies'] and
            ( 0 <= args.heatmode[1] < len(mapping.HEAT_MODE))):
            if (gateway.set_heat_mode(
                int(args.heatmode[0]), int(args.heatmode[1])):
                gateway.update()
                print(mapping.BODY_TYPE
                      [gateway.get_data()['bodies']
                       [int(args.heatmode[0])]['body_type']['value']],
                      mapping.HEAT_MODE
                      [gateway.get_data()['bodies']
                       [int(args.heatmode[0])]['heat_mode']['value']])
            sys.exit()
        else:
            sys.exit(1)
    elif (args.heattemp):
        
    else:
        print(json.dumps(gateway.get_data(), indent=2))
        sys.exit()
