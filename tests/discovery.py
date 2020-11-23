import screenlogicpy

_ip, _port, _type, _subtype, _name = screenlogicpy.discovery.discover()
gateway = screenlogicpy.ScreenLogicGateway(_ip)
print("{}:{}".format(gateway.ip, gateway.port), gateway.name)

