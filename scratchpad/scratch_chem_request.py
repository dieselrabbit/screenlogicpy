import socket
import json
from screenlogicpy.discovery import discover
from screenlogicpy.requests.login import connect_to_gateway
from screenlogicpy.requests.config import request_pool_config
from screenlogicpy.requests.chemistry import request_chemistry

soc, mac = connect_to_gateway('192.168.1.43', '80')
data = {}
request_pool_config(soc, data)
request_chemistry(soc, data)
soc.close()
print(json.dumps(data['chemistry']['unknown'], indent=2))
