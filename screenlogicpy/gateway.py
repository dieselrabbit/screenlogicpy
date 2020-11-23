import time
import socket
from .request.login import gateway_login
from .request.gateway import request_gateway_version
from .request.config import request_pool_config
from .request.status import request_pool_status
from .request.button import request_pool_button_press
from .request.heat import request_set_heat_setpoint, request_set_heat_mode
from .const import HEAT_MODE, ScreenLogicError

class GatewayInfo:
    pass

class ScreenLogicGateway:
    def __init__(self, ip, port=80, gtype=0, gsubtype=0, name=""):
        self.__ip = ip
        self.__port = port
        self.__type = gtype
        self.__subtype = gsubtype
        self.__name = name
        self.__connected = False
        self.__data = {}
        
        if (self.__ip and self.__port):
            if (self._connect()):
                self._get_config()
                self._get_status()
                self._disconnect()
        else:
            raise ValueError("Invalid ip or port")
    
    @property
    def ip(self):
        return self.__ip

    @property
    def port(self):
        return self.__port

    @property
    def name(self):
        return self.__name

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
                if (request_pool_button_press(self.__socket, circuitID, circuitState)):
                    self._disconnect()
                    return True
        else:
            return False

    def set_heat_temp(self, body, temp):
        if (self._is_valid_body(body) and
            self._is_valid_heattemp(body, temp)):
            if (self.__connected or self._connect()):
                if (request_set_heat_setpoint(self.__socket, body, temp)):
                    self._disconnect()
                    return True
        else:
            return False

    def set_heat_mode(self, body, mode):
        if (self._is_valid_body(body) and
            self._is_valid_heatmode(mode)):
            if (self.__connected or self._connect()):
                if (request_set_heat_mode(self.__socket, body, mode)):
                    self._disconnect()
                    return True
        else:
            return False

    def is_connected(self):
        return self.__connected


    def _connect(self):
        self.__socket = gateway_login(self.__ip, self.__port)
        if (self.__socket):
            self.__version = ""
            self.__version = request_gateway_version(self.__socket)
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
        return (0 <= heatmode < 5)

    def _is_valid_heattemp(self, body, temp):
        return (self.__data['config']['min_set_point']['value'][int(body)] <=
                temp <=
                self.__data['config']['max_set_point']['value'][int(body)])
