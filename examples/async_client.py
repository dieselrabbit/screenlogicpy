import asyncio
import logging
from pprint import pprint

from screenlogicpy import ScreenLogicGateway, discovery
from screenlogicpy.const import CODE


async def main():
    logging.basicConfig(
        format="%(asctime)s %(levelname)-8s %(message)s",
        level=logging.DEBUG,
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    hosts = await discovery.async_discover()

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

        gateway = ScreenLogicGateway()

        await gateway.async_connect(
            **hosts[0], connection_closed_callback=on_connection_lost
        )

        # Multiple 'clients' can subscribe to different ScreenLogic messages
        data_unsub1 = await gateway.async_subscribe_client(
            status_updated_1, CODE.STATUS_CHANGED
        )
        data_unsub2 = await gateway.async_subscribe_client(
            status_updated_2, CODE.STATUS_CHANGED
        )
        chem_unsub1 = await gateway.async_subscribe_client(
            chemistry_updated_1, CODE.CHEMISTRY_CHANGED
        )
        chem_unsub2 = await gateway.async_subscribe_client(
            chemistry_updated_2, CODE.CHEMISTRY_CHANGED
        )

        # Can update individual sections of data. NOTE: Some expected
        # data keys may not be present until all data has been updated at
        # least once. ex. circuit state in data["circuits"][500]["value"]
        await gateway.async_get_pumps()
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
