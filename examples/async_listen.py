import asyncio
import logging
from pprint import pprint

from screenlogicpy import ScreenLogicGateway, discovery
from scratchpad.local_host import get_local


async def main():
    logging.basicConfig(level=logging.DEBUG)
    hosts = await discovery.async_discover()
    if len(hosts) == 0:
        hosts.append(get_local())

    if len(hosts) > 0:

        loop = asyncio.get_running_loop()

        connection_lost = loop.create_future()

        def on_connection_lost():
            connection_lost.set_result()

        async def weather_handler(message, data: dict):
            result = await gateway.async_send_message(9807)
            user = data.setdefault("user", {})
            user[9807] = result

        gateway = ScreenLogicGateway(**hosts[0])

        await gateway.async_connect(on_connection_lost)
        gateway.register_message_handler(9806, weather_handler, gateway.get_data())
        await gateway.async_update()

        try:
            await connection_lost
        finally:
            pprint(gateway.get_data())
            await gateway.async_disconnect()

    else:
        print("No gateways found")


asyncio.run(main())