from slgateway.decode_response.datautil import *
from slgateway.const import *

def decode_pool_status_response(buff, data):

    #{ name="", value= }
    if('sensors' not in data):
        data['sensors'] = {}
  
    ok, offset = getSome("I", buff, 0)

    freezeMode, offset = getSome("B", buff, offset)

    remotes, offset = getSome("B", buff, offset)

    poolDelay, offset = getSome("B", buff, offset)

    spaDelay, offset = getSome("B", buff, offset)

    cleanerDelay, offset = getSome("B", buff, offset)

    # fast forward 3 bytes. why? because.
    ff1, offset = getSome("B", buff, offset)
    ff2, offset = getSome("B", buff, offset)
    ff3, offset = getSome("B", buff, offset)

    if(data['config']['is_celcius']['value']):
        unittxt = '\xb0C'
    else:
        unittxt = '\xb0F'

    airTemp, offset = getSome("i", buff, offset)
    data['sensors']['air_temperature'] = {
        'name':"Air Temperature",
        'value':airTemp}

    bodiesCount, offset = getSome("I", buff, offset)
    # Should this default to 2?
    bodiesCount = min(bodiesCount, 2)

    if('bodies' not in data):
        data['bodies'] = {} 

    for i in range(bodiesCount):
        bodyType, offset = getSome("I", buff, offset)
        if(bodyType not in range(2)): bodyType = 0

        if(i not in data['bodies']):
            data['bodies'][i] = {}
    
        data['bodies'][i]['body_type'] = {
            'name':"Type of body of water",
            'value':bodyType}

        currentTemp, offset = getSome("i", buff, offset)
        bodyName = "Current {} Temperature".format(mapping.BODY_TYPE[bodyType])
        data['bodies'][i]['current_temperature'] = {
            'name':bodyName,
            'value':currentTemp}

        heatStatus, offset = getSome("i", buff, offset)
        heaterName = "{} Heater".format(mapping.BODY_TYPE[bodyType])
        data['bodies'][i]['heat_status'] = {
            'name':heaterName,
            'value':heatStatus}

        heatSetPoint, offset = getSome("i", buff, offset)
        hspName = "{} Heat Set Point".format(mapping.BODY_TYPE[bodyType])
        data['bodies'][i]['heat_set_point'] = {
            'name':hspName,
            'value':heatSetPoint}

        coolSetPoint, offset = getSome("i", buff, offset)
        cspName = "{} Cool Set Point".format(mapping.BODY_TYPE[bodyType])
        data['bodies'][i]['cool_set_point'] = {
            'name':cspName,
            'value':coolSetPoint}

        heatMode, offset = getSome("i", buff, offset)
        hmName = "{} Heater Mode".format(mapping.BODY_TYPE[bodyType])
        data['bodies'][i]['heat_mode'] = {
            'name':hmName,
            'value':heatMode}
  
    circuitCount, offset = getSome("I", buff, offset)

    if('circuits' not in data):
        data['circuits'] = {}

    for i in range(circuitCount):
        circuitID, offset = getSome("I", buff, offset)

        if(circuitID not in data['circuits']):
            data['circuits'][circuitID] = {}

        if('id' not in data['circuits'][circuitID]):
            data['circuits'][circuitID]['id'] = circuitID

        circuitstate, offset = getSome("I", buff, offset)
        data['circuits'][circuitID]['value'] = circuitstate

        circuitColorSet, offset = getSome("B", buff, offset)
        circuitColorPos, offset = getSome("B", buff, offset)
        circuitColorStagger, offset = getSome("B", buff, offset)
        circuitDelay, offset = getSome("B", buff, offset)

    if('chemistry' not in data):
        data['chemistry'] = {}
    
    pH, offset = getSome("i", buff, offset)
    data['chemistry']['ph'] = {
        'name':"pH",
        'value':(pH / 100)}
  
    orp, offset = getSome("i", buff, offset)
    data['chemistry']['orp'] = {
        'name':"ORP",
        'value':orp}

    saturation, offset = getSome("i", buff, offset)
    data['chemistry']['saturation'] = {
        'name':"Saturation Index",
        'value':(saturation / 100)}

    saltPPM, offset = getSome("i", buff, offset)
    data['chemistry']['salt_ppm'] = {
        'name':"Salt",
        'value':saltPPM}

    pHTank, offset = getSome("i", buff, offset)
    data['chemistry']['ph_tank_level'] = {
        'name':"pH Tank Level",
        'value':pHTank}

    orpTank, offset = getSome("i", buff, offset)
    data['chemistry']['orp_tank_level'] = {
        'name':"ORP Tank Level",
        'value':orpTank}

    alarms, offset = getSome("i", buff, offset)
    data['chemistry']['alarms'] = {
        'name':"Chemistry Alarm",
        'value':alarms}

