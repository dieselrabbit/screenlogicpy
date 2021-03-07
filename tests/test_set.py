import time
from screenlogicpy import ScreenLogicGateway, discovery, const

# TODO: Rewrite as an actual test

# # Choose a 'safe' circuit like a light
cir_num = 508

hosts = discovery.discover()
if len(hosts) > 0:
    gateway = ScreenLogicGateway(**hosts[0])
    print(f"{gateway.ip}:{gateway.port} {gateway.name}")
    print(gateway.set_circuit(cir_num, const.ON_OFF.ON))
    time.sleep(10)
    print(gateway.set_circuit(cir_num, const.ON_OFF.OFF))
else:
    print("No gateways found")
