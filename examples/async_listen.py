import asyncio
import logging
from pprint import pprint

from scratchpad.local_host import get_local
from screenlogicpy import ScreenLogicGateway, discovery


async def main():
    logging.basicConfig(
        format="%(asctime)s %(levelname)-8s %(message)s",
        level=logging.DEBUG,
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    hosts = await discovery.async_discover()

    if not hosts:
        hosts.append(get_local())

    if len(hosts) > 0:

        loop = asyncio.get_running_loop()

        connection_lost = loop.create_future()

        def on_connection_lost():
            connection_lost.set_result(True)

        async def data_updated():
            print("---- ** DATA UPDATED ** ----")

        async def weather_handler(message, data: dict):
            result = await gateway.async_send_message(9807)
            user = data.setdefault("user", {})
            user[9807] = result
            await data_updated()

        gateway = ScreenLogicGateway(**hosts[0])

        await gateway.async_connect(on_connection_lost)
        await gateway.async_subscribe_client(data_updated)
        # gateway.register_message_handler(9806, weather_handler, gateway.get_data())
        await gateway.async_update()

        try:
            await connection_lost
        finally:
            pprint(gateway.get_data())
            await gateway.async_disconnect()

    else:
        print("No gateways found")


asyncio.run(main())
