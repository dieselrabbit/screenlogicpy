from .utility import getSome
from ..const import BODY_TYPE

#pylint: disable=unused-variable
def decode(buff, data):

    #data[""][""] = { 
    #    'name':'', 
    #    'value': }
  
    ok, offset = getSome("I", buff, 0)
    data["config"]["ok"] = {
        'name': 'OK Check',
        'value': ok }

    freezeMode, offset = getSome("B", buff, offset)
    data["config"]["freeze_mode"] = { 
        'name':'Freeze Mode', 
        'value':freezeMode }

    remotes, offset = getSome("B", buff, offset)
    data["config"]["remotes"] = { 
        'name':'Remotes', 
        'value':remotes }

    poolDelay, offset = getSome("B", buff, offset)
    data["config"]["pool_delay"] = { 
        'name':'Pool Delay', 
        'value':poolDelay }

    spaDelay, offset = getSome("B", buff, offset)
    data["config"]["spa_delay"] = { 
        'name':'Spa Delay', 
        'value':spaDelay }

    cleanerDelay, offset = getSome("B", buff, offset)
    data["config"]["cleaner_delay"] = { 
        'name':'Cleaner Delay', 
        'value':cleanerDelay }

    # fast forward 3 bytes. Unknown data.
    ff1, offset = getSome("B", buff, offset)
    ff2, offset = getSome("B", buff, offset)
    ff3, offset = getSome("B", buff, offset)

    unittxt = '\xb0F'
    if(data['config']['is_celcius']['value']):
        unittxt = '\xb0C'

    if('sensors' not in data):
        data['sensors'] = {}

    airTemp, offset = getSome("i", buff, offset)
    data['sensors']['air_temperature'] = {
        'name':"Air Temperature",
        'value':airTemp,
        'unit':unittxt}

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

        data['bodies'][i]['min_set_point']['unit'] = unittxt
        data['bodies'][i]['max_set_point']['unit'] = unittxt

        data['bodies'][i]['body_type'] = {
            'name':"Type of body of water",
            'value':bodyType}

        currentTemp, offset = getSome("i", buff, offset)
        bodyName = "Current {} Temperature".format(BODY_TYPE.GetFriendlyName(bodyType))
        data['bodies'][i]['current_temperature'] = {
            'name':bodyName,
            'value':currentTemp,
            'unit':unittxt}

        heatStatus, offset = getSome("i", buff, offset)
        heaterName = "{} Heat".format(BODY_TYPE.GetFriendlyName(bodyType))
        data['bodies'][i]['heat_status'] = {
            'name':heaterName,
            'value':heatStatus}

        heatSetPoint, offset = getSome("i", buff, offset)
        hspName = "{} Heat Set Point".format(BODY_TYPE.GetFriendlyName(bodyType))
        data['bodies'][i]['heat_set_point'] = {
            'name':hspName,
            'value':heatSetPoint,
            'unit':unittxt}

        coolSetPoint, offset = getSome("i", buff, offset)
        cspName = "{} Cool Set Point".format(BODY_TYPE.GetFriendlyName(bodyType))
        data['bodies'][i]['cool_set_point'] = {
            'name':cspName,
            'value':coolSetPoint,
            'unit':unittxt}

        heatMode, offset = getSome("i", buff, offset)
        hmName = "{} Heat Mode".format(BODY_TYPE.GetFriendlyName(bodyType))
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

    #if('chemistry' not in data):
    #    data['chemistry'] = {}
    
    pH, offset = getSome("i", buff, offset)
    data['sensors']['ph'] = {
        'name':"pH",
        'value':(pH / 100),
        'unit':'pH'}
  
    orp, offset = getSome("i", buff, offset)
    data['sensors']['orp'] = {
        'name':"ORP",
        'value':orp,
        'unit':'mV'}

    saturation, offset = getSome("i", buff, offset)
    data['sensors']['saturation'] = {
        'name':"Saturation Index",
        'value':(saturation / 100),
        'unit':'lsi'}

    saltPPM, offset = getSome("i", buff, offset)
    data['sensors']['salt_ppm'] = {
        'name':"Salt",
        'value':(saltPPM * 50),
        'unit':'ppm'}

    pHTank, offset = getSome("i", buff, offset)
    data['sensors']['ph_tank_level'] = {
        'name':"pH Tank Level",
        'value':pHTank}

    orpTank, offset = getSome("i", buff, offset)
    data['sensors']['orp_tank_level'] = {
        'name':"ORP Tank Level",
        'value':orpTank}

    alarm, offset = getSome("i", buff, offset)
    data['sensors']['chem_alarm'] = {
        'name':"Chemistry Alarm",
        'value':alarm}

