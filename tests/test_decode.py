from screenlogicpy.requests.utility import getSome

#pylint: disable=unused-variable
def decode(buff):
    size, offset = getSome("I", buff, 0) #0
    unknown1, offset = getSome("B", buff, offset) #4
    pH, offset = getSome(">H", buff, offset) #5
    pH /= 100
    orp, offset = getSome(">H", buff, offset) #7
    pHSetpoint, offset = getSome(">H", buff, offset) #9
    pHSetpoint /= 100
    orpSetpoint, offset = getSome(">H", buff, offset) #11

    skipped = []
    for i in range(12):
     skip, offset = getSome("B", buff, offset) #13-23
     skipped.append(skip)

    pHSupplyLevel, offset = getSome("B", buff, offset) #25
    pHSupplyLevel -= 1
    orpSupplyLevel, offset = getSome("B", buff, offset) #26
    orpSupplyLevel -= 1

    saturation, offset = getSome("B", buff, offset) #27
    saturation -= 256
    saturation /= 100
    cal, offset = getSome(">H", buff, offset) #28
    cya, offset = getSome(">H", buff, offset) #30
    alk, offset = getSome(">H", buff, offset) #32
    salt, offset = getSome("H", buff, offset) #34
    saltppm = salt*50
    temp, offset = getSome("B", buff, offset) #36

    skip, offset = getSome("H", buff, offset) #37

    corosivness, offset = getSome("B", buff, offset) #39
    last, offset = getSome("B", buff, offset) #40
    last2, offset = getSome("B", buff, offset) #41
    print('stop')



def getArray(buff, offset):
    itemCount, offset = getSome("I", buff, offset)
    items = [0 for x in range(itemCount)]
    for i in range(itemCount):
        items[i] , offset = getSome("B", buff, offset)
    offsetPad = 0
    if itemCount % 4 != 0:
        offsetPad = (4 - itemCount % 4) % 4
        offset += offsetPad
    return items, offset

def toINT(buff):
    offset = 0
    for i in range(len(buff)):
        byte, offset = getSome("B", buff, offset)
        print(offset, byte)

def decodePump(buff):
    pump = {}
    pump['pumpType'], offset = getSome("I", buff, 0)
    pump['state'], offset = getSome("I", buff, offset)
    pump['currentWatts'], offset = getSome("I", buff, offset)
    pump['currentRPM'], offset = getSome("I", buff, offset)
    unknown1, offset = getSome("I", buff, offset)
    pump['currentGPM'], offset = getSome("I", buff, offset)
    unknown2, offset = getSome("I", buff, offset)

    pump['presets'] = {}
    for i in range(8):
        pump['presets'][i] = {}
        pump['presets'][i]['cid'], offset = getSome("I", buff, offset)
        pump['presets'][i]['setPoint'], offset = getSome("I", buff, offset)
        pump['presets'][i]['isRPM'], offset = getSome("I", buff, offset)

    print(pump)
