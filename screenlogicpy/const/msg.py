import struct

COM_MAX_RETRIES = 1
COM_RETRY_WAIT = 1
COM_TIMEOUT = 2
HEADER_FORMAT = "<HHI"
HEADER_LENGTH = struct.calcsize(HEADER_FORMAT)


# Some of the message codes
# ANSWERS are QUERY + 1
class CODE:
    MSG_CODE_1 = 0
    ERROR_LOGIN_REJECTED = 13
    CHALLENGE_QUERY = 14
    PING_QUERY = 16
    LOCALLOGIN_QUERY = 27
    ERROR_INVALID_REQUEST = 30
    ERROR_BAD_PARAMETER = 31  # Actually bad parameter?
    VERSION_QUERY = 8120
    WEATHER_FORECAST_CHANGED = 9806
    WEATHER_FORECAST_QUERY = 9807
    STATUS_CHANGED = 12500
    COLOR_UPDATE = 12504
    CHEMISTRY_CHANGED = 12505
    ADD_CLIENT_QUERY = 12522
    REMOVE_CLIENT_QUERY = 12524
    POOLSTATUS_QUERY = 12526
    SETHEATTEMP_QUERY = 12528
    BUTTONPRESS_QUERY = 12530
    CTRLCONFIG_QUERY = 12532
    SETHEATMODE_QUERY = 12538
    LIGHTCOMMAND_QUERY = 12556
    SETCHEMDATA_QUERY = 12594
    EQUIPMENT_QUERY = 12566
    SCGCONFIG_QUERY = 12572
    SETSCG_QUERY = 12576
    PUMPSTATUS_QUERY = 12584
    SETCOOLTEMP_QUERY = 12590
    CHEMISTRY_QUERY = 12592
    GATEWAYDATA_QUERY = 18003
