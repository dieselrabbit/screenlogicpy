import socket
import screenlogicpy

host = screenlogicpy.discovery.discover()
name = host['name'] if host['name'] else socket.gethostbyaddr(host['ip'])[0].split('.')[0]
gateway = screenlogicpy.ScreenLogicGateway(host['ip'], name=name)
print("{}:{}".format(gateway.ip, gateway.port), gateway.name)
data =  gateway.get_data()
print(screenlogicpy.const.CONTROLLER_HARDWARE[data['config']['controler_type']][data['config']['hardware_type']])

