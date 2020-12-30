from .utility import getSome

#pylint: disable=unused-variable
def decode(buff, data, pumpID):
    pump = data['pumps'][pumpID]
    pump['name'] = ''
    pump['pumpType'], offset = getSome("I", buff, 0)
    pump['state'], offset = getSome("I", buff, offset)

    curW, offset = getSome("I", buff, offset)
    pump['currentWatts'] = {
        'name': 'Pump ' + str(pumpID+1) + " Watts",
        'value': curW,
        'unit': 'W',
        'hass_device_class': 'power'
    }

    curR, offset = getSome("I", buff, offset)
    pump['currentRPM'] = {
        'name': 'Pump ' + str(pumpID+1) + " RPM",
        'value': curR,
        'unit': 'RPM'
    }

    unknown1, offset = getSome("I", buff, offset)

    curG, offset = getSome("I", buff, offset)
    pump['currentGPM'] = {
        'name': 'Pump ' + str(pumpID+1) + " GPM",
        'value': curG,
        'unit': 'GPM'
    }

    unknown2, offset = getSome("I", buff, offset)

    pump['presets'] = {}
    name = ''
    for i in range(8):
        pump['presets'][i] = {}
        pump['presets'][i]['cid'], offset = getSome("I", buff, offset)
        for num, circuit in data['circuits'].items():
            if pump['presets'][i]['cid'] == circuit['device_id']:
                name += circuit['name'] + ', '
        pump['presets'][i]['setPoint'], offset = getSome("I", buff, offset)
        pump['presets'][i]['isRPM'], offset = getSome("I", buff, offset)

    name = name.strip().strip(',') + ' Pump'
    pump['name'] = name