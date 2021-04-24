import pprint

from screenlogicpy import ScreenLogicGateway, discovery

hosts = discovery.discover()

if len(hosts) > 0:
    gateway = ScreenLogicGateway(**hosts[0])
    pprint.pprint(gateway.get_data())
else:
    print("No gateways found")
