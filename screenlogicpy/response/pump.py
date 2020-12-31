from .utility import getSome

#pylint: disable=unused-variable
def decode(buff, data, pumpID):
    pump = data['pumps'][pumpID]
    pump['name'] = ''
    pump['pumpType'], offset = getSome("I", buff, 0)
    pump['state'], offset = getSome("I", buff, offset)

    curW, offset = getSome("I", buff, offset)
    pump['currentWatts'] = {}
    curR, offset = getSome("I", buff, offset)
    pump['currentRPM'] = {}
    
    unknown1, offset = getSome("I", buff, offset)

    curG, offset = getSome("I", buff, offset)
    pump['currentGPM'] = {}

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

    pump['currentWatts'] = {
        'name': pump['name'] + " Current Watts",
        'value': curW,
        'unit': 'W',
        'hass_device_class': 'power'
    }

    pump['currentRPM'] = {
        'name': pump['name'] + " Current RPM",
        'value': curR,
        'unit': 'rpm'
    }

    pump['currentGPM'] = {
        'name': pump['name'] + " Current GPM",
        'value': curG,
        'unit': 'gpm'
    }
