from .utility import getSome

#pylint: disable=unused-variable
def decode(buff, data, pumpID):
    pump = data['config']['pumps'][pumpID]
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
