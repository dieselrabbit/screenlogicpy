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

        gateway = ScreenLogicGateway(**hosts[0])

        async def weather_handler(message, data: dict):
            # Sends a request for the actual weather forecast, returns the reply.
            result = await gateway.async_send_message(CODE.WEATHER_FORECAST_QUERY)
            weather = data.setdefault("weather", {})
            weather["_raw"] = result

        await gateway.async_connect(on_connection_lost)

        # Registers the method 'weather_handler' to be called when a weather forecast
        # changed message is received.
        gateway.register_message_handler(
            CODE.WEATHER_FORECAST_CHANGED, weather_handler, gateway.get_data()
        )

        # Updates all pool data. Optional.
        await gateway.async_update()

        try:
            await connection_lost
        finally:
            pprint(gateway.get_data())
            await gateway.async_disconnect()

    else:
        print("No gateways found")


asyncio.run(main())
