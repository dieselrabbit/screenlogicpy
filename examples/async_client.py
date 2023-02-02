import asyncio
import logging
from pprint import pprint

from scratchpad.local_host import get_local
from screenlogicpy import ScreenLogicGateway, discovery
from screenlogicpy.const import CODE


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

        def status_updated_1():
            print("---- ** DATA UPDATED 1 ** ----")

        def status_updated_2():
            print("---- ** DATA UPDATED 2 ** ----")

        def chemistry_updated_1():
            print("-- ** CHEMISTRY UPDATED 1 ** -")

        def chemistry_updated_2():
            print("-- ** CHEMISTRY UPDATED 2 ** -")

        def weather_updated():
            print("--- ** WEATHER UPDATED ** ---")

        async def weather_handler(message, data: dict):
            result = await gateway.async_send_message(9807)
            weather = data.setdefault("weather", {})
            weather["_raw"] = result
            weather_updated()

        gateway = ScreenLogicGateway(**hosts[0])

        await gateway.async_connect(on_connection_lost)

        # Multiple 'clients' can subscribe to different ScreenLogic messages
        data_unsub1 = await gateway.clients.async_subscribe(
            status_updated_1, CODE.STATUS_CHANGED
        )
        data_unsub2 = await gateway.clients.async_subscribe(
            status_updated_2, CODE.STATUS_CHANGED
        )
        chem_unsub1 = await gateway.clients.async_subscribe(
            chemistry_updated_1, CODE.CHEMISTRY_CHANGED
        )
        chem_unsub2 = await gateway.clients.async_subscribe(
            chemistry_updated_2, CODE.CHEMISTRY_CHANGED
        )

        #  Can register your own custom message handler
        gateway.register_message_handler(9806, weather_handler, gateway.get_data())

        # Can update individual sections of data
        await gateway.async_update()
        await asyncio.sleep(5)
        await gateway.async_get_pumps()
        await asyncio.sleep(5)
        await gateway.async_get_scg()

        try:
            await connection_lost
        finally:
            data_unsub2()
            data_unsub1()
            chem_unsub1()
            chem_unsub2()
            pprint(gateway.get_data())
            await gateway.async_disconnect()

    else:
        print("No gateways found")


asyncio.run(main())
