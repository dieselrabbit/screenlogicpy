import time
import socket
from . discovery import discover
from . login import gateway_login
from . request import request_gateway, request_pool_config, \
     request_pool_status, request_pool_button_press, request_set_heat_setpoint, \
     request_set_heat_mode
from . const import mapping

class gateway:
    def __init__(self, verbose=False, ip=None, port=None):
        self.__ip = ip
        self.__port = port
        self.__connected = False
        self.__data = {}
        

        # Try to discover gateway
        if (not self.__ip):
            self.__ip, self.__port, self.__type,\
            self.__subtype, self.__name, okchk = discover(verbose)

        if (self.__ip):
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
            self._is_valid_heattemp(body, temp)):
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
