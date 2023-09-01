from screenlogicpy.const.common import (
    SL_GATEWAY_IP,
    SL_GATEWAY_NAME,
    SL_GATEWAY_PORT,
    SL_GATEWAY_SUBTYPE,
    SL_GATEWAY_TYPE,
)
from screenlogicpy.const.msg import CODE

from .data_sets import TESTING_DATA_COLLECTION as TDC


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

ASYNC_SL_RESPONSES = {
    CODE.VERSION_QUERY: TDC.version.raw,
    CODE.CTRLCONFIG_QUERY: TDC.config.raw,
    CODE.POOLSTATUS_QUERY: TDC.status.raw,
    CODE.STATUS_CHANGED: TDC.status.raw,
    CODE.PUMPSTATUS_QUERY: TDC.pumps[0].raw,
    CODE.CHEMISTRY_QUERY: TDC.chemistry.raw,
    CODE.CHEMISTRY_CHANGED: TDC.chemistry.raw,
    CODE.SCGCONFIG_QUERY: TDC.scg.raw,
    CODE.COLOR_UPDATE: TDC.color[7].raw,
    CODE.BUTTONPRESS_QUERY: b"",
    CODE.LIGHTCOMMAND_QUERY: b"",
    CODE.SETHEATMODE_QUERY: b"",
    CODE.SETHEATTEMP_QUERY: b"",
    CODE.SETSCG_QUERY: b"",
    CODE.SETCHEMDATA_QUERY: b"",
    CODE.ADD_CLIENT_QUERY: b"",
    CODE.REMOVE_CLIENT_QUERY: b"",
    CODE.PING_QUERY: b"",
}

EXPECTED_DASHBOARD = """Discovered 'Fake: 00-00-00' at 127.0.0.1:6448
EasyTouch2 8
**************************
Pool temperature is last 56°F
Pool Heat Set Point: 86°F
Pool Heat: Off
Pool Heat Mode: Off
--------------------------
Spa temperature is last 97°F
Spa Heat Set Point: 97°F
Spa Heat: Off
Spa Heat Mode: Heater
--------------------------
**************************
 ID  STATE  NAME
--------------------------
500    Off  Spa
501    Off  Waterfall
502     On  Pool Light
503     On  Spa Light
504     On  Cleaner
505    Off  Pool Low
506     On  Yard Light
507    Off  Aux 6
508    Off  Pool High
510    Off  Feature 1
511    Off  Feature 2
512    Off  Feature 3
513    Off  Feature 4
514    Off  Feature 5
515    Off  Feature 6
516    Off  Feature 7
517    Off  Feature 8
519    Off  AuxEx
**************************"""

EXPECTED_VERBOSE_PREAMBLE = """Discovered 'Fake: 00-00-00' at 127.0.0.1:6448
EasyTouch2 8
Version: POOL: 5.2 Build 736.0 Rel
"""
