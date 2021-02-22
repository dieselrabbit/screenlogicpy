import screenlogicpy

hosts = screenlogicpy.discovery.discover()
if len(hosts) > 0:
    gateway = screenlogicpy.ScreenLogicGateway(**hosts[0])
    print(f"{gateway.ip}:{gateway.port} {gateway.name}")
    data =  gateway.get_data()
    print(screenlogicpy.const.CONTROLLER_HARDWARE[data['config']['controler_type']][data['config']['hardware_type']])
else:
    print("No gateways found")

