import struct

from screenlogicpy.const.common import (
    SL_GATEWAY_IP,
    SL_GATEWAY_NAME,
    SL_GATEWAY_PORT,
    SL_GATEWAY_SUBTYPE,
    SL_GATEWAY_TYPE,
)
from screenlogicpy.const.msg import CODE
from screenlogicpy.requests.utility import encodeMessageString

FAKE_GATEWAY_ADDRESS = "127.0.0.1"
FAKE_GATEWAY_CHK = 2
FAKE_GATEWAY_DISCOVERY_PORT = 1444
FAKE_GATEWAY_MAC = "00:00:00:00:00:00"
FAKE_GATEWAY_NAME = "Fake: 00-00-00"
FAKE_GATEWAY_PORT = 6448
FAKE_GATEWAY_SUB_TYPE = 12
FAKE_GATEWAY_TYPE = 2
FAKE_GATEWAY_VERSION = "fake 0.0.3"


FAKE_CONNECT_INFO = {
    SL_GATEWAY_IP: FAKE_GATEWAY_ADDRESS,
    SL_GATEWAY_PORT: FAKE_GATEWAY_PORT,
    SL_GATEWAY_TYPE: FAKE_GATEWAY_TYPE,
    SL_GATEWAY_SUBTYPE: FAKE_GATEWAY_SUB_TYPE,
    SL_GATEWAY_NAME: FAKE_GATEWAY_NAME,
}

FAKE_VERSION_RESPONSE = b"\x19\x00\x00\x00POOL: 5.2 Build 736.0 Rel\x00\x00\x00\x02\x00\x00\x00\x05\x00\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00\x0c\x00\x00\x00"
FAKE_CONFIG_RESPONSE = b"d\x00\x00\x00(h(h\x00\r\x00\x008\x80\xff\xff\x0e\x00\x00\x00Water Features\x00\x00\x12\x00\x00\x00\xf4\x01\x00\x00\x03\x00\x00\x00Spa\x00G\x01\x01\x01\x00\x00\x00\x01\xd0\x02\x00\x00\xf5\x01\x00\x00\t\x00\x00\x00Waterfall\x00\x00\x00U\x00\x02\x00\x00\x00\x00\x02\xd0\x02\x00\x00\xf6\x01\x00\x00\n\x00\x00\x00Pool Light\x00\x00>\x10\x03\x00\x02\x00\n\x03\xd0\x02\x00\x00\xf7\x01\x00\x00\t\x00\x00\x00Spa Light\x00\x00\x00I\x10\x03\x00\x07\x00\n\x04\xd0\x02\x00\x00\xf8\x01\x00\x00\x07\x00\x00\x00Cleaner\x00\x15\x00\x02\x00\x00\x00\x00\x05\xd0\x02\x00\x00\xf9\x01\x00\x00\x08\x00\x00\x00Pool Low?\x02\x00\x01\x00\x00\x00\x06\xd0\x02\x00\x00\xfa\x01\x00\x00\n\x00\x00\x00Yard Light\x00\x00[\x00\x02\x00\x00\x00\x00\x07\xd0\x02\x00\x00\xfb\x01\x00\x00\x05\x00\x00\x00Aux 6\x00\x00\x00\x07\x00\x02\x00\x00\x00\x00\x08\xd0\x02\x00\x00\xfc\x01\x00\x00\t\x00\x00\x00Pool High\x00\x00\x00=\x05\x02\x00\x00\x00\x00\t\xd0\x02\x00\x00\xfe\x01\x00\x00\t\x00\x00\x00Feature 1\x00\x00\x00]\x00\x02\x00\x00\x00\x00\x0b\xd0\x02\x00\x00\xff\x01\x00\x00\t\x00\x00\x00Feature 2\x00\x00\x00^\x00\x02\x00\x00\x00\x00\x0c\xd0\x02\x00\x00\x00\x02\x00\x00\t\x00\x00\x00Feature 3\x00\x00\x00_\x00\x02\x00\x00\x00\x00\r\xd0\x02\x00\x00\x01\x02\x00\x00\t\x00\x00\x00Feature 4\x00\x00\x00`\x00\x02\x00\x00\x00\x00\x0e\xd0\x02\x00\x00\x02\x02\x00\x00\t\x00\x00\x00Feature 5\x00\x00\x00a\x00\x02\x00\x00\x00\x00\x0f\xd0\x02\x00\x00\x03\x02\x00\x00\t\x00\x00\x00Feature 6\x00\x00\x00b\x00\x02\x00\x00\x00\x00\x10\xd0\x02\x00\x00\x04\x02\x00\x00\t\x00\x00\x00Feature 7\x00\x00\x00c\x00\x02\x00\x00\x00\x00\x11\xd0\x02\x00\x00\x05\x02\x00\x00\t\x00\x00\x00Feature 8\x00\x00\x00d\x00\x02\x00\x00\x00\x00\x12\xd0\x02\x00\x00\x07\x02\x00\x00\x05\x00\x00\x00AuxEx\x00\x00\x00\\\x00\x02\x00\x00\x00\x00\x14\xd0\x02\x00\x00\x08\x00\x00\x00\x05\x00\x00\x00White\x00\x00\x00\xff\x00\x00\x00\xff\x00\x00\x00\xff\x00\x00\x00\x0b\x00\x00\x00Light Green\x00\xa0\x00\x00\x00\xff\x00\x00\x00\xa0\x00\x00\x00\x05\x00\x00\x00Green\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00P\x00\x00\x00\x04\x00\x00\x00Cyan\x00\x00\x00\x00\xff\x00\x00\x00\xc8\x00\x00\x00\x04\x00\x00\x00Blued\x00\x00\x00\x8c\x00\x00\x00\xff\x00\x00\x00\x08\x00\x00\x00Lavender\xe6\x00\x00\x00\x82\x00\x00\x00\xff\x00\x00\x00\x07\x00\x00\x00Magenta\x00\xff\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\r\x00\x00\x00Light Magenta\x00\x00\x00\xff\x00\x00\x00\xb4\x00\x00\x00\xd2\x00\x00\x00F\x00\x00\x00\x00\x00\x00\x00\x7f\x00\x00\x00\x00\x00\x00\x00"
FAKE_CONFIG_RESPONSE_LARGE = b"\x03\x00\xf50,\x04\x00\x00d\x00\x00\x00(h(h\x00\x02\x00\xa00\x00\x00\x00\x0e\x00\x00\x00Water Features\x00\x00\x1b\x00\x00\x00\xf4\x01\x00\x00\x03\x00\x00\x00Spa\x00G\x01\x01\x01\x00\x00\x00\x01\xd0\x02\x00\x00\xf5\x01\x00\x00\x07\x00\x00\x00Cleaner\x00\x15\x05\x00\x00\x00\x00\x00\x02\xd0\x02\x00\x00\xf6\x01\x00\x00\x04\x00\x00\x00Jets-\x00\x01\x00\x00\x00\x00\x03\xd0\x02\x00\x00\xf7\x01\x00\x00\r\x00\x00\x00Water Feature\x00\x00\x00S\x00\x02\x00\x00\x00\x00\x04\xd0\x02\x00\x00\xf8\x01\x00\x00\x0b\x00\x00\x00Fiber Optic\x00\x1d\x0b\x04\x00\x00\x00\x00\x05\xd0\x02\x00\x00\xf9\x01\x00\x00\x04\x00\x00\x00Pool<\x02\x00\x01\x00\x00\x00\x06\xd0\x02\x00\x00\xfa\x01\x00\x00\x0b\x00\x00\x00Color Wheel\x00\x16\x0c\x03\x00\x00\x00\n\x07\xd0\x02\x00\x00\xfb\x01\x00\x00\x0b\x00\x00\x00Color Wheel\x00\x16\x0c\x03\x00\x00\x00\n\x08\xd0\x02\x00\x00\xfc\x01\x00\x00\x05\x00\x00\x00Aux 7\x00\x00\x00\x08\x00\x05\x00\x00\x00\x00\t\xd0\x02\x00\x00\xfd\x01\x00\x00\x05\x00\x00\x00Aux 8\x00\x00\x00\t\x00\x05\x00\x00\x00\x00\n\xd0\x02\x00\x00\xfe\x01\x00\x00\t\x00\x00\x00Spa Light\x00\x00\x00I\n\x03\x00\x00\x00\x00\x0b\xd0\x02\x00\x00\xff\x01\x00\x00\x0b\x00\x00\x00Pool Light \x00\\\t\x03\x00\x00\x00\x00\x0c\xd0\x02\x00\x00\x00\x02\x00\x00\x0b\x00\x00\x00Pool Light \x00]\t\x03\x00\x00\x00\x00\r\xd0\x02\x00\x00\x01\x02\x00\x00\x0b\x00\x00\x00Pool Light \x00^\t\x03\x00\x00\x00\x00\x0e\xd0\x02\x00\x00\x02\x02\x00\x00\x0b\x00\x00\x00Pool Light \x00_\t\x03\x00\x00\x00\x00\x0f\xd0\x02\x00\x00\x03\x02\x00\x00\x0b\x00\x00\x00Pool Light \x00`\t\x03\x00\x00\x00\x00\x10\xd0\x02\x00\x00\x04\x02\x00\x00\t\x00\x00\x00Waterfall\x00\x00\x00U\x00\x02\x00\x00\x00\x00\x11\xd0\x02\x00\x00\x05\x02\x00\x00\x05\x00\x00\x00Aux 8\x00\x00\x00\t\x00\x05\x00\x00\x00\x00\x12\xd0\x02\x00\x00\x06\x02\x00\x00\x05\x00\x00\x00Aux 9\x00\x00\x00\n\x00\x05\x00\x00\x00\x00\x13\xd0\x02\x00\x00\x07\x02\x00\x00\x06\x00\x00\x00Aux 10\x00\x00\x0b\x00\x05\x00\x00\x00\x00\x14\xd0\x02\x00\x00\x08\x02\x00\x00\x08\x00\x00\x00Upr Poola\x00\x02\x00\x00\x00\x00\x15\xd0\x02\x00\x00\t\x02\x00\x00\x0b\x00\x00\x00Upr Cleaner\x00b\x00\x00\x00\x00\x00\x00\x16\xd0\x02\x00\x00\n\x02\x00\x00\x0b\x00\x00\x00Upr Wtrfall\x00c\x00\x02\x00\x00\x00\x00\x17\xd0\x02\x00\x00\x0b\x02\x00\x00\x0b\x00\x00\x00U Pool Ligh\x00d\x07\x04\x00\x00\x00\x00\x18\xd0\x02\x00\x00\x0c\x02\x00\x00\x05\x00\x00\x00Aux 5\x00\x00\x00\x06\x00\x05\x00\x00\x00\x00\x19\xd0\x02\x00\x00\x1c\x02\x00\x00\x05\x00\x00\x00Slide\x00\x00\x00E\x00\x02\x00\x00\x00\x00)\xd0\x02\x00\x00\x1d\x02\x00\x00\r\x00\x00\x00Spa Waterfall\x00\x00\x00M\x0e\x02\x00\x00\x00\x00*\xd0\x02\x00\x00\x08\x00\x00\x00\x05\x00\x00\x00White\x00\x00\x00\xff\x00\x00\x00\xff\x00\x00\x00\xff\x00\x00\x00\x0b\x00\x00\x00Light Green\x00\xa0\x00\x00\x00\xff\x00\x00\x00\xa0\x00\x00\x00\x05\x00\x00\x00Green\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00P\x00\x00\x00\x04\x00\x00\x00Cyan\x00\x00\x00\x00\xff\x00\x00\x00\xc8\x00\x00\x00\x04\x00\x00\x00Blued\x00\x00\x00\x8c\x00\x00\x00\xff\x00\x00\x00\x08\x00\x00\x00Lavender\xe6\x00\x00\x00\x82\x00\x00\x00\xff\x00\x00\x00\x07\x00\x00\x00Magenta\x00\xff\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\r\x00\x00\x00Light Magenta\x00\x00\x00\xff\x00\x00\x00\xb4\x00\x00\x00\xd2\x00\x00\x00F\x00\x00\x00\x00\x00\x00\x00\x7f\x00\x00\x00\x00\x00\x00\x00"
FAKE_STATUS_RESPONSE = b"\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x009\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x008\x00\x00\x00\x00\x00\x00\x00V\x00\x00\x00d\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00a\x00\x00\x00\x00\x00\x00\x00a\x00\x00\x009\x00\x00\x00\x03\x00\x00\x00\x12\x00\x00\x00\xf4\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xf5\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xf6\x01\x00\x00\x01\x00\x00\x00\x02\x00\n\x00\xf7\x01\x00\x00\x01\x00\x00\x00\x07\x00\n\x00\xf8\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\xf9\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xfa\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\xfb\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xfc\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xfe\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x05\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x07\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xec\x02\x00\x00\xbd\x02\x00\x00\xf3\xff\xff\xff\x00\x00\x00\x00\x03\x00\x00\x00\x04\x00\x00\x00\x01\x00\x00\x00"
FAKE_PUMP_RESPONSE = b"\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00\x06\x00\x00\x00\xc4\t\x00\x00\x01\x00\x00\x00\t\x00\x00\x00\xf0\n\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00z\r\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x1e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x1e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x1e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x1e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x1e\x00\x00\x00\x00\x00\x00\x00"
FAKE_CHEMISTRY_RESPONSE = b"*\x00\x00\x00\x00\x00\x00\x00\x00\x02\xee\x02\xbc\x00\x00\x00\x05\x00\x00\x00\x02\x00\n\x00\x04\x03\x04\xf3\x02\xe4\x00$\x00F\x14\x008\x81\x00\xa5 <\x01\x00\x00\x00\x00\x00"
FAKE_SCG_RESPONSE = b"\x00\x00\x00\x00\x01\x00\x00\x002\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
FAKE_COLOR_UPDATES = [struct.pack("<5I", 12, x, 15, 0, 0) for x in range(15)]

ASYNC_SL_RESPONSES = {
    CODE.VERSION_QUERY: encodeMessageString(FAKE_GATEWAY_VERSION),
    CODE.CTRLCONFIG_QUERY: FAKE_CONFIG_RESPONSE,
    CODE.POOLSTATUS_QUERY: FAKE_STATUS_RESPONSE,
    CODE.STATUS_CHANGED: FAKE_STATUS_RESPONSE,
    CODE.PUMPSTATUS_QUERY: FAKE_PUMP_RESPONSE,
    CODE.CHEMISTRY_QUERY: FAKE_CHEMISTRY_RESPONSE,
    CODE.CHEMISTRY_CHANGED: FAKE_CHEMISTRY_RESPONSE,
    CODE.SCGCONFIG_QUERY: FAKE_SCG_RESPONSE,
    CODE.COLOR_UPDATE: FAKE_COLOR_UPDATES[7],
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
