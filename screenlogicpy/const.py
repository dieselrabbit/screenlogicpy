import sys
import os
import struct


def me():
    return os.path.basename(sys.argv[0])


class ScreenLogicError(Exception):
    pass


class ScreenLogicWarning(Exception):
    pass


class header:
    fmt = "<HHI"
    length = struct.calcsize(fmt)


# Some of the message codes
class code:
    MSG_CODE_1 = 0
    UNKNOWN_ANSWER = 13
    CHALLENGE_QUERY = 14
    CHALLENGE_ANSWER = CHALLENGE_QUERY + 1
    LOCALLOGIN_QUERY = 27
    LOCALLOGIN_ANSWER = LOCALLOGIN_QUERY + 1
    VERSION_QUERY = 8120
    VERSION_ANSWER = VERSION_QUERY + 1
    POOLSTATUS_QUERY = 12526
    POOLSTATUS_ANSWER = POOLSTATUS_QUERY + 1
    SETHEATTEMP_QUERY = 12528
    SETHEATTEMP_ANSWER = SETHEATTEMP_QUERY + 1
    BUTTONPRESS_QUERY = 12530
    BUTTONPRESS_ANSWER = BUTTONPRESS_QUERY + 1
    CTRLCONFIG_QUERY = 12532
    CTRLCONFIG_ANSWER = CTRLCONFIG_QUERY + 1
    SETHEATMODE_QUERY = 12538
    SETHEATMODE_ANSWER = SETHEATMODE_QUERY + 1
    SETCOOLTEMP_QUERY = 12590
    SETCOOLTEMP_ANSWER = SETCOOLTEMP_QUERY + 1
    GATEWAYDATA_QUERY = 18003
    GATEWAYDATA_ANSWER = GATEWAYDATA_QUERY + 1
    CONTROLLER_QUERRY = 12532
    CONTROLLER_ANSWER = CONTROLLER_QUERRY + 1
    EQUIPMENT_QUERY = 12566
    EQUIPMENT_ANSWER = EQUIPMENT_QUERY + 1
    PUMPSTATUS_QUERY = 12584
    PUMPSTATUS_ANSWER = PUMPSTATUS_QUERY + 1
    LIGHTCOMMAND_QUERY = 12556
    LIGHTCOMMAND_ANSWER = LIGHTCOMMAND_QUERY + 1
    CHEMISTRY_QUERY = 12592
    CHEMISTRY_ANSWER = CHEMISTRY_QUERY + 1


# class mapping:
#    BODY_TYPE  = ['Pool', 'Spa']

#    HEAT_MODE  = ['Off', 'Solar',
#                  "Solar Prefered",
#                  'Heat', "Don't Change"]

#    ON_OFF     = ['Off', 'On']

#    COLOR_MODE = ['Off', 'On',
#                  'Set', 'Sync',
#                  'Swim', 'Party',
#                  'Romantic', 'Caribbean',
#                  'American', 'Sunset',
#                  'Royal', 'Save',
#                  'Recall', 'Blue',
#                  'Green', 'Red',
#                  'White', 'Magenta',
#                  'Thumper', 'Next',
#                  'Reset', 'Hold']


class BODY_TYPE:
    POOL = 0
    SPA = 1
    Names = ["Pool", "Spa"]

    @classmethod
    def GetFriendlyName(cls, index):
        return cls.Names[index]


class ON_OFF:
    OFF = 0
    ON = 1
    Names = ["Off", "On"]

    @classmethod
    def GetFriendlyName(cls, index):
        return cls.Names[index]


class HEAT_MODE:
    OFF = 0
    SOLAR = 1
    SOLAR_PREFERED = 2
    HEATER = 3
    DONT_CHANGE = 4
    Names = ["Off", "Solar", "Solar Prefered", "Heater", "Don't Change"]

    @classmethod
    def GetFriendlyName(cls, index):
        return cls.Names[index]


class COLOR_MODE:
    OFF = 0
    ON = 1
    SET = 2
    SYNC = 3
    SWIM = 4
    PARTY = 5
    ROMANTIC = 6
    CARIBBEAN = 7
    AMERICAN = 8
    SUNSET = 9
    ROYAL = 10
    SAVE = 11
    RECALL = 12
    BLUE = 13
    GREEN = 14
    RED = 15
    WHITE = 16
    MAGENTA = 17
    THUMPER = 18
    NEXT = 19
    RESET = 20
    HOLD = 21

    Names = [
        "Off",
        "On",
        "Set",
        "Sync",
        "Swim",
        "Party",
        "Romantic",
        "Caribbean",
        "American",
        "Sunset",
        "Royal",
        "Save",
        "Recall",
        "Blue",
        "Green",
        "Red",
        "White",
        "Magenta",
        "Thumper",
        "Next",
        "Reset",
        "Hold",
    ]

    @classmethod
    def GetFriendlyName(cls, index):
        return cls.Names[index]


CONTROLLER_HARDWARE = {
    0: {0: "IntelliTouch i5+3S"},
    1: {0: "IntelliTouch i7+3"},
    2: {0: "IntelliTouch i9+3"},
    3: {0: "IntelliTouch i5+3S"},
    4: {0: "IntelliTouch i9+3S"},
    5: {0: "IntelliTouch i10+3D"},
    11: {0: "Suntouch/Intellicom"},
    13: {
        0: "EasyTouch2 8",
        1: "EasyTouch2 8P",
        2: "EasyTouch2 4",
        3: "EasyTouch2 4P",
        5: "EasyTouch2 PL4",
        6: "EasyTouch2 PSL4",
    },
    14: {0: "EasyTouch1 8", 1: "EasyTouch1 8P", 2: "EasyTouch1 4", 3: "EasyTouch1 4P"},
}

PUMP_TYPE = {0: "None", 1: "Intelliflow VF", 2: "Intelliflow VS", 3: "Intelliflow VSF"}

SL_GATEWAY_IP = "ip"
SL_GATEWAY_PORT = "port"
SL_GATEWAY_TYPE = "gtype"
SL_GATEWAY_SUBTYPE = "gsubtype"
SL_GATEWAY_NAME = "name"
