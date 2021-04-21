import asyncio
import pprint

from screenlogicpy import discovery

pprint.pprint(asyncio.run(discovery.async_discover()))
