import asyncio
import pprint

from screenlogicpy import ScreenLogicGateway, discovery


async def main():
    hosts = await discovery.async_discover()

    if len(hosts) > 0:
        gateway = ScreenLogicGateway(**hosts[0])
        await gateway.async_connect()
        await gateway.async_update()
        await gateway.async_disconnect()
        pprint.pprint(gateway.get_data())
    else:
        print("No gateways found")


asyncio.run(main())
