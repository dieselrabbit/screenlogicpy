from screenlogicpy.response.utility import getSome

#pylint: disable=unused-variable
def decode(buff):
    controlerType, offset = getSome("B", buff, 0)
    hardwareType, offset = getSome("B", buff, offset)

    skip1, offset = getSome("B", buff, offset)
    skip2, offset = getSome("B", buff, offset)
    controlerData, offset = getSome("I", buff, offset)

    versions, offset = getArray(buff, offset)
    speeds, offset =  getArray(buff, offset)
    valves, offset =  getArray(buff, offset)
    remotes, offset =  getArray(buff, offset)
    sensors, offset =  getArray(buff, offset)
    delays, offset =  getArray(buff, offset)
    macros, offset =  getArray(buff, offset)
    misc, offset =  getArray(buff, offset)
    lights, offset =  getArray(buff, offset)
    flows, offset =  getArray(buff, offset)
    sgs, offset =  getArray(buff, offset)
    spaFlows, offset =  getArray(buff, offset)

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
