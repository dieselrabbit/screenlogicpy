from .requests import (
    connect_to_gateway,
    request_gateway_version,
    request_pool_button_press,
    request_pool_config,
    request_pool_lights_command,
    request_pool_status,
    request_pump_status,
    request_set_heat_mode,
    request_set_heat_setpoint,
    request_chemistry
)


class ScreenLogicGateway:
    def __init__(self, ip, port=80, gtype=0, gsubtype=0, name="Unnamed-Screenlogic-Gateway"):
        self.__ip = ip
        self.__port = port
        self.__type = gtype
        self.__subtype = gsubtype
        self.__name = name
        self.__mac = ""
        self.__connected = False
        self.__data = {}

        if (self.__ip and self.__port):
            if (self._connect()):
                self._get_config()
                self._get_status()
                self._get_pumps()
                self._get_chemistry()
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

    @property
    def mac(self):
        return self.__mac

    def update(self):
        if ((self.is_connected or self._connect()) and self.__data):
            self._get_status()
            self._get_pumps()
            self._get_chemistry()
            self._disconnect()

    def get_data(self):
        return self.__data

    def set_circuit(self, circuitID, circuitState):
        if (self._is_valid_circuit(circuitID) and self._is_valid_circuit_state(circuitState)):
            if (self.__connected or self._connect()):
                if (request_pool_button_press(self.__socket, circuitID, circuitState)):
                    self._disconnect()
                    return True
        else:
            return False

    def set_heat_temp(self, body, temp):
        if (self._is_valid_body(body) and self._is_valid_heattemp(body, temp)):
            if (self.__connected or self._connect()):
                if (request_set_heat_setpoint(self.__socket, body, temp)):
                    self._disconnect()
                    return True
        else:
            return False

    def set_heat_mode(self, body, mode):
        if (self._is_valid_body(body) and self._is_valid_heatmode(mode)):
            if (self.__connected or self._connect()):
                if (request_set_heat_mode(self.__socket, body, mode)):
                    self._disconnect()
                    return True
        else:
            return False

    def set_color_lights(self, light_command):
        if (self.__connected or self._connect()):
            if (request_pool_lights_command(self.__socket, light_command)):
                self._disconnect()
                return True
        return False

    def is_connected(self):
        return self.__connected

    def _connect(self):
        soc_mac = connect_to_gateway(self.__ip, self.__port)
        if (soc_mac):
            self.__socket, self.__mac = soc_mac
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
    
    def _get_pumps(self):
        if (self.__connected or self._connect()):
            for pID in self.__data['pumps']:
                if (self.__data['pumps'][pID]['data'] != 0):
                    request_pump_status(self.__socket, self.__data, pID)
    
    def _get_chemistry(self):
        if (self.__connected or self._connect()):
            request_chemistry(self.__socket, self.__data)

    def _is_valid_circuit(self, circuit):
        return (circuit in self.__data['circuits'])

    def _is_valid_circuit_state(self, state):
        return (state == 0 or state == 1)

    def _is_valid_body(self, body):
        return (body in self.__data['bodies'])

    def _is_valid_heatmode(self, heatmode):
        return (0 <= heatmode < 5)

    def _is_valid_heattemp(self, body, temp):
        return (self.__data['bodies'][int(body)]['min_set_point']['value'] <=
                temp <=
                self.__data['bodies'][int(body)]['max_set_point']['value'])
