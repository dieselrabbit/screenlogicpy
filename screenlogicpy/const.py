import sys
import os
import struct

def me(): return(os.path.basename(sys.argv[0]))

class ScreenLogicError(Exception):
    pass

class ScreenLogicWarning(Exception):
    pass

class header:
    fmt    = "<HHI"
    length = struct.calcsize(fmt)

# Some of the message codes
class code:
    MSG_CODE_1            = 0
    UNKNOWN_ANSWER        = 13
    CHALLENGE_QUERY       = 14
    CHALLENGE_ANSWER      = CHALLENGE_QUERY  + 1
    LOCALLOGIN_QUERY      = 27
    LOCALLOGIN_ANSWER     = LOCALLOGIN_QUERY + 1
    VERSION_QUERY         = 8120
    VERSION_ANSWER        = VERSION_QUERY    + 1
    POOLSTATUS_QUERY      = 12526
    POOLSTATUS_ANSWER     = POOLSTATUS_QUERY + 1
    SETHEATTEMP_QUERY     = 12528
    SETHEATTEMP_ANSWER    = SETHEATTEMP_QUERY + 1
    BUTTONPRESS_QUERY     = 12530
    BUTTONPRESS_ANSWER    = BUTTONPRESS_QUERY + 1
    CTRLCONFIG_QUERY      = 12532
    CTRLCONFIG_ANSWER     = CTRLCONFIG_QUERY + 1
    SETHEATMODE_QUERY     = 12538
    SETHEATMODE_ANSWER    = SETHEATMODE_QUERY + 1
    SETCOOLTEMP_QUERY     = 12590
    SETCOOLTEMP_ANSWER    = SETCOOLTEMP_QUERY + 1
#    GATEWAYDATA_QUERY     = 18003
#    GATEWAYDATA_ANSWER    = GATEWAYDATA_QUERY + 1
    EQUIPMENT_QUERY       = 12566
    EQUIPMENT_ANSWER      = EQUIPMENT_QUERY + 1

#class mapping:
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
    _names  = ['Pool', 'Spa']

    @classmethod
    def GetFriendlyName(cls, index):
        return cls._names[index]


class ON_OFF:
    OFF = 0
    ON = 1
    _names     = ['Off', 'On']

    @classmethod
    def GetFriendlyName(cls, index):
        return cls._names[index]


class HEAT_MODE:
    OFF = 0
    SOLAR = 1
    SOLAR_PREFERED = 2
    HEAT = 3
    DONT_CHANGE = 4
    _names  = ['Off', 'Solar', "Solar Prefered", 'Heat', "Don't Change"]

    @classmethod
    def GetFriendlyName(cls, index):
        return cls._names[index]


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

    _names = ['Off', 'On',
              'Set', 'Sync',
              'Swim', 'Party',
              'Romantic', 'Caribbean',
              'American', 'Sunset',
              'Royal', 'Save',
              'Recall', 'Blue',
              'Green', 'Red',
              'White', 'Magenta',
              'Thumper', 'Next',
              'Reset', 'Hold']

    def GetFriendlyName(self, index):
        return self._names[index]
