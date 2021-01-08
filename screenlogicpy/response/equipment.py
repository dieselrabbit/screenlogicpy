from .utility import getSome, getArray

#pylint: disable=unused-variable
def decode(buff, data):
    if 'equipment' not in data:
        data['equipment'] = {} 
    data['equipment']['controlerType'], offset = getSome("B", buff, 0)
    data['equipment']['hardwareType'], offset = getSome("B", buff, offset)

    skip1, offset = getSome("B", buff, offset)
    skip2, offset = getSome("B", buff, offset)
    data['equipment']['controlerData'], offset = getSome("I", buff, offset)

    data['equipment']['versionDataArray'], offset = getArray(buff, offset)
    data['equipment']['speedDataArray'], offset =  getArray(buff, offset)
    data['equipment']['valveDataArray'], offset =  getArray(buff, offset)
    data['equipment']['remoteDataArray'], offset =  getArray(buff, offset)
    data['equipment']['sensorDataArray'], offset =  getArray(buff, offset)
    data['equipment']['delayDataArray'], offset =  getArray(buff, offset)
    data['equipment']['macrosDataArray'], offset =  getArray(buff, offset)
    data['equipment']['miscDataArray'], offset =  getArray(buff, offset)
    data['equipment']['lightDataArray'], offset =  getArray(buff, offset)
    data['equipment']['flowsDataArray'], offset =  getArray(buff, offset)
    data['equipment']['sgsDataArray'], offset =  getArray(buff, offset)
    data['equipment']['spaFlowsDataArray'], offset =  getArray(buff, offset)