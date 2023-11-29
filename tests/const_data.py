from screenlogicpy.const.common import (
    SL_GATEWAY_IP,
    SL_GATEWAY_NAME,
    SL_GATEWAY_PORT,
    SL_GATEWAY_SUBTYPE,
    SL_GATEWAY_TYPE,
)
from screenlogicpy.const.msg import CODE

FAKE_GATEWAY_ADDRESS = "127.0.0.1"
FAKE_GATEWAY_CHK = 2
FAKE_GATEWAY_DISCOVERY_PORT = 1444
FAKE_GATEWAY_MAC = "00:00:00:00:00:00"
FAKE_GATEWAY_NAME = "Fake: 00-00-00"
FAKE_GATEWAY_PORT = 6448
FAKE_GATEWAY_SUB_TYPE = 12
FAKE_GATEWAY_TYPE = 2

FAKE_CONNECT_INFO = {
    SL_GATEWAY_IP: FAKE_GATEWAY_ADDRESS,
    SL_GATEWAY_PORT: FAKE_GATEWAY_PORT,
    SL_GATEWAY_TYPE: FAKE_GATEWAY_TYPE,
    SL_GATEWAY_SUBTYPE: FAKE_GATEWAY_SUB_TYPE,
    SL_GATEWAY_NAME: FAKE_GATEWAY_NAME,
}


EXPECTED_DASHBOARD = """Discovered 'Fake: 00-00-00' at 127.0.0.1:6448
EasyTouch2 8
**************************
Pool temperature is last 59°F
Pool Heat Set Point: 83°F
Pool Heat: Off
Pool Heat Mode: Off
--------------------------
Spa temperature is last 59°F
Spa Heat Set Point: 95°F
Spa Heat: Off
Spa Heat Mode: Heater
--------------------------
**************************
 ID  STATE  NAME
--------------------------
500    Off  Spa
501    Off  Waterfall
502    Off  Pool Light
503    Off  Spa Light
504    Off  Cleaner
505     On  Pool Low
506    Off  Yard Light
507     On  Cameras
508    Off  Pool High
510    Off  Spillway
**************************"""

EXPECTED_VERBOSE_PREAMBLE = """Discovered 'Fake: 00-00-00' at 127.0.0.1:6448
EasyTouch2 8
Version: POOL: 5.2 Build 738.0 Rel
"""
