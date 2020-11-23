import screenlogicpy
from screenlogicpy import const

_ip, _port, _type, _subtype, _name = screenlogicpy.discovery.discover()
print(_name)
gateway = screenlogicpy.ScreenLogicGateway(_ip, _port, _type, _subtype, _name)
print(gateway.set_circuit(508, const.ON_OFF.ON))
print(gateway.set_heat_mode(const.BODY_TYPE.POOL, const.HEAT_MODE.HEATER))
