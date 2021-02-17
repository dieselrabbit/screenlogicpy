import struct
from ..const import code
from .utility import sendRecieveMessage, getSome

def request_chemistry(gateway_socket, data):
    response = sendRecieveMessage(gateway_socket, code.CHEMISTRY_QUERY, struct.pack("<I", 0))
    decode_chemistry(response, data)

#pylint: disable=unused-variable
def decode_chemistry(buff, data):

    if 'chemistry' not in data:
        data['chemistry'] = {}

    chemistry = data['chemistry']

    unittxt = '\xb0F'
    if(data["config"]['is_celcius']['value']):
        unittxt = '\xb0C'

    size, offset = getSome("I", buff, 0) #0

    if 'unknown' not in chemistry:
        chemistry['unknown'] = {}

    unknown = chemistry['unknown']

    unknown1, offset = getSome("B", buff, offset) #4
    unknown['unknown1'] = unknown1

    pH, offset = getSome(">H", buff, offset) #5
    chemistry['ph'] = {
        'name':"pH",
        'value':(pH / 100),
        'unit':'pH'}

    orp, offset = getSome(">H", buff, offset) #7
    chemistry['orp'] = {
        'name':"ORP",
        'value':orp,
        'unit':'mV'}

    pHSetpoint, offset = getSome(">H", buff, offset) #9
    chemistry['ph_setpoint'] = {
        'name':"pH",
        'value':(pHSetpoint / 100),
        'unit':'pH'}

    orpSetpoint, offset = getSome(">H", buff, offset) #11
    chemistry['orp_setpoint'] = {
        'name':"ORP",
        'value':orpSetpoint,
        'unit':'mV'}

    
    # fast forward 12 bytes
    unknown['skipped'] = []
    #for i in range(12):
    #    skip, offset = getSome("B", buff, offset) #13-23
    #    unknown['skipped'].append(skip)
    skip1, offset = getSome(">I", buff, offset)
    unknown['skipped'].append(skip1)
    skip2, offset = getSome(">I", buff, offset)
    unknown['skipped'].append(skip2)
    skip3, offset = getSome(">H", buff, offset)
    unknown['skipped'].append(skip3)
    skip4, offset = getSome(">H", buff, offset)
    unknown['skipped'].append(skip4)
    

    pHSupplyLevel, offset = getSome("B", buff, offset) #25
    chemistry['ph_supply_level'] = {
        'name':"pH Supply Level",
        'value':pHSupplyLevel}

    orpSupplyLevel, offset = getSome("B", buff, offset) #26
    chemistry['orp_supply_level'] = {
        'name':"ORP Supply Level",
        'value':orpSupplyLevel}

    saturation, offset = getSome("B", buff, offset) #27
    saturation -= 256
    chemistry['saturation'] = {
        'name':"Saturation Index",
        'value':(saturation / 100),
        'unit':'lsi'}

    cal, offset = getSome(">H", buff, offset) #28
    chemistry['calcium_harness'] = {
        'name':"Calcium Hardness",
        'value': cal,
        'unit': "ppm"}

    cya, offset = getSome(">H", buff, offset) #30
    chemistry['cya'] = {
        'name':"Cyanuric Acid",
        'value': cya,
        'unit': "ppm"}

    alk, offset = getSome(">H", buff, offset) #32
    chemistry['total_alkalinity'] = {
        'name':"Total Alkalinity",
        'value': alk,
        'unit': "ppm"}

    saltPPM, offset = getSome("H", buff, offset) #34
    chemistry['salt_ppm'] = {
        'name':"Salt",
        'value':(saltPPM * 50),
        'unit':'ppm'}

    waterTemp, offset = getSome("B", buff, offset) #36
    chemistry['water_temperature'] = {
        'name':"Water Temperature",
        'value':waterTemp,
        'unit':unittxt,
        'hass_device_class': 'temperature'}

    unknown2, offset = getSome("H", buff, offset) #37
    unknown['unknown2'] = unknown2


    corosivness, offset = getSome("B", buff, offset) #39
    chemistry['corosivness'] = {
        'name':"Corosiveness",
        'value': corosivness}

    last1, offset = getSome("B", buff, offset) #40
    unknown['last1'] = last1
    last2, offset = getSome("B", buff, offset) #41
    unknown['last2'] = last2
